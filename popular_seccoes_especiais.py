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
            'Diretor de Gabinete do Administrador Municipal',
            'Secretário do Administrador Municipal'
        ],
        'Gabinete do Administrador Municipal Adjunto para a Área Técnica, Infra-estruturas e Serviços Comunitários': [
            'Administrador Municipal Adjunto para a Área Técnica',
            'Secretário do Administrador Municipal Adjunto'
        ],
        'Gabinete do Administrador Municipal Adjunto para a Área Política, Social e Económica': [
            'Administrador Municipal Adjunto para a Área Política e Social',
            'Secretário do Administrador Municipal Adjunto'
        ]
    }

    administracoes = Administracao.objects.all()
    total_admins = administracoes.count()
    print(f"Processando {total_admins} administrações...")

    count_dept = 0
    count_sec = 0

    for admin in administracoes:
        print(f".", end="", flush=True) # Progresso visual
        
        # O tipo E tem estrutura simplificada, mas geralmente tem Administrador.
        # Vamos assumir que TODOS têm Gabinete do Administrador.
        # Ajuste conforme necessidade: se Tipo E não tiver Adjuntos, podemos filtrar.
        
        # Filtrar Adjuntos para Tipo E? O decreto 270/24 define estruturas.
        # Tipo D e E geralmente têm menos adjuntos ou apenas 1.
        # Por segurança, vamos criar TODAS as estruturas para A, B, C, D.
        # E para E, talvez apenas o Administrador?
        # O requisito não especificou filtro por tipo, então vou aplicar a todos para garantir,
        # ou aplicar lógica baseada no tipo se for crítico.
        # Assumindo que todos têm pelo menos o Administrador.
        
        estruturas_a_criar = {}
        
        # Gabinete do Administrador (Para TODOS)
        estruturas_a_criar['Gabinete do Administrador Municipal'] = ESTRUTURA_ESPECIAL['Gabinete do Administrador Municipal']

        # Adjuntos (Apenas para A, B, C, D) - Simplificação
        if admin.tipo_municipio in ['A', 'B', 'C', 'D']:
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
