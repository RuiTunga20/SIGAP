"""
Script para criar Secções Especiais (Cargos como Secções) nos Gabinetes.
Conforme solicitação para Hierarquia Estrita e Sigilo.
"""
import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SGA.settings')
django.setup()

from ARQUIVOS.models import Administracao, Departamento, Seccoes

def popular_seccoes_especiais():
    print("="*80)
    print("POPULANDO SECÇÕES ESPECIAIS (GABINETES E ASSESSORES)")
    print("="*80)

    # Definição das Estruturas Especiais
    ESTRUTURA_ESPECIAL = {
        'Gabinete do Administrador Municipal': [
            'Administrador Municipal',
            'Assessor do Administrador Municipal',
            'Director de Gabinete do Administrador Municipal',
            'Secretário do Administrador Municipal'
        ],
        'Gabinete do Administrador Municipal Adjunto para a Área Técnica, Infra-estruturas e Serviços Comunitários': [
            'Administrador Municipal Adjunto para a Área Técnica',
            'Director de Gabinete do Administrador Municipal Adjunto',
            'Secretário do Administrador Municipal Adjunto'
        ],
        'Gabinete do Administrador Municipal Adjunto para a Área Política, Social e Económica': [
            'Administrador Municipal Adjunto para a Área Política e Social',
            'Director de Gabinete do Administrador Municipal Adjunto',
            'Secretário do Administrador Municipal Adjunto'
        ]
    }

    # Estrutura Simplificada para Administrações Tipo E
    ESTRUTURA_TIPO_E = {
        'Gabinete do Administrador Municipal': [
            'Administrador Municipal',
            'Secretário do Administrador Municipal'
        ]
    }

    administracoes = Administracao.objects.all()
    total_admins = administracoes.count()
    print(f"Processando {total_admins} administrações...")

    count_dept = 0
    count_sec = 0

    for admin in administracoes:
        print(f".", end="", flush=True) # Progresso visual
        
        estruturas_a_criar = {}
        
        if admin.tipo_municipio == 'E':
            # Tipo E tem estrutura simplificada
            estruturas_a_criar = ESTRUTURA_TIPO_E
        else:
            # Gabinete do Administrador (Para A, B, C, D)
            estruturas_a_criar['Gabinete do Administrador Municipal'] = ESTRUTURA_ESPECIAL['Gabinete do Administrador Municipal']

            # Adjuntos (Para A, B, C, D)
            estruturas_a_criar.update({k:v for k,v in ESTRUTURA_ESPECIAL.items() if k != 'Gabinete do Administrador Municipal'})

        for dept_nome, seccoes_nomes in estruturas_a_criar.items():
            # 1. Criar/Obter Departamento (Gabinete)
            dept, created_dept = Departamento.objects.get_or_create(
                nome=dept_nome,
                administracao=admin,
                defaults={
                    'tipo_municipio': admin.tipo_municipio,
                    'ativo': True
                }
            )
            if created_dept:
                count_dept += 1
            
            # 2. Criar Secções (Cargos)
            for sec_nome in seccoes_nomes:
                sec, created_sec = Seccoes.objects.get_or_create(
                    nome=sec_nome,
                    departamento=dept,
                    defaults={
                        'ativo': True
                    }
                )
                if created_sec:
                    count_sec += 1

    print(f"\n\n{'='*80}")
    print(f"CONCLUÍDO!")
    print(f"Departamentos (Gabinetes) Criados: {count_dept}")
    print(f"Secções (Cargos) Criadas:        {count_sec}")
    print(f"{'='*80}")

if __name__ == "__main__":
    popular_seccoes_especiais()
