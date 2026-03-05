"""
Views da API de sincronização.
Estes endpoints são usados pelo motor de sincronização (sync_data command) para:
  - Push: receber dados de instâncias locais
  - Pull: enviar dados para instâncias locais
  - Status: verificar estado de conexão
"""
import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.core.serializers import serialize, deserialize
from django.apps import apps
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from functools import wraps
import requests
import base64
import os
from django.core.files.base import ContentFile
from django.db.models import FileField, ImageField

logger = logging.getLogger('sync')


def sync_auth_required(view_func):
    """Decorador que valida o token de autenticação para a API de sync."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        expected_token = settings.SYNC_AUTH_TOKEN

        if not expected_token:
            return JsonResponse(
                {'error': 'SYNC_AUTH_TOKEN não configurado no servidor'},
                status=503
            )

        if auth_header != f'Token {expected_token}':
            return JsonResponse({'error': 'Token de autenticação inválido'}, status=401)

        return view_func(request, *args, **kwargs)
    return wrapper


@csrf_exempt
@require_POST
@sync_auth_required
def sync_push(request):
    """
    Recebe dados de uma instância local.
    Espera JSON com:
      - instance_id: identificador da instância
      - model: caminho do modelo (ex: 'ARQUIVOS.Documento')
      - data: dados serializados em JSON (Django serializer format)
    """
    try:
        body = json.loads(request.body)
        instance_id = body.get('instance_id', '')
        model_path = body.get('model', '')
        data = body.get('data', '[]')

        if not model_path or not data:
            return JsonResponse({'error': 'Campos model e data são obrigatórios'}, status=400)

        # Validar modelo
        if model_path not in settings.SYNC_MODELS:
            return JsonResponse({'error': f'Modelo {model_path} não permitido para sync'}, status=403)

        model = apps.get_model(model_path)
        synced_uuids = []
        
        # Obter campos de arquivo para este modelo
        file_fields = [f.name for f in model._meta.get_fields() if isinstance(f, (FileField, ImageField))]

        with transaction.atomic():
            for obj in deserialize('json', data):
                instance = obj.object
                uuid_sinc = instance.uuid_sinc

                # Extrair arquivos do JSON estendido
                files_data = body.get('files', {}).get(str(uuid_sinc), {})

                # Verificar se já existe
                existing = model.objects.filter(uuid_sinc=uuid_sinc).first()
                
                # Fallback para CustomUser por username (evita erros unique se UUIDs divergirem)
                if not existing and model_path == 'ARQUIVOS.CustomUser':
                    existing = model.objects.filter(username=instance.username).first()
                    if existing:
                        # Se encontramos pelo username, atualizamos o UUID local para bater com o global/central
                        model.objects.filter(pk=existing.pk).update(uuid_sinc=uuid_sinc)
                        logger.info(f'Vinculado usuário {instance.username} por username e atualizado UUID.')
                    # Estratégia: quem tem a data_modificacao mais recente vence
                    # No Django, auto_now preenche ao salvar, mas vamos comparar os valores vindos do JSON
                    remote_mod = getattr(instance, 'data_modificacao', None)
                    local_mod = getattr(existing, 'data_modificacao', None)

                    # Se o remoto for mais recente, atualizamos o local
                    if not local_mod or (remote_mod and (not local_mod or remote_mod > local_mod)):
                        # Garantir que usamos o ID local para não criar duplicado por PK
                        instance.id = existing.id
                        instance.pk = existing.pk
                        
                        # Primeiro, processar arquivos se houver
                        for field_name in file_fields:
                            field_data = files_data.get(field_name)
                            if field_data:
                                content = base64.b64decode(field_data['content'])
                                getattr(instance, field_name).save(field_data['name'], ContentFile(content), save=False)
                        
                        # Guardar forçando o update se o ID já existe
                        instance.save(force_update=True)
                    # Se local é mais recente ou igual, ignoramos o push para manter a versão mais nova
                else:
                    # Novo registo, guardar
                    for field_name in file_fields:
                        field_data = files_data.get(field_name)
                        if field_data:
                            content = base64.b64decode(field_data['content'])
                            getattr(instance, field_name).save(field_data['name'], ContentFile(content), save=False)
                    instance.save()

                # Marcar como sincronizado e definir origem
                model.objects.filter(uuid_sinc=uuid_sinc).update(
                    pendente_sinc=False,
                    ultima_sincronizacao=timezone.now(),
                    origem_instancia=instance_id,
                )
                synced_uuids.append(str(uuid_sinc))

        logger.info(f'Sync push de {instance_id}: {len(synced_uuids)} registos de {model_path}')

        return JsonResponse({
            'status': 'ok',
            'synced_uuids': synced_uuids,
            'count': len(synced_uuids),
        })

    except Exception as e:
        logger.error(f'Erro no sync push: {e}')
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_GET
@sync_auth_required
def sync_pull(request):
    """
    Envia dados para uma instância local.
    Parâmetros GET:
      - instance_id: identificador da instância
      - model: caminho do modelo
      - since: ISO timestamp (apenas registos alterados depois desta data)
    """
    try:
        instance_id = request.GET.get('instance_id', '')
        model_path = request.GET.get('model', '')
        since = request.GET.get('since', '')

        if not model_path:
            return JsonResponse({'error': 'Campo model é obrigatório'}, status=400)

        if model_path not in settings.SYNC_MODELS:
            return JsonResponse({'error': f'Modelo {model_path} não permitido para sync'}, status=403)

        model = apps.get_model(model_path)
        batch_size = settings.SYNC_BATCH_SIZE

        # Obter todos os registos relevantes (incluindo os que este cliente criou mas que podem ter sido editados na nuvem)
        queryset = model.objects.all()

        if since:
            from django.utils.dateparse import parse_datetime
            since_dt = parse_datetime(since)
            if since_dt:
                queryset = queryset.filter(ultima_sincronizacao__gt=since_dt)

        queryset = queryset[:batch_size]
        count = queryset.count()

        # Serialização normal dos dados
        data = serialize('json', queryset, use_natural_primary_keys=False)
        
        # Serialização adiciocal de arquivos em Base64
        files_dict = {}
        file_fields = [f.name for f in model._meta.get_fields() if isinstance(f, (FileField, ImageField))]
        
        if file_fields:
            for item in queryset:
                item_files = {}
                for field_name in file_fields:
                    field = getattr(item, field_name)
                    if field and hasattr(field, 'path') and os.path.exists(field.path):
                        try:
                            with open(field.path, "rb") as f:
                                encoded = base64.b64encode(f.read()).decode('utf-8')
                                item_files[field_name] = {
                                    'name': os.path.basename(field.name),
                                    'content': encoded
                                }
                        except Exception as e:
                            logger.error(f"Erro ao ler arquivo {field.name}: {e}")
                
                if item_files:
                    files_dict[str(item.uuid_sinc)] = item_files

        return JsonResponse({
            'status': 'ok',
            'model': model_path,
            'count': count,
            'data': data,
            'files': files_dict,
        })

    except Exception as e:
        logger.error(f'Erro no sync pull: {e}')
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def sync_status(request):
    """
    Endpoint público para verificar se o servidor está online.
    Tenta pingar o servidor central para confirmar conectividade real.
    """
    central_url = getattr(settings, 'SYNC_CENTRAL_URL', '')
    is_central_reachable = False
    
    if central_url:
        try:
            # Tenta um HEAD request rápido para não sobrecarregar
            response = requests.head(central_url, timeout=3)
            is_central_reachable = response.status_code < 400
        except Exception:
            is_central_reachable = False
    
    return JsonResponse({
        'status': 'online' if (not central_url or is_central_reachable) else 'offline',
        'central_reachable': is_central_reachable,
        'instance_id': getattr(settings, 'SYNC_INSTANCE_ID', 'offline'),
        'timestamp': timezone.now().isoformat(),
    })


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.core.management import call_command
from ARQUIVOS.models import Administracao, Documento

@login_required
def painel_sincronizacao(request):
    """View para o painel de sincronização manual offline."""
    if request.method == 'POST':
        acao = request.POST.get('acao')
        if acao == 'exportar':
            destino_id = request.POST.get('destino_id')
            origem = request.user.administracao
            destino = Administracao.objects.filter(id=destino_id).first() if destino_id else None
            
            try:
                pacote = exportar_pacote(origem, destino)
                # Marcar imediatamente após exportar pacote offline
                marcar_como_sincronizado(origem, destino)
                
                response = HttpResponse(
                    json.dumps(pacote, ensure_ascii=False, indent=2),
                    content_type='application/json'
                )
                filename = f"sync_{origem.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}.json"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
            except Exception as e:
                messages.error(request, f"Erro ao exportar pacote: {e}")
                
        elif acao == 'importar':
            arquivo = request.FILES.get('arquivo_sync')
            if arquivo:
                try:
                    pacote = json.load(arquivo)
                    resultados = importar_pacote(pacote, request.user.administracao)
                    messages.success(request, f"Importação concluída: {resultados['importados']} novos, {resultados['duplicados']} ignorados.")
                    if resultados.get('erros'):
                        for erro in resultados['erros']:
                            messages.warning(request, erro)
                except Exception as e:
                    logger.error(f'Erro na importação manual: {e}')
                    messages.error(request, f"Erro ao importar ficheiro. Verifique se o JSON é válido.")
            else:
                messages.error(request, "Nenhum ficheiro fornecido para importação.")
                
        return redirect('painel_sincronizacao')
        
    administracoes = Administracao.objects.exclude(id=request.user.administracao.id)
    documentos_pendentes = Documento.objects.filter(pendente_sinc=True).order_by('-data_criacao')
    
    context = {
        'administracoes': administracoes,
        'documentos_pendentes': documentos_pendentes
    }
    return render(request, 'Paginas/sincronizacao.html', context)

@login_required
@require_POST
def sincronizar_agora(request):
    """View para acionar a sincronização com a nuvem instantaneamente."""
    try:
        # Executa o comando de sincronização
        call_command('sync_data')
        return JsonResponse({'status': 'sucesso', 'mensagem': 'Sincronização concluída com sucesso!'})
    except Exception as e:
        logger.error(f'Erro na sincronização manual: {e}')
        return JsonResponse({'status': 'erro', 'mensagem': str(e)}, status=500)
