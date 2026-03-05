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

        with transaction.atomic():
            for obj in deserialize('json', data):
                uuid_sinc = obj.object.uuid_sinc

                # Verificar se já existe
                existing = model.objects.filter(uuid_sinc=uuid_sinc).first()

                if existing:
                    # Estratégia: última escrita vence (baseado em updated_at se disponível)
                    remote_updated = getattr(obj.object, 'updated_at', None)
                    local_updated = getattr(existing, 'updated_at', None)

                    if remote_updated and local_updated and remote_updated > local_updated:
                        # O registo remoto é mais recente, actualizar
                        obj.save()
                    elif not local_updated:
                        obj.save()
                    # Se local é mais recente, manter local
                else:
                    # Novo registo, guardar
                    obj.save()

                # Marcar como sincronizado
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

        # Filtrar registos: não enviar de volta os que vieram desta instância
        queryset = model.objects.exclude(origem_instancia=instance_id)

        if since:
            from django.utils.dateparse import parse_datetime
            since_dt = parse_datetime(since)
            if since_dt:
                queryset = queryset.filter(ultima_sincronizacao__gt=since_dt)

        queryset = queryset[:batch_size]
        count = queryset.count()

        data = serialize('json', queryset, use_natural_primary_keys=False)

        return JsonResponse({
            'status': 'ok',
            'model': model_path,
            'count': count,
            'data': data,
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
from ARQUIVOS.models import Administracao
from ARQUIVOS.sincronizacao import exportar_pacote, marcar_como_sincronizado, importar_pacote
from django.http import HttpResponse

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
    return render(request, 'Paginas/sincronizacao.html', {'administracoes': administracoes})
