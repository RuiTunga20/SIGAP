import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SGA.settings')
django.setup()

from ARQUIVOS.models import Administracao, Departamento, CustomUser

def create_super_mat():
    print("--- INICIANDO CRIAÇÃO DO SUPER-UTILIZADOR MAT ---")
    
    try:
        # 1. Localizar o Ministério (MAT)
        mat = Administracao.objects.filter(tipo_municipio='M').first()
        if not mat:
            print("[ERRO] MinistériO (MAT) não encontrado no sistema.")
            return

        # 2. Localizar o Departamento Principal (Secretaria Geral)
        dept = Departamento.objects.filter(administracao=mat, nome__icontains="Secretaria").first()
        if not dept:
            # Pega o primeiro departamento disponível no MAT se não achar por nome
            dept = Departamento.objects.filter(administracao=mat).first()
            
        if not dept:
            print("[ERRO] Nenhum departamento encontrado para o MAT.")
            return

        # 3. Criar ou Atualizar o Usuário 'mat'
        username = 'mat'
        email = 'mat@min-mat.gov.ao'
        password = 'MatUser123!' # Senha padrão inicial (pode ser alterada)

        user, created = CustomUser.objects.get_or_create(username=username)
        
        user.email = email
        user.administracao = mat
        user.departamento = dept
        user.nivel_acesso = 'admin_sistema'
        user.is_staff = True
        user.is_superuser = True
        
        if created:
            user.set_password(password)
            print(f"[SUCESSO] Usuário '{username}' CRIADO com permissões totais.")
        else:
            # Se já existir, garantimos que ele tenha as permissões
            print(f"[INFO] Usuário '{username}' já existia. ATUALIZANDO permissões...")
        
        user.save()
        print(f"  - Admin: {mat.nome}")
        print(f"  - Dept: {dept.nome}")
        print(f"  - Nível: {user.get_nivel_acesso_display()}")
        print(f"  - Superuser: {user.is_superuser}")
        
    except Exception as e:
        print(f"[ERRO CRÍTICO] Falha ao processar: {e}")

if __name__ == "__main__":
    create_super_mat()
