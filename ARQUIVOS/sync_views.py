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
from django.db.models import Q, FileField, ImageField
from ARQUIVOS.consumers import send_notification_sync, send_pendencia_update_sync
from ARQUIVOS.sincronizacao import exportar_pacote, importar_pacote, marcar_como_sincronizado
from ARQUIVOS.models.sistema import ConfiguracaoSistema

logger = logging.getLogger('sync')


# ================================================================
# Função auxiliar: Resolver referências FK (Natural Keys -> PKs)
# ================================================================
def _resolver_fks_no_json(records, model):
    """
    Pré-processa uma lista de registos JSON (formato Django serializer)
    e substitui referências Natural Key (UUIDs) por PKs reais do servidor local.
    
    Quando serialize(..., use_natural_foreign_keys=True) é usado, FKs são escritas como:
      "fields": { "administracao": ["uuid-aqui"] }
    
    Em vez de depender de get_by_natural_key() (que pode falhar se o UUID não existe),
    esta função resolve cada FK manualmente usando uuid_sinc.
    """
    # Obter definição dos campos FK do modelo
    fk_fields = {}
    for field in model._meta.get_fields():
        if hasattr(field, 'related_model') and field.related_model and hasattr(field, 'name'):
            related_model = field.related_model
            # Verificar se o modelo relacionado tem uuid_sinc
            if hasattr(related_model, 'uuid_sinc'):
                fk_fields[field.name] = related_model

    resolved_records = []
    resolve_errors = []

    for record in records:
        fields = record.get('fields', {})
        had_error = False

        for field_name, related_model in fk_fields.items():
            value = fields.get(field_name)
            
            # Natural Key é uma lista: ["uuid-string"]
            if isinstance(value, list) and len(value) == 1:
                uuid_str = value[0]
                try:
                    related_obj = related_model.objects.get(uuid_sinc=uuid_str)
                    fields[field_name] = related_obj.pk
                except related_model.DoesNotExist:
                    # UUID não existe neste servidor - registar o erro
                    uuid_sinc_val = fields.get('uuid_sinc', 'desconhecido')
                    resolve_errors.append({
                        'uuid': str(uuid_sinc_val),
                        'error': f'{related_model.__name__} com uuid_sinc={uuid_str} não encontrado'
                    })
                    had_error = True
                    break
                except Exception as e:
                    uuid_sinc_val = fields.get('uuid_sinc', 'desconhecido')
                    resolve_errors.append({
                        'uuid': str(uuid_sinc_val),
                        'error': f'Erro ao resolver {field_name}: {e}'
                    })
                    had_error = True
                    break
            elif isinstance(value, list) and len(value) > 1:
                # Natural Key composta - tentar resolver via get_by_natural_key
                try:
                    related_obj = related_model.objects.get_by_natural_key(*value)
                    fields[field_name] = related_obj.pk
                except Exception:
                    # Fallback: se a lista contém um UUID, tentar por uuid_sinc
                    try:
                        related_obj = related_model.objects.get(uuid_sinc=value[0])
                        fields[field_name] = related_obj.pk
                    except Exception as e:
                        uuid_sinc_val = fields.get('uuid_sinc', 'desconhecido')
                        resolve_errors.append({
                            'uuid': str(uuid_sinc_val),
                            'error': f'{related_model.__name__} NK={value} não encontrado'
                        })
                        had_error = True
                        break
        
        if not had_error:
            resolved_records.append(record)

    return resolved_records, resolve_errors


def sync_auth_required(view_func):
    """Decorador que valida o token de autenticação para a API de sync."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        # Tenta obter do banco de dados de forma robusta
        ConfigModel = apps.get_model('ARQUIVOS', 'ConfiguracaoSistema')
        expected_token = ConfigModel.get_valor('SYNC_AUTH_TOKEN', settings.SYNC_AUTH_TOKEN)

        if not expected_token:
            return JsonResponse(
                {'error': 'SYNC_AUTH_TOKEN não configurado no servidor'},
                status=503
            )

        if auth_header != f"Token {expected_token}":
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
        skipped_records = []
        
        # Obter campos de arquivo para este modelo
        file_fields = [f.name for f in model._meta.get_fields() if isinstance(f, (FileField, ImageField))]

        # === FASE 1: Pré-processar JSON para resolver FKs por uuid_sinc ===
        import json as json_module
        records = json_module.loads(data)

        # Resolver FKs ANTES da deserialização
        resolved_records, fk_errors = _resolver_fks_no_json(records, model)
        skipped_records.extend(fk_errors)

        # === FASE 2: Processar os registos com FKs resolvidas ===
        for record in resolved_records:
            try:
                single_json = json_module.dumps([record])
                # use_natural_foreign_keys=False porque já resolvemos as FKs manualmente
                obj_list = list(deserialize('json', single_json))
                if not obj_list:
                    continue
                obj = obj_list[0]
            except Exception as deser_err:
                uuid_val = record.get('fields', {}).get('uuid_sinc', 'desconhecido')
                skipped_records.append({
                    'uuid': str(uuid_val),
                    'error': str(deser_err)
                })
                logger.warning(f'Push: registo ignorado em {model_path} (uuid={uuid_val}): {deser_err}')
                continue

            try:
                with transaction.atomic():
                    instance = obj.object
                    # Desabilitar validação durante sync
                    instance._skip_validation = True
                    uuid_sinc = instance.uuid_sinc

                    # Extrair arquivos do JSON estendido
                    files_data = body.get('files', {}).get(str(uuid_sinc), {})

                    # 1. Verificar se já existe por UUID
                    existing = model.objects.filter(uuid_sinc=uuid_sinc).first()
                    
                    # Fallback para Administracao (evitar erro de UUID diferente para mesma admin)
                    if not existing and model_path == 'ARQUIVOS.Administracao':
                        existing = model.objects.filter(nome=instance.nome).first()
                        if existing:
                            model.objects.filter(pk=existing.pk).update(uuid_sinc=uuid_sinc)
                            logger.info(f'Vinculada administração {instance.nome} por nome e atualizado UUID.')

                    # Fallback para Departamento (evitar erro de nome duplicado na mesma admin)
                    if not existing and model_path == 'ARQUIVOS.Departamento':
                        admin = getattr(instance, 'administracao', None)
                        if admin:
                            existing = model.objects.filter(nome=instance.nome, administracao=admin).first()
                            if existing:
                                model.objects.filter(pk=existing.pk).update(uuid_sinc=uuid_sinc)
                                logger.info(f'Vinculado departamento {instance.nome} por nome.')

                    # Fallback para Seccoes (evitar erro de nome duplicado no mesmo dept)
                    if not existing and model_path == 'ARQUIVOS.Seccoes':
                        dept = getattr(instance, 'departamento', None)
                        if dept:
                            existing = model.objects.filter(nome=instance.nome, departamento=dept).first()
                            if existing:
                                model.objects.filter(pk=existing.pk).update(uuid_sinc=uuid_sinc)
                                logger.info(f'Vinculada secção {instance.nome} por nome.')

                    # Fallback para CustomUser (evitar erro de username duplicado)
                    if not existing and model_path == 'ARQUIVOS.CustomUser':
                        existing = model.objects.filter(username=instance.username).first()
                        if existing:
                            model.objects.filter(pk=existing.pk).update(uuid_sinc=uuid_sinc)
                            logger.info(f'Vinculado usuário {instance.username} por username e atualizado UUID.')

                    # 2. Resolução de Conflitos ou Inserção
                    if existing:
                        # Estratégia: o que tem a data_modificacao mais recente vence
                        remote_mod = getattr(instance, 'data_modificacao', None)
                        local_mod = getattr(existing, 'data_modificacao', None)

                        if not local_mod or (remote_mod and remote_mod > local_mod):
                            # Remoto é mais recente: Atualizar local
                            for field in model._meta.fields:
                                if not field.primary_key and field.name not in ['uuid_sinc']:
                                    setattr(existing, field.name, getattr(instance, field.name))
                            
                            # Processar arquivos se houver
                            for field_name in file_fields:
                                field_data = files_data.get(field_name)
                                if field_data:
                                    content = base64.b64decode(field_data['content'])
                                    getattr(existing, field_name).save(field_data['name'], ContentFile(content), save=False)
                            
                            existing._skip_validation = True
                            try:
                                update_fields = [f.name for f in model._meta.fields if not f.primary_key and not isinstance(f, (FileField, ImageField))] + ['pendente_sinc']
                                existing.save(update_fields=update_fields)
                            except Exception as save_err:
                                logger.error(f"Erro ao atualizar {model_path} {uuid_sinc}: {save_err}")
                                skipped_records.append({
                                    'uuid': str(uuid_sinc),
                                    'error': str(save_err)
                                })
                                continue
                                
                            instance = existing 
                        else:
                            logger.debug(f'Ignorado push de {uuid_sinc}: versão local é mais recente.')
                            synced_uuids.append(str(uuid_sinc))
                            continue
                    else:
                        # Novo registo: Inserir
                        for field_name in file_fields:
                            field_data = files_data.get(field_name)
                            if field_data:
                                content = base64.b64decode(field_data['content'])
                                getattr(instance, field_name).save(field_data['name'], ContentFile(content), save=False)
                        
                        instance.pendente_sinc = False
                        instance._skip_validation = True
                        try:
                            instance.save()
                        except Exception as save_err:
                            logger.error(f"Erro ao inserir novo {model_path} {uuid_sinc}: {save_err}")
                            skipped_records.append({
                                'uuid': str(uuid_sinc),
                                'error': str(save_err)
                            })
                            continue

                    # Marcar como sincronizado e definir origem
                    model.objects.filter(uuid_sinc=uuid_sinc).update(
                        pendente_sinc=False,
                        ultima_sincronizacao=timezone.now(),
                        origem_instancia=instance_id,
                    )
                    synced_uuids.append(str(uuid_sinc))

                    # --- Gatilhos de WebSocket Real-time ---
                    try:
                        if model_path == 'ARQUIVOS.Notificacao':
                            group_name = f"user_{instance.usuario_id}"
                            send_notification_sync(group_name, instance.mensagem, instance.link)
                        elif model_path == 'ARQUIVOS.MovimentacaoDocumento':
                            if instance.tipo_movimentacao == 'encaminhamento':
                                if instance.seccao_destino_id:
                                    group_name = f"seccao_{instance.seccao_destino_id}"
                                else:
                                    group_name = f"departamento_{instance.departamento_destino_id}"
                                send_pendencia_update_sync(group_name, f"Novo documento recebido: {instance.documento.numero_protocolo}")
                    except Exception as ws_err:
                        logger.warning(f"Erro ao disparar WebSocket durante sync push: {ws_err}")

            except Exception as record_err:
                uuid_val = str(record.get('fields', {}).get('uuid_sinc', 'desconhecido'))
                skipped_records.append({
                    'uuid': uuid_val,
                    'error': str(record_err)
                })
                logger.warning(f'Push: erro ao processar registo {model_path} (uuid={uuid_val}): {record_err}')

        logger.info(f'Sync push de {instance_id}: {len(synced_uuids)} sincronizados, {len(skipped_records)} ignorados de {model_path}')

        return JsonResponse({
            'status': 'ok',
            'synced_uuids': synced_uuids,
            'skipped_records': skipped_records,
            'count': len(synced_uuids),
            'skipped': len(skipped_records),
        })

    except Exception as e:
        import traceback
        error_msg = str(e)
        logger.error(f'Erro no sync push: {error_msg}')
        logger.error(traceback.format_exc())
        return JsonResponse({'error': error_msg}, status=500)


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
        page = int(request.GET.get('page', '0'))

        if not model_path:
            return JsonResponse({'error': 'Campo model é obrigatório'}, status=400)

        if model_path not in settings.SYNC_MODELS:
            return JsonResponse({'error': f'Modelo {model_path} não permitido para sync'}, status=403)

        model = apps.get_model(model_path)
        batch_size = settings.SYNC_BATCH_SIZE

        # Obter todos os registos relevantes
        queryset = model.objects.all()

        # Evitar enviar de volta o que a própria instância acabou de carregar (evitar eco)
        # MAS apenas se for um pull incremental (since definido).
        # Se for um pull total (since vazio), permitimos recuperar registros próprios (ex: após reset da DB local)
        if instance_id and hasattr(model, 'origem_instancia') and since:
            queryset = queryset.exclude(origem_instancia=instance_id)

        if since:
            from django.utils.dateparse import parse_datetime
            since_dt = parse_datetime(since)
            if since_dt:
                # CORREÇÃO: Usar data_modificacao OU ultima_sincronizacao
                # Garante que dados criados na nuvem (sem ultima_sincronizacao) sejam sincronizados
                queryset = queryset.filter(Q(ultima_sincronizacao__gt=since_dt) | Q(data_modificacao__gt=since_dt))

        # Paginação: usar offset baseado na página
        # IMPORTANTE: order_by garante ordem consistente entre páginas
        offset = page * batch_size
        queryset = queryset.order_by('pk')[offset:offset + batch_size]
        count = queryset.count()

        # Serialização usando Natural Keys para enviar UUIDs em vez de PKs numéricas
        data = serialize('json', queryset, use_natural_foreign_keys=True, use_natural_primary_keys=True)
        
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
