"""
Management command para sincronizar dados entre instância local e servidor central.

Uso:
    python manage.py sync_data              # Sincroniza tudo (push + pull)
    python manage.py sync_data --push       # Apenas envia dados locais
    python manage.py sync_data --pull       # Apenas recebe dados do servidor
    python manage.py sync_data --status     # Mostra estado de sincronização
    python manage.py sync_data --daemon     # Executa continuamente em background
"""
import json
import time
import logging
import requests
import base64
import os
from django.core.files.base import ContentFile
from django.db.models import FileField, ImageField
from ARQUIVOS.consumers import send_notification_sync, send_pendencia_update_sync
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.apps import apps
from django.core.serializers import serialize, deserialize
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger('sync')


class Command(BaseCommand):
    help = 'Sincroniza dados entre a instância local e o servidor central'

    def add_arguments(self, parser):
        parser.add_argument(
            '--push', action='store_true',
            help='Apenas enviar dados locais para o servidor central'
        )
        parser.add_argument(
            '--pull', action='store_true',
            help='Apenas receber dados do servidor central'
        )
        parser.add_argument(
            '--status', action='store_true',
            help='Mostrar estado actual de sincronização'
        )
        parser.add_argument(
            '--daemon', action='store_true',
            help='Executar continuamente em segundo plano'
        )

    def handle(self, *args, **options):
        self.central_url = settings.SYNC_CENTRAL_URL
        self.auth_token = settings.SYNC_AUTH_TOKEN
        self.instance_id = settings.SYNC_INSTANCE_ID
        self.batch_size = settings.SYNC_BATCH_SIZE

        if options['status']:
            self._show_status()
            return

        if not self.central_url:
            self.stdout.write(self.style.WARNING(
                '⚠ SYNC_CENTRAL_URL não configurada. '
                'A sincronização será registada localmente mas não será enviada.'
            ))

        if options['daemon']:
            self._run_daemon()
            return

        # Sincronização única
        if options['push']:
            self._push_data()
        elif options['pull']:
            self._pull_data()
        else:
            # Push + Pull (sync completo)
            self._push_data()
            self._pull_data()

    def _show_status(self):
        """Mostra quantos registos estão pendentes de sincronização."""
        self.stdout.write(self.style.HTTP_INFO('\n📊 Estado de Sincronização'))
        self.stdout.write(f'   Instância: {self.instance_id}')
        self.stdout.write(f'   Servidor Central: {self.central_url or "(não configurado)"}')
        self.stdout.write('')

        total_pendentes = 0
        for model_path in settings.SYNC_MODELS:
            try:
                model = apps.get_model(model_path)
                # Verificar se o modelo tem os campos de sincronização
                if not hasattr(model, 'pendente_sinc'):
                    self.stdout.write(f'   ⏭ {model_path}: sem campos de sincronização')
                    continue

                pendentes = model.objects.filter(pendente_sinc=True).count()
                total = model.objects.count()
                total_pendentes += pendentes

                if pendentes > 0:
                    self.stdout.write(
                        self.style.WARNING(f'   🔄 {model_path}: {pendentes}/{total} pendentes')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ {model_path}: {total} registos sincronizados')
                    )
            except LookupError:
                self.stdout.write(self.style.ERROR(f'   ❌ {model_path}: modelo não encontrado'))

        self.stdout.write('')
        if total_pendentes > 0:
            self.stdout.write(self.style.WARNING(
                f'   📤 Total pendente: {total_pendentes} registos aguardando envio'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ Tudo sincronizado!'))
        self.stdout.write('')

    def _push_data(self):
        """Envia registos pendentes para o servidor central."""
        self.stdout.write(self.style.HTTP_INFO('\n📤 A enviar dados para o servidor central...'))

        if not self.central_url:
            self.stdout.write(self.style.WARNING(
                '   ⚠ Servidor central não configurado. Registos ficam marcados como pendentes.'
            ))
            return

        for model_path in settings.SYNC_MODELS:
            try:
                model = apps.get_model(model_path)
                if not hasattr(model, 'pendente_sinc'):
                    continue

                pendentes = model.objects.filter(pendente_sinc=True)[:self.batch_size]
                count = pendentes.count()

                if count == 0:
                    continue

                self.stdout.write(f'   📦 {model_path}: a enviar {count} registos...')

                # Serializar para JSON usando Natural Keys para resolver FKs via UUID
                data = serialize('json', pendentes, use_natural_foreign_keys=True, use_natural_primary_keys=True)

                # Extrair arquivos em Base64 para envio
                files_dict = {}
                file_fields = [f.name for f in model._meta.get_fields() if isinstance(f, (FileField, ImageField))]
                
                if file_fields:
                    for item in pendentes:
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
                                    self.stdout.write(self.style.ERROR(f'   ❌ Erro ao ler ficheiro {field.name}: {e}'))
                        
                        if item_files:
                            files_dict[str(item.uuid_sinc)] = item_files

                try:
                    response = requests.post(
                        f'{self.central_url}/api/sync/push/',
                        json={
                            'instance_id': self.instance_id,
                            'model': model_path,
                            'data': data,
                            'files': files_dict,
                        },
                        headers={
                            'Authorization': f'Token {self.auth_token}',
                            'Content-Type': 'application/json',
                        },
                        timeout=30,
                    )

                    if response.status_code == 200:
                        result = response.json()
                        # Marcar APENAS os registos que foram aceites (não os skipped)
                        synced_uuids = result.get('synced_uuids', [])
                        skipped_records = result.get('skipped_records', [])
                        skipped_count = result.get('skipped', 0)
                        now = timezone.now()
                        if synced_uuids:
                            model.objects.filter(
                                uuid_sinc__in=synced_uuids
                            ).update(
                                pendente_sinc=False,
                                ultima_sincronizacao=now,
                            )
                        msg = f'   ✅ {model_path}: {len(synced_uuids)} sincronizados'
                        if skipped_count:
                            msg += f' | {skipped_count} ignorados'
                            for skip in skipped_records[:5]: # Mostrar apenas os primeiros 5 para não inundar o log
                                msg += f'\n      ⚠️ {skip.get("uuid")}: {skip.get("error")}'
                            if skipped_count > 5:
                                msg += f'\n      ... e mais {skipped_count - 5} outros.'
                        self.stdout.write(self.style.SUCCESS(msg))
                    else:
                        self.stdout.write(self.style.ERROR(
                            f'   ❌ {model_path}: erro HTTP {response.status_code}'
                        ))

                except requests.ConnectionError:
                    self.stdout.write(self.style.ERROR(
                        f'   ❌ Sem conexão com o servidor central'
                    ))
                    return  # Parar todo o push se não há ligação
                except requests.Timeout:
                    self.stdout.write(self.style.ERROR(
                        f'   ⏱ Timeout ao enviar {model_path}'
                    ))

            except LookupError:
                self.stdout.write(self.style.ERROR(f'   ❌ Modelo {model_path} não encontrado'))

    def _pull_data(self):
        """Recebe registos novos/actualizados do servidor central."""
        self.stdout.write(self.style.HTTP_INFO('\n📥 A receber dados do servidor central...'))

        if not self.central_url:
            self.stdout.write(self.style.WARNING(
                '   ⚠ Servidor central não configurado.'
            ))
            return

        # Coleccionar modelos com registos ignorados para uma segunda passagem
        models_to_retry = []

        for model_path in settings.SYNC_MODELS:
            skipped_total = self._pull_model(model_path)
            if skipped_total > 0:
                models_to_retry.append((model_path, skipped_total))

        # --- SEGUNDA PASSAGEM: Re-tentar modelos com dependências em falta ---
        # Depois de todos os modelos base terem sido puxados, as dependências
        # que faltavam na 1ª passagem podem agora existir localmente.
        if models_to_retry:
            self.stdout.write(self.style.HTTP_INFO(
                f'\n🔄 Segunda passagem: a re-tentar {len(models_to_retry)} modelos com registos ignorados...'
            ))
            for model_path, prev_skipped in models_to_retry:
                skipped = self._pull_model(model_path)
                if skipped > 0:
                    self.stdout.write(self.style.WARNING(
                        f'   ⚠️ {model_path}: ainda restam {skipped} registos com dependências em falta'
                    ))
                else:
                    self.stdout.write(self.style.SUCCESS(
                        f'   ✅ {model_path}: todos os {prev_skipped} registos anteriormente ignorados foram importados com sucesso!'
                    ))

    def _pull_model(self, model_path):
        """Puxa um modelo específico do servidor. Retorna o total de registos ignorados."""
        total_skipped = 0
        has_more = True
        page = 0
        while has_more:
            try:
                model = apps.get_model(model_path)
                if not hasattr(model, 'ultima_sincronizacao'):
                    return 0

                from datetime import timedelta
                last_sync = model.objects.filter(
                    ultima_sincronizacao__isnull=False
                ).order_by('-ultima_sincronizacao').values_list(
                    'ultima_sincronizacao', flat=True
                ).first()

                # Margem de segurança para lidar com variações de relógio entre os servidores
                since_time = last_sync - timedelta(minutes=5) if last_sync else None

                # Metadados base (Foundational) devem ser sempre puxados na totalidade 
                # Adicionado CustomUser para garantir que todos os usuários existam localmente para FKs
                if model_path in ['ARQUIVOS.Administracao', 'ARQUIVOS.TipoDocumento', 
                                  'ARQUIVOS.Departamento', 'ARQUIVOS.Seccoes', 'ARQUIVOS.CustomUser',
                                  'ARQUIVOS.ConfiguracaoSistema', 'ARQUIVOS.LocalArmazenamento']:
                    since_time = None

                params = {
                    'instance_id': self.instance_id,
                    'model': model_path,
                    'since': since_time.isoformat() if since_time else '',
                    'page': page,
                }

                response = requests.get(
                    f'{self.central_url}/api/sync/pull/',
                    params=params,
                    headers={
                        'Authorization': f'Token {self.auth_token}',
                    },
                    timeout=30,
                )

                if response.status_code == 200:
                    result = response.json()
                    data = result.get('data', '[]')
                    count = result.get('count', 0)

                    # ROBUSTEZ: Continuar enquanto houver registos, independentemente de batch_size
                    # Isso evita parar se o servidor tiver um limite menor que o cliente
                    has_more = (count > 0)

                    if count == 0:
                        has_more = False
                        continue

                    self.stdout.write(f'   📦 {model_path}: a receber {count} registos...')

                    # Deserializar e salvar — REGISTO A REGISTO com transaction individual
                    try:
                        files_data_all = result.get('files', {})
                        file_fields = [f.name for f in model._meta.get_fields() if isinstance(f, (FileField, ImageField))]

                        import json as json_module
                        records = json_module.loads(data)
                        skipped = 0
                        for record in records:
                            try:
                                single_json = json_module.dumps([record])
                                obj_list = list(deserialize('json', single_json, use_natural_foreign_keys=True))
                                if not obj_list:
                                    continue
                                obj = obj_list[0]
                            except Exception as deser_err:
                                skipped += 1
                                self.stdout.write(self.style.WARNING(
                                    f'   ⚠️ Registo ignorado em {model_path}: {deser_err}'
                                ))
                                continue

                            try:
                                with transaction.atomic():
                                    instance = obj.object
                                    uuid_str = str(instance.uuid_sinc)
                                    files_data = files_data_all.get(uuid_str, {})

                                    # 1. Verificar se já existe por UUID
                                    existing = model.objects.filter(
                                        uuid_sinc=instance.uuid_sinc
                                    ).first()

                                    # Fallback para Departamento
                                    if not existing and model_path == 'ARQUIVOS.Departamento':
                                        admin = getattr(instance, 'administracao', None)
                                        if admin:
                                            existing = model.objects.filter(nome=instance.nome, administracao=admin).first()
                                            if existing:
                                                model.objects.filter(pk=existing.pk).update(uuid_sinc=instance.uuid_sinc)
                                                self.stdout.write(self.style.WARNING(f'   ⚠️ Departamento {instance.nome} vinculado por nome.'))

                                    # Fallback para Seccoes
                                    if not existing and model_path == 'ARQUIVOS.Seccoes':
                                        dept = getattr(instance, 'departamento', None)
                                        if dept:
                                            existing = model.objects.filter(nome=instance.nome, departamento=dept).first()
                                            if existing:
                                                model.objects.filter(pk=existing.pk).update(uuid_sinc=instance.uuid_sinc)
                                                self.stdout.write(self.style.WARNING(f'   ⚠️ Secção {instance.nome} vinculada por nome.'))

                                    # Fallback para CustomUser
                                    if not existing and model_path == 'ARQUIVOS.CustomUser':
                                        existing = model.objects.filter(username=instance.username).first()
                                        if existing:
                                            model.objects.filter(pk=existing.pk).update(uuid_sinc=instance.uuid_sinc)
                                            self.stdout.write(self.style.WARNING(f'   ⚠️ Usuário {instance.username} vinculado por username.'))

                                    # 2. Resolução de Conflitos ou Inserção
                                    if existing:
                                        remote_mod = getattr(instance, 'data_modificacao', None)
                                        local_mod = getattr(existing, 'data_modificacao', None)

                                        if not local_mod or (remote_mod and remote_mod > local_mod):
                                            for field in model._meta.fields:
                                                if not field.primary_key and field.name not in ['uuid_sinc']:
                                                    setattr(existing, field.name, getattr(instance, field.name))
                                            
                                            for field_name in file_fields:
                                                f_data = files_data.get(field_name)
                                                if f_data:
                                                    content = base64.b64decode(f_data['content'])
                                                    getattr(existing, field_name).save(f_data['name'], ContentFile(content), save=False)
                                            
                                            existing.save(update_fields=[f.name for f in model._meta.fields if not f.primary_key] + ['pendente_sinc'])
                                            instance = existing
                                        else:
                                            continue
                                    else:
                                        for field_name in file_fields:
                                            f_data = files_data.get(field_name)
                                            if f_data:
                                                content = base64.b64decode(f_data['content'])
                                                getattr(instance, field_name).save(f_data['name'], ContentFile(content), save=False)
                                        
                                        instance.pendente_sinc = False
                                        instance.save()

                                    # Marcar como sincronizado localmente
                                    model.objects.filter(
                                        uuid_sinc=instance.uuid_sinc
                                    ).update(
                                        pendente_sinc=False,
                                        ultima_sincronizacao=timezone.now(),
                                    )

                                    # Gatilhos Real-time
                                    try:
                                        if model_path == 'ARQUIVOS.Notificacao':
                                            group_name = f"user_{instance.usuario_id}"
                                            send_notification_sync(group_name, instance.mensagem, instance.link)
                                        elif model_path == 'ARQUIVOS.MovimentacaoDocumento':
                                            if instance.tipo_movimentacao == 'encaminhamento':
                                                dest_group = f"seccao_{instance.seccao_destino_id}" if instance.seccao_destino_id else f"departamento_{instance.departamento_destino_id}"
                                                send_pendencia_update_sync(dest_group, f"Novo documento recebido via sync: {instance.documento.numero_protocolo}")
                                    except Exception:
                                        pass

                            except Exception as record_err:
                                skipped += 1
                                self.stdout.write(self.style.WARNING(
                                    f'   ⚠️ Erro ao guardar registo em {model_path}: {record_err}'
                                ))

                        total_skipped += skipped
                        msg = f'   ✅ {model_path}: {count - skipped} recebidos (página {page + 1})'
                        if skipped:
                            msg += f' | {skipped} ignorados (dependências em falta)'
                        self.stdout.write(self.style.SUCCESS(msg))
                        page += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'   ❌ Erro ao processar {model_path}: {e}'))
                        has_more = False
                else:
                    self.stdout.write(self.style.ERROR(
                        f'   ❌ {model_path}: erro HTTP {response.status_code}'
                    ))
                    has_more = False

            except requests.ConnectionError:
                self.stdout.write(self.style.ERROR(f'   ❌ Sem conexão com o servidor central'))
                return total_skipped
            except requests.Timeout:
                self.stdout.write(self.style.ERROR(f'   ⏱ Timeout ao receber {model_path}'))
                has_more = False
            except LookupError:
                self.stdout.write(self.style.ERROR(f'   ❌ Modelo {model_path} não encontrado'))
                has_more = False
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Erro inesperado em {model_path}: {e}'))
                has_more = False

        return total_skipped

    def _run_daemon(self):
        """Executa sincronização continuamente em background."""
        interval = settings.SYNC_INTERVAL_SECONDS
        self.stdout.write(self.style.SUCCESS(
            f'\n🔁 Modo daemon iniciado (intervalo: {interval}s)\n'
            f'   Pressione Ctrl+C para parar.\n'
        ))

        while True:
            try:
                self.stdout.write(f'\n⏰ [{timezone.now().strftime("%H:%M:%S")}] A sincronizar...')
                self._push_data()
                self._pull_data()
                self.stdout.write(f'   💤 Próxima sincronização em {interval}s...')
                time.sleep(interval)
            except KeyboardInterrupt:
                self.stdout.write(self.style.SUCCESS('\n👋 Daemon de sincronização parado.'))
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Erro: {e}'))
                self.stdout.write(f'   🔄 Nova tentativa em {interval}s...')
                time.sleep(interval)
