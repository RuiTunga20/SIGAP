import io
import os
import base64
import requests
import json
import logging
from django.core.files.base import ContentFile
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Frame, KeepInFrame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from django.utils import timezone
from django.template.loader import render_to_string
from xhtml2pdf import pisa
import qrcode


def _obter_caminho_brasao():
    """Retorna o caminho absoluto para o brasão de Angola."""
    caminhos = [
        os.path.join(settings.BASE_DIR, 'ARQUIVOS', 'static', 'img', 'brasao_angola.png'),
        os.path.join(settings.STATIC_ROOT or '', 'img', 'brasao_angola.png'),
    ]
    for caminho in caminhos:
        if os.path.exists(caminho):
            return caminho
    return None


def _obter_caminho_logo_governo():
    """Retorna o caminho absoluto para o logo novo do Governo de Angola."""
    caminhos = [
        os.path.join(settings.BASE_DIR, 'ARQUIVOS', 'static', 'img', 'logo_governo_angola.png'),
        os.path.join(settings.STATIC_ROOT or '', 'img', 'logo_governo_angola.png'),
    ]
    for caminho in caminhos:
        if os.path.exists(caminho):
            return caminho
    return None


MESES_PT = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}


def _de_ou_do(nome):
    """
    Retorna 'DE' ou 'DO' baseando-se na última letra do nome.
    Se terminar em 'A', retorna 'DE'. Caso contrário, retorna 'DO'.
    """
    if not nome:
        return "DE"
    # Limpa espaços e pega a última letra
    ultimo_char = nome.strip().upper()[-1:]
    return "DE" if ultimo_char == 'A' else "DO"


def _construir_cabecalho(admin, usuario=None):
    """
    Constrói as linhas do cabeçalho hierárquico baseado no tipo de administração e no usuário.
    Retorna lista de strings para desenhar centradas.
    """
    linhas = ['REPÚBLICA DE ANGOLA']

    if not admin:
        return linhas

    tipo = admin.tipo_municipio
    
    # Extrair departamento/gabinete do usuário
    depto_nome = "SECRETARIA GERAL"
    if usuario and hasattr(usuario, 'departamento_efetivo') and usuario.departamento_efetivo:
        depto_nome = usuario.departamento_efetivo.nome.upper()

    if tipo == 'M':
        # MAT: República → Ministério → Departamento
        linhas.append(admin.nome.upper())
        linhas.append(depto_nome)

    elif tipo == 'G':
        # Governo Provincial: República → Governo Provincial de [X] → Departamento
        prov_nome = admin.nome.upper()
        if not prov_nome.startswith('GOVERNO'):
            prefixo = f"GOVERNO PROVINCIAL {_de_ou_do(admin.nome)}"
            prov_nome = f"{prefixo} {prov_nome}"
        linhas.append(prov_nome)
        linhas.append(depto_nome)

    else:
        # Admin Municipal (A-E):
        # República → Governo Provincial de [Prov] → Administração Municipal de [X] → Departamento
        provincia = admin.provincia or ''
        if provincia:
            prefixo_gov = f"GOVERNO PROVINCIAL {_de_ou_do(provincia)}"
            linhas.append(f"{prefixo_gov} {provincia.upper()}")
        
        mun_nome = admin.nome.upper()
        if not mun_nome.startswith('ADMINISTRAÇÃO'):
            prefixo_mun = f"ADMINISTRAÇÃO MUNICIPAL {_de_ou_do(admin.nome)}"
            mun_nome = f"{prefixo_mun} {mun_nome}"
        
        linhas.append(mun_nome)
        linhas.append(depto_nome)

    return linhas


def gerar_pdf_despacho(documento, texto_despacho, usuario_responsavel, novo_status, request=None):
    """
    Gera um PDF de despacho usando xhtml2pdf (HTML to PDF).
    Inclui um código QR de verificação em vez da assinatura tradicional.
    """
    # Usar a administração de quem assina o despacho para o cabeçalho/contexto
    admin = usuario_responsavel.administracao or documento.administracao
    brasao_path = _obter_caminho_brasao()
    logo_path = _obter_caminho_logo_governo()
    linhas_cabecalho = _construir_cabecalho(admin, usuario_responsavel)
    
    # Data formatada
    data_actual = timezone.now()
    local_nome = admin.provincia or admin.nome if admin else "Angola"
    nome_curto = admin.nome.split('(')[0].strip() if admin else "Angola"
    data_texto = (
        f"{nome_curto}, em {local_nome} aos, "
        f"{data_actual.day:02d} de {MESES_PT[data_actual.month]} de {data_actual.year}."
    )
    
    # Cargo
    dept_nome = ""
    if hasattr(usuario_responsavel, 'departamento_efetivo') and usuario_responsavel.departamento_efetivo:
        dept_nome = usuario_responsavel.departamento_efetivo.nome
    cargo_texto = dept_nome.upper() if dept_nome else "A SECRETÁRIA GERAL"
    
    # Gerar QR Code de verificação
    qr_base64 = None
    url_verificacao = ''
    
    # Prioridade para o servidor central (online) se configurado, para que a verificação funcione via internet
    central_url = getattr(settings, 'SYNC_CENTRAL_URL', '').rstrip('/')
    from django.urls import reverse
    path_verificacao = reverse('verificar_despacho', args=[str(documento.token_verificacao)])
    
    if central_url:
        url_verificacao = f"{central_url}{path_verificacao}"
    elif request:
        url_verificacao = request.build_absolute_uri(path_verificacao)
    else:
        url_verificacao = f'/verificar-despacho/{documento.token_verificacao}/'
    
    # Gerar email dinâmico para o rodapé (ex: uige@sigap.gov.ao)
    import re
    def slugify_simple(text):
        if not text: return "geral"
        text = text.lower()
        # Remove "administração municipal" ou similares para ficar só o nome principal
        text = text.replace('administração municipal de', '').replace('administração municipal do', '').replace('governo provincial de', '').strip()
        text = text.split('(')[0].strip() # Remove parênteses
        text = re.sub(r'[^a-z0-9]', '', text)
        return text or "geral"

    nome_slug = slugify_simple(admin.nome)
    admin_email = f"{nome_slug}@sigap.gov.ao"
    
    # Gerar imagem QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url_verificacao)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color='black', back_color='white')
    
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')
    
    # Contexto para o template
    contexto = {
        'documento': documento,
        'texto_despacho': texto_despacho,
        'nome_responsavel': usuario_responsavel.get_full_name() or usuario_responsavel.username,
        'cargo_texto': cargo_texto,
        'admin': admin,
        'brasao_path': brasao_path,
        'logo_path': logo_path,
        'linhas_cabecalho': linhas_cabecalho,
        'data_texto': data_texto,
        'qr_base64': qr_base64,
        'url_verificacao': url_verificacao,
        'admin_email': admin_email,
    }
    
    # Renderizar HTML
    html = render_to_string('pdf/despacho_pdf.html', contexto)
    
    # Gerar PDF
    buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=buffer)
    
    if pisa_status.err:
        raise Exception("Erro ao gerar PDF com xhtml2pdf")
        
    buffer.seek(0)
    return ContentFile(
        buffer.getvalue(),
        name=f"despacho_{documento.numero_protocolo.replace('/', '-')}.pdf"
    )

logger = logging.getLogger(__name__)

def enviar_whatsapp_notificacao(telefone, context=None):
    """
    Envia uma notificação via WhatsApp utilizando a API oficial da Meta.
    O telefone deve ser válido (idealmente com indicativo 244 para Angola).
    """
    if not telefone:
        return False
        
    numero = str(telefone).strip().replace(" ", "")
    # A API oficial do WhatsApp exige o número com código do país, sem o '+' e sem zeros à esquerda
    if numero.startswith('+'):
        numero = numero[1:]
        
    if len(numero) == 9 and numero.isdigit():
        numero = f"244{numero}"
        
    from django.apps import apps
    ConfigModel = apps.get_model('ARQUIVOS', 'ConfiguracaoSistema')
    
    phone_number_id = ConfigModel.get_valor('WHATSAPP_PHONE_NUMBER_ID', 
                                          getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', 
                                                  os.getenv('WHATSAPP_PHONE_NUMBER_ID', '101884902726142')))
    token = ConfigModel.get_valor('WHATSAPP_TOKEN', 
                                 getattr(settings, 'WHATSAPP_TOKEN', 
                                         os.getenv('WHATSAPP_TOKEN', 'EAARkkJz79Y0...'))) # Mantido o default longo que estava
    
    # URL customizada ou fallback para Meta v22.0
    default_url = f"https://graph.facebook.com/v22.0/{phone_number_id}/messages"
    url = ConfigModel.get_valor('WHATSAPP_API_URL', 
                               getattr(settings, 'WHATSAPP_API_URL', default_url))
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "template",
        "template": {
            "name": "hello_world",
            "language": {
                "code": "en_US"
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar WhatsApp para {numero}: {str(e)}")
        if hasattr(e, 'response') and getattr(e, 'response', None) is not None:
             logger.error(f"Detalhes: {e.response.text}")
        return False
