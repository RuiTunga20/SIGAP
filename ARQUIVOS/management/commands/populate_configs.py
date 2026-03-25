from django.core.management.base import BaseCommand
from django.conf import settings
from ARQUIVOS.models.sistema import ConfiguracaoSistema
import os

class Command(BaseCommand):
    help = 'Popula a tabela ConfiguracaoSistema com valores do .env'

    def handle(self, *args, **options):
        configs = [
            {
                'chave': 'WHATSAPP_TOKEN',
                'valor': getattr(settings, 'WHATSAPP_TOKEN', os.getenv('WHATSAPP_TOKEN', '')),
                'descricao': 'Token de autenticação da API do WhatsApp (Meta)'
            },
            {
                'chave': 'WHATSAPP_PHONE_NUMBER_ID',
                'valor': getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')),
                'descricao': 'ID do número de telefone da API do WhatsApp'
            },
            {
                'chave': 'WHATSAPP_API_URL',
                'valor': getattr(settings, 'WHATSAPP_API_URL', f"https://graph.facebook.com/v22.0/{getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', os.getenv('WHATSAPP_PHONE_NUMBER_ID', ''))}/messages"),
                'descricao': 'URL da API do WhatsApp/SMS'
            },
            {
                'chave': 'SYNC_AUTH_TOKEN',
                'valor': getattr(settings, 'SYNC_AUTH_TOKEN', os.getenv('SYNC_AUTH_TOKEN', '')),
                'descricao': 'Token de autenticação entre instâncias SIGAP'
            },
            {
                'chave': 'SYNC_CENTRAL_URL',
                'valor': getattr(settings, 'SYNC_CENTRAL_URL', os.getenv('SYNC_CENTRAL_URL', '')),
                'descricao': 'URL do servidor central de sincronização'
            }
        ]

        for config in configs:
            obj, created = ConfiguracaoSistema.objects.get_or_create(
                chave=config['chave'],
                defaults={'valor': config['valor'], 'descricao': config['descricao']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Criada configuração: {config['chave']}"))
            else:
                if not obj.valor and config['valor']:
                    obj.valor = config['valor']
                    obj.save()
                    self.stdout.write(self.style.SUCCESS(f"🆙 Atualizada configuração (vazia): {config['chave']}"))
                else:
                    self.stdout.write(f"ℹ️ Configuração já existe: {config['chave']}")

        self.stdout.write(self.style.SUCCESS("\nConcluído! Já pode editar estas configurações no Admin do Django."))
