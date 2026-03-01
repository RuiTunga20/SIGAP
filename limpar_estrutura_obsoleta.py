"""
Script para limpar estruturas obsoletas conforme Manual de Configuração do SIGAP.

Remove departamentos e secções que já não fazem parte da estrutura orgânica:
- Remoções globais: Corpo de Assessores, Secção de Expediente e Protocolo, Secção de Secretariado
- Remoções por tipo: Repartições, Secretariado e Apoio Geral, etc.

ATENÇÃO: Este script faz DELETE no banco de dados. Executar apenas após confirmação.
"""
import os
import django
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SGA.settings')
django.setup()

from ARQUIVOS.models import Administracao, Departamento, Seccoes


def limpar_estrutura():
    print("=" * 80)
    print("LIMPEZA DE ESTRUTURA OBSOLETA")
    print("=" * 80)

    total_sec_removidas = 0
    total_dept_removidos = 0

    # =========================================================================
    # 1. REMOÇÕES GLOBAIS (Todos os gabinetes — MAT, Governo, Administração)
    # =========================================================================
    print("\n--- 1. Remoções Globais (Secções obsoletas em gabinetes) ---")

    SECCOES_GLOBAIS_A_REMOVER = [
        'Corpo de Assessores',
        'Secção de Expediente e Protocolo',
        'Secção de Secretariado',
    ]

    for nome in SECCOES_GLOBAIS_A_REMOVER:
        qs = Seccoes.objects.filter(nome__iexact=nome)
        count = qs.count()
        if count > 0:
            qs.delete()
            total_sec_removidas += count
            print(f"  [x] Removidas {count} ocorrências de: {nome}")
        else:
            print(f"  [=] Nenhuma encontrada: {nome}")

    # =========================================================================
    # 2. REMOÇÕES POR TIPO DE ADMINISTRAÇÃO
    # =========================================================================

    # --- TIPO E ---
    print("\n--- 2a. Remoções Tipo E ---")
    DEPT_TIPO_E = [
        'Repartição de Administração e Serviços Gerais',
        'Repartição de Serviços Sociais e Económicos',
        'Repartição de Serviços Técnicos, Infra-estruturas e Agricultura',
    ]
    admins_e = Administracao.objects.filter(tipo_municipio='E')
    for nome in DEPT_TIPO_E:
        qs = Departamento.objects.filter(nome__iexact=nome, administracao__in=admins_e)
        count = qs.count()
        if count > 0:
            qs.delete()
            total_dept_removidos += count
            print(f"  [x] Removidos {count} departamentos: {nome}")
        else:
            print(f"  [=] Nenhum encontrado: {nome}")

    # --- TIPO D ---
    print("\n--- 2b. Remoções Tipo D ---")
    DEPT_TIPO_D = [
        'Secretariado e Apoio Geral',
        'Repartição de Administração e Serviços Gerais',
        'Repartição de Serviços Sociais e Económicos',
        'Repartição de Serviços Técnicos e Agricultura',
    ]
    admins_d = Administracao.objects.filter(tipo_municipio='D')
    for nome in DEPT_TIPO_D:
        qs = Departamento.objects.filter(nome__iexact=nome, administracao__in=admins_d)
        count = qs.count()
        if count > 0:
            qs.delete()
            total_dept_removidos += count
            print(f"  [x] Removidos {count} departamentos: {nome}")
        else:
            print(f"  [=] Nenhum encontrado: {nome}")

    # --- TIPOS C e B ---
    print("\n--- 2c. Remoções Tipos C e B ---")
    DEPT_TIPO_CB = [
        'Secção de Secretariado e Apoio Técnico',
        'Secretaria Municipal',
        'Repartição de Planeamento e Serviços Sociais',
        'Repartição de Serviços Técnicos e Agricultura',
    ]
    admins_cb = Administracao.objects.filter(tipo_municipio__in=['C', 'B'])

    for nome in DEPT_TIPO_CB:
        # Tentar como departamento
        qs_dept = Departamento.objects.filter(nome__iexact=nome, administracao__in=admins_cb)
        count_dept = qs_dept.count()
        if count_dept > 0:
            qs_dept.delete()
            total_dept_removidos += count_dept
            print(f"  [x] Removidos {count_dept} departamentos: {nome}")

        # Tentar como secção
        qs_sec = Seccoes.objects.filter(
            nome__iexact=nome,
            departamento__administracao__in=admins_cb
        )
        count_sec = qs_sec.count()
        if count_sec > 0:
            qs_sec.delete()
            total_sec_removidas += count_sec
            print(f"  [x] Removidas {count_sec} secções: {nome}")

        if count_dept == 0 and count_sec == 0:
            print(f"  [=] Nenhum encontrado: {nome}")

    # Remover "Gabinete do Adm. Adjunto" genérico em C e B
    # (manter os 2 adjuntos específicos com áreas)
    print("\n--- 2d. Remover Gabinete Adjunto genérico em C e B ---")
    qs_adj_generico = Departamento.objects.filter(
        nome='Administrador Municipal Adjunto',
        administracao__in=admins_cb
    )
    count_adj = qs_adj_generico.count()
    if count_adj > 0:
        qs_adj_generico.delete()
        total_dept_removidos += count_adj
        print(f"  [x] Removidos {count_adj} 'Administrador Municipal Adjunto' genéricos")
    else:
        print(f"  [=] Nenhum 'Administrador Municipal Adjunto' genérico encontrado em C/B")

    # =========================================================================
    # RESUMO
    # =========================================================================
    print(f"\n{'=' * 80}")
    print(f"LIMPEZA CONCLUÍDA!")
    print(f"  Departamentos removidos: {total_dept_removidos}")
    print(f"  Secções removidas:       {total_sec_removidas}")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    limpar_estrutura()
