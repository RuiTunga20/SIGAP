"""
Script para criar Secções Especiais (Cargos como Secções) nos Gabinetes.
Conforme Manual de Configuração do SIGAP e Decreto Presidencial n.º 270/24.

Política Universal de Gabinete:
- Cada gabinete tem: Titular, Assessor, Director de Gabinete, Secretário(a)
- Director Adjunto de Gabinete apenas para Ministro e Governador
- A mesma estrutura aplica-se a MAT, Governos e Administrações
"""
import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SGA.settings')
django.setup()

from ARQUIVOS.models import Administracao, Departamento, Seccoes
from limpar_estrutura_obsoleta import limpar_estrutura


def popular_seccoes_especiais():
    limpar_estrutura()
    print("=" * 80)
    print("POPULANDO SECÇÕES ESPECIAIS (GABINETES E CARGOS)")
    print("Política Universal: Titular + Assessor + Dir. Gabinete + Secretário(a)")
    print("=" * 80)

    # =========================================================================
    # ESTRUTURA PARA ADMINISTRAÇÕES MUNICIPAIS (Tipos A, B, C)
    # 2 Adjuntos com áreas específicas
    # =========================================================================
    ESTRUTURA_2_ADJUNTOS = {
        'Gabinete do Administrador Municipal': [
            'Administrador Municipal',
            'Assessor do Administrador Municipal',
            'Director de Gabinete do Administrador Municipal',
            'Secretário do Administrador Municipal',
        ],
        'Gabinete do Administrador Municipal Adjunto para a Área Técnica, Infra-estruturas e Serviços Comunitários': [
            'Administrador Municipal Adjunto para a Área Técnica',
            'Assessor do Administrador Municipal Adjunto para a Área Técnica',
            'Director de Gabinete do Administrador Municipal Adjunto para a Área Técnica',
            'Secretário do Administrador Municipal Adjunto para a Área Técnica',
        ],
        'Gabinete do Administrador Municipal Adjunto para a Área Política, Social e Económica': [
            'Administrador Municipal Adjunto para a Área Política e Social',
            'Assessor do Administrador Municipal Adjunto para a Área Política e Social',
            'Director de Gabinete do Administrador Municipal Adjunto para a Área Política e Social',
            'Secretário do Administrador Municipal Adjunto para a Área Política e Social',
        ],
    }

    # =========================================================================
    # ESTRUTURA PARA TIPO D — 1 Adjunto (sem área específica)
    # =========================================================================
    ESTRUTURA_TIPO_D = {
        'Gabinete do Administrador Municipal': [
            'Administrador Municipal',
            'Assessor do Administrador Municipal',
            'Director de Gabinete do Administrador Municipal',
            'Secretário do Administrador Municipal',
        ],
        'Gabinete do Administrador Municipal Adjunto': [
            'Administrador Municipal Adjunto',
            'Assessor do Administrador Municipal Adjunto',
            'Director de Gabinete do Administrador Municipal Adjunto',
            'Secretário do Administrador Municipal Adjunto',
        ],
    }

    # =========================================================================
    # ESTRUTURA PARA TIPO E — 1 Adjunto (simplificada, sem Assessor no adj.)
    # =========================================================================
    ESTRUTURA_TIPO_E = {
        'Gabinete do Administrador Municipal': [
            'Administrador Municipal',
            'Assessor do Administrador Municipal',
            'Director de Gabinete do Administrador Municipal',
            'Secretário do Administrador Municipal',
        ],
        'Gabinete do Administrador Municipal Adjunto': [
            'Administrador Municipal Adjunto',
            'Secretário do Administrador Municipal Adjunto',
        ],
    }

    administracoes = Administracao.objects.exclude(tipo_municipio__in=['G', 'M'])
    total_admins = administracoes.count()
    print(f"Processando {total_admins} administrações municipais...")

    count_dept = 0
    count_sec = 0

    for admin in administracoes:
        print(f".", end="", flush=True)

        # Seleccionar estrutura conforme tipo
        if admin.tipo_municipio == 'E':
            estruturas_a_criar = ESTRUTURA_TIPO_E
        elif admin.tipo_municipio == 'D':
            estruturas_a_criar = ESTRUTURA_TIPO_D
        else:
            # Tipos A, B, C — 2 adjuntos com áreas
            estruturas_a_criar = ESTRUTURA_2_ADJUNTOS

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

    print(f"\n\n{'=' * 80}")
    print(f"CONCLUÍDO!")
    print(f"Departamentos (Gabinetes) Criados: {count_dept}")
    print(f"Secções (Cargos) Criadas:          {count_sec}")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    popular_seccoes_especiais()
