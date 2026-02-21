
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SGA.settings')
django.setup()

from ARQUIVOS.models import Documento, TipoDocumento, Administracao, Departamento, StatusDocumento
from ARQUIVOS.formularios import DocumentoForm
from django.contrib.auth import get_user_model

User = get_user_model()

def reproduce():
    # 1. Get or create a user with administration/department
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        print("No user found.")
        return

    admin = user.administracao
    dept = user.departamento_efetivo
    
    if not admin or not dept:
        print(f"User {user.username} missing admin ({admin}) or dept ({dept})")
        return

    # 2. Get a TipoDocumento
    tipo = TipoDocumento.objects.filter(ativo=True).first()
    if not tipo:
        print("No TipoDocumento found.")
        return

    # 3. Simulate form data (matches the fields in DocumentoForm)
    # fields = ['titulo', 'tipo_documento', 'prioridade', 'arquivo', 'arquivo_digitalizado', 'tags', 'observacoes', 'utente', 'telefone', 'email', 'origem', 'niveis', 'referencia']
    form_data = {
        'titulo': 'Teste Reversao',
        'conteudo': 'Conteudo restaurado aqui',
        'tipo_documento': tipo.id,
        'prioridade': 'normal',
        'utente': 'Joao Reversao',
        'telefone': '923456789',
        'email': 'joao@teste.com',
        'origem': 'Pessoa Singular',
        'niveis': 'Público',
        'referencia': 'REF-001'
    }

    form = DocumentoForm(data=form_data)
    
    print("Form is valid?", form.is_valid())
    if not form.is_valid():
        print("Form errors:", form.errors.as_json())
        return

    try:
        documento = form.save(commit=False)
        documento.criado_por = user
        documento.departamento_origem = dept
        documento.departamento_atual = dept
        documento.administracao = admin
        documento.responsavel_atual = user
        
        documento.save()
        print(f"Document registered successfully! ID: {documento.id}, Protocolo: {documento.numero_protocolo}")
    except Exception as e:
        print(f"Failed to save document: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reproduce()
