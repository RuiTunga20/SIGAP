import os
import json
from django.core.management.base import BaseCommand
from ARQUIVOS.models import Administracao
from ARQUIVOS.sincronizacao import importar_pacote

class Command(BaseCommand):
    help = 'Importar pacote de sincronização offline a partir de ficheiro JSON.'

    def add_arguments(self, parser):
        parser.add_argument('--destino', type=int, required=True, help='ID da administração destino local que recebe os dados')
        parser.add_argument('--arquivo', type=str, required=True, help='Caminho do ficheiro a ser importado (ex: importacao.json)')

    def handle(self, *args, **options):
        destino_id = options['destino']
        arquivo = options['arquivo']

        if not os.path.exists(arquivo):
            self.stderr.write(self.style.ERROR(f"Erro: O ficheiro '{arquivo}' não foi encontrado."))
            return

        try:
            destino = Administracao.objects.get(id=destino_id)

            self.stdout.write(f"Iniciando importação de pacote para: {destino.nome}...")
            
            with open(arquivo, 'r', encoding='utf-8') as f:
                pacote = json.load(f)
                
            resultados = importar_pacote(pacote_json=pacote, administracao_destino=destino)
            
            self.stdout.write(self.style.SUCCESS('Importação concluída com sucesso!'))
            self.stdout.write(f" - Importados: {resultados['importados']}")
            self.stdout.write(f" - Duplicados ignorados: {resultados['duplicados']}")
            if resultados.get('erros'):
                self.stderr.write(self.style.WARNING(f" - Erros ({len(resultados['erros'])}):"))
                for err in resultados['erros']:
                    self.stderr.write(f"   > {err}")
                    
        except Administracao.DoesNotExist:
            self.stderr.write(self.style.ERROR('Erro: Administração de destino não encontrada.'))
        except json.JSONDecodeError:
            self.stderr.write(self.style.ERROR('Erro: Ficheiro inválido ou não é um JSON válido.'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Erro inesperado durante a importação: {str(e)}'))
