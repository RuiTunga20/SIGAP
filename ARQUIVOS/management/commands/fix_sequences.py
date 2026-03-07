import logging
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from io import StringIO

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Corrige as sequências (auto-incremento) da base de dados PostgreSQL após importações manuais.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Iniciando correção de sequências...'))
        
        # Tenta obter todos os apps instalados que tenham modelos
        from django.apps import apps as django_apps
        target_apps = [app_config.label for app_config in django_apps.get_app_configs() 
                       if not app_config.models_module is None]
        
        try:
            output = StringIO()
            for app in target_apps:
                self.stdout.write(f'A processar app: {app}...')
                call_command('sqlsequencereset', app, stdout=output)
            
            sql = output.getvalue()
            
            if not sql:
                self.stdout.write(self.style.SUCCESS('Nenhuma sequência precisa de correção.'))
                return

            self.stdout.write(self.style.NOTICE('Executando comandos de reset...'))
            
            with connection.cursor() as cursor:
                # O sqlsequencereset gera comandos SQL. Vamos executá-los.
                # Filtramos linhas vazias e comentários
                for line in sql.split('\n'):
                    cmd = line.strip()
                    if not cmd or cmd.startswith('--'):
                        continue
                    
                    # O Django gera blocos com BEGIN; e COMMIT; se não estivermos em transação gerenciada.
                    # Mas no execute() do cursor, devemos evitar BEGIN/COMMIT manuais se possível,
                    # ou garantir que o comando seja válido.
                    if cmd.upper() in ['BEGIN;', 'COMMIT;']:
                        continue

                    try:
                        cursor.execute(cmd)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'Aviso ao executar "{cmd[:50]}...": {e}'))
                
            self.stdout.write(self.style.SUCCESS('✅ Todas as sequências foram corrigidas com sucesso!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao corrigir sequências: {str(e)}'))
            logger.error(f"Erro no fix_sequences: {e}")
