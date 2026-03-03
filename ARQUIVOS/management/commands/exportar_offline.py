import os
import json
from django.core.management.base import BaseCommand
from ARQUIVOS.models import Administracao
from ARQUIVOS.sincronizacao import exportar_pacote, marcar_como_sincronizado

class Command(BaseCommand):
    help = 'Exportar pacote de sincronização offline para ficheiro JSON.'

    def add_arguments(self, parser):
        parser.add_argument('--origem', type=int, required=True, help='ID da administração de origem (a local)')
        parser.add_argument('--destino', type=int, required=False, help='ID da administração destino (opcional, para filtrar)')
        parser.add_argument('--arquivo', type=str, required=True, help='Caminho/nome do ficheiro exportado (ex: exportacao.json)')

    def handle(self, *args, **options):
        origem_id = options['origem']
        destino_id = options.get('destino')
        arquivo = options['arquivo']

        try:
            origem = Administracao.objects.get(id=origem_id)
            destino = Administracao.objects.get(id=destino_id) if destino_id else None

            self.stdout.write(f"Iniciando exportação a partir de: {origem.nome}...")
            if destino:
                self.stdout.write(f"Filtrando para o destino: {destino.nome}...")
            
            pacote = exportar_pacote(administracao_origem=origem, administracao_destino=destino)
            
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(pacote, f, ensure_ascii=False, indent=4)
                
            marcar_como_sincronizado(administracao_origem=origem, administracao_destino=destino)
            
            self.stdout.write(self.style.SUCCESS(f"Pacote exportado com sucesso em '{arquivo}' contendo {len(pacote['movimentacoes'])} movimentações!"))
            
        except Administracao.DoesNotExist:
            self.stderr.write(self.style.ERROR('Erro: A administração (origem ou destino) especificada não foi encontrada.'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Erro inesperado durante a exportação: {str(e)}'))
