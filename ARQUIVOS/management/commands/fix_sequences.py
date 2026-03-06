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
        
        # Lista de apps para processar
        apps = ['ARQUIVOS', 'auth', 'contenttypes']
        
        try:
            output = StringIO()
            # O comando sqlsequencereset gera o SQL necessário para resetar as sequências
            for app in apps:
                self.stdout.write(f'A processar app: {app}...')
                call_command('sqlsequencereset', app, stdout=output)
            
            sql = output.getvalue()
            
            if not sql:
                self.stdout.write(self.style.SUCCESS('Nenhuma sequência precisa de correção.'))
                return

            self.stdout.write(self.style.NOTICE('Executando comandos de reset...'))
            
            with connection.cursor() as cursor:
                # O sqlsequencereset gera blocos com BEGIN; e COMMIT;
                # Vamos executar apenas as linhas que começam por SELECT ou TRUNCATE
                for line in sql.split('\n'):
                    cmd = line.strip()
                    if not cmd:
                        continue
                    
                    # Remover ponto e vírgula do fim para o execute()
                    cmd_clean = cmd.rstrip(';')
                    
                    if cmd_clean.upper().startswith('SELECT') or cmd_clean.upper().startswith('TRUNCATE'):
                        # self.stdout.write(f'A executar: {cmd_clean}')
                        cursor.execute(cmd_clean)
                
            self.stdout.write(self.style.SUCCESS('✅ Todas as sequências foram corrigidas com sucesso!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao corrigir sequências: {str(e)}'))
            logger.error(f"Erro no fix_sequences: {e}")
