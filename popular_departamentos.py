"""
Script para popular os Departamentos e Secções das 326 Administrações
conforme o Decreto Presidencial n.º 270/24 de 29 de novembro.

Estrutura Orgânica:
- Tipo A: 18 direcções/gabinetes com secções
- Tipo B: 17 direcções/gabinetes com secções
- Tipo C: 15 direcções/gabinetes com secções
- Tipo D: 14 direcções/gabinetes com secções
- Tipo E: 8 direcções/gabinetes (sem secções - estrutura simplificada)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SGA.settings')
django.setup()

from ARQUIVOS.models import Administracao, Departamento, Seccoes
from limpar_estrutura_obsoleta import limpar_estrutura

# =============================================================================
# ESTRUTURAS ORGÂNICAS POR TIPO DE MUNICÍPIO
# =============================================================================

# Estrutura comum a todos os tipos (A, B, C, D)
ESTRUTURA_COMUM = {
    'Secretaria Geral': [
        'Secção de Orçamento, Finanças e Contratação Pública',
        'Secção de Património, Logística e Protocolo',
        'Secção de Expediente',
    ],
    'Gabinete de Estudos, Planeamento e Estatística': [
        'Secção de Estudos e Estatística',
        'Secção de Planeamento',
        'Secção de Monitorização e Controlo',
    ],
    'Gabinete de Recursos Humanos': [
        'Secção de Gestão Administrativa',
        'Secção de Gestão de Carreiras e Capacitação Técnica',
    ],
    'Gabinete de Comunicação Social': [
        'Secção de Comunicação Institucional e Imprensa',
        'Secção para Documentação e Informação',
    ],
    'Gabinete Jurídico e Apoio às Comissões de Moradores': [
        'Secção dos Assuntos Jurídicos, Contencioso e Intercâmbio',
        'Secção de Acompanhamento e Apoio às Comissões de Moradores',
    ],
    'Direcção Municipal da Educação': [
        'Secção de Educação e Ensino',
        'Secção de Planeamento, Estatística e Recursos Humanos',
        'Secção de Inspecção e Supervisão Pedagógica',
        'Secção de Ciência, Tecnologia e Inovação',
    ],
    'Direcção Municipal da Saúde': [
        'Secção de Logística Hospitalar e Depósito de Medicamentos',
        'Secção de Estatística, Planeamento e Recursos Humanos',
        'Secção de Saúde Pública',
        'Secção de Inspecção de Saúde',
    ],
    'Direcção Municipal de Promoção do Desenvolvimento Económico Integrado': [
        'Secção de Promoção do Desenvolvimento Económico Integrado',
        'Secção de Licenciamento das Actividades Económicas e Serviços',
    ],
    'Direcção Municipal da Fiscalização e Inspecção das Actividades Económicas e Segurança Alimentar': [
        'Secção Municipal de Fiscalização',
        'Secção Municipal de Inspecção das Actividades Económicas e Segurança Alimentar',
    ],
}

# =============================================================================
# TIPO A - 18 direcções/gabinetes
# =============================================================================
ESTRUTURA_TIPO_A = {
    **ESTRUTURA_COMUM,
    'Direcção Municipal do Turismo e Cultura': [
        'Secção do Turismo',
        'Secção de Promoção da Cultura',
    ],
    'Direcção Municipal de Tempos Livres, Juventude e Desportos': [
        'Secção de Tempos Livres',
        'Secção de Juventude e Desportos',
    ],
    'Direcção Municipal da Acção Social, Família e Igualdade de Género': [
        'Secção de Acção Social',
        'Secção de Família e Igualdade do Género',
    ],
    'Direcção Municipal de Infra-estruturas, Ordenamento do Território e Habitação': [
        'Secção do Ordenamento do Território',
        'Secção de Habitação',
        'Secção de Infra-estruturas',
    ],
    'Direcção Municipal do Ambiente e Saneamento Básico': [
        'Secção do Ambiente',
        'Secção do Saneamento Básico',
    ],
    'Direcção Municipal de Transportes, Tráfego e Mobilidade': [
        'Secção de Transportes',
        'Secção de Tráfego e Mobilidade',
    ],
    'Direcção Municipal de Energias e Águas': [
        'Secção de Serviços Municipalizados de Energia',
        'Secção de Serviços Municipalizados das Águas',
    ],
    'Direcção Municipal de Agricultura, Pecuária e Pescas': [
        'Secção de Agricultura',
        'Secção de Pecuária e Pescas',
    ],
    'Direcção Municipal dos Registos e Modernização Administrativa': [
        'Secção de Administração Pública e Trabalho',
        'Secção de Registo Eleitoral, Recenseamento Militar e Organização do Território',
        'Secção de Modernização Administrativa e Gestão do BUAP',
    ],
}

# =============================================================================
# TIPO B - 17 direcções/gabinetes
# =============================================================================
ESTRUTURA_TIPO_B = {
    **ESTRUTURA_COMUM,
    'Direcção Municipal do Turismo, Cultura, Tempos Livres, Juventude e Desportos': [
        'Secção do Turismo',
        'Secção de Promoção da Cultura',
        'Secção de Tempos Livres, Juventude e Desportos',
    ],
    'Direcção Municipal da Acção Social, Família e Igualdade de Género': [
        'Secção de Acção Social',
        'Secção de Família e Igualdade do Género',
    ],
    'Direcção Municipal de Infra-estruturas, Ordenamento do Território e Habitação': [
        'Secção do Ordenamento do Território',
        'Secção de Habitação',
        'Secção de Infra-estruturas',
    ],
    'Direcção Municipal do Ambiente e Saneamento Básico': [
        'Secção do Ambiente',
        'Secção do Saneamento Básico',
    ],
    'Direcção Municipal de Transportes, Tráfego e Mobilidade': [
        'Secção de Transportes',
        'Secção de Tráfego e Mobilidade',
    ],
    'Direcção Municipal de Energias e Águas': [
        'Secção de Serviços Municipalizados de Energia',
        'Secção de Serviços Municipalizados das Águas',
    ],
    'Direcção Municipal de Agricultura, Pecuária e Pescas': [
        'Secção de Agricultura',
        'Secção de Pecuária e Pescas',
    ],
    'Direcção Municipal dos Registos e Modernização Administrativa': [
        'Secção de Administração Pública e Trabalho',
        'Secção de Registo Eleitoral, Recenseamento Militar e Organização do Território',
        'Secção de Modernização Administrativa e Gestão do BUAP',
    ],
}

# =============================================================================
# TIPO C - 15 direcções/gabinetes
# =============================================================================
ESTRUTURA_TIPO_C = {
    **ESTRUTURA_COMUM,
    'Direcção Municipal da Acção Social, Turismo, Cultura, Juventude e Desportos': [
        'Secção de Promoção do Turismo e Cultura',
        'Secção de Juventude e Desportos',
        'Secção de Acção Social',
    ],
    'Direcção Municipal de Infra-estruturas, Ordenamento do Território, Habitação, Ambiente e Saneamento Básico': [
        'Secção do Ordenamento do Território e Habitação',
        'Secção de Infra-estruturas',
        'Secção do Ambiente e Saneamento Básico',
    ],
    'Direcção Municipal de Transportes, Tráfego e Mobilidade': [
        'Secção de Transportes',
        'Secção de Tráfego e Mobilidade',
    ],
    'Direcção Municipal de Energias e Águas': [
        'Secção de Serviços Municipalizados de Energia',
        'Secção de Serviços Municipalizados das Águas',
    ],
    'Direcção Municipal de Agricultura, Pecuária e Pescas': [
        'Secção de Agricultura',
        'Secção de Pecuária e Pescas',
    ],
    'Direcção Municipal dos Registos e Modernização Administrativa': [
        'Secção de Administração Pública e Trabalho',
        'Secção de Registo Eleitoral, Recenseamento Militar e Organização do Território',
        'Secção de Modernização Administrativa e Gestão do BUAP',
    ],
}

# =============================================================================
# TIPO D - 14 direcções/gabinetes
# =============================================================================
ESTRUTURA_TIPO_D = {
    **ESTRUTURA_COMUM,
    'Direcção Municipal da Acção Social, Turismo, Cultura, Juventude e Desportos': [
        'Secção de Promoção do Turismo e Cultura',
        'Secção de Juventude e Desportos',
        'Secção de Acção Social',
    ],
    'Direcção Municipal de Infra-estruturas, Transporte, Equipamento Urbano, Ambiente e Saneamento': [
        'Secção de Infra-estruturas e Equipamento Urbano',
        'Secção de Transportes',
        'Secção do Ambiente e Saneamento',
    ],
    'Direcção Municipal de Energias e Águas': [
        'Secção de Serviços Municipalizados de Energia',
        'Secção de Serviços Municipalizados das Águas',
    ],
    'Direcção Municipal de Agricultura, Pecuária e Pescas': [
        'Secção de Agricultura',
        'Secção de Pecuária e Pescas',
    ],
    'Direcção Municipal dos Registos e Modernização Administrativa': [
        'Secção de Administração Pública e Trabalho',
        'Secção de Registo Eleitoral, Recenseamento Militar e Organização do Território',
        'Secção de Modernização Administrativa e Gestão do BUAP',
    ],
}

# =============================================================================
# TIPO E - 8 direcções/gabinetes (SEM SECÇÕES - estrutura simplificada)
# =============================================================================
ESTRUTURA_TIPO_E = {
    'Secretaria Geral': [],
    'Gabinete Jurídico e Apoio às Comissões de Moradores': [],
    'Direcção Municipal da Educação': [],
    'Direcção Municipal da Saúde': [],
    'Direcção Municipal de Promoção do Desenvolvimento Económico Integrado': [],
    'Direcção Municipal da Fiscalização e Inspecção das Actividades Económicas e Segurança Alimentar': [],
    'Direcção Municipal da Acção Social, Turismo, Cultura, Juventude e Desportos': [],
    'Direcção Municipal de Infra-estruturas e Serviços Técnicos': [],
}

# Mapear tipo para estrutura
ESTRUTURAS_POR_TIPO = {
    'A': ESTRUTURA_TIPO_A,
    'B': ESTRUTURA_TIPO_B,
    'C': ESTRUTURA_TIPO_C,
    'D': ESTRUTURA_TIPO_D,
    'E': ESTRUTURA_TIPO_E,
}


def popular_departamentos_seccoes():
    """
    Popula os departamentos e secções para todas as administrações
    conforme seu tipo de estrutura orgânica.
    """
    limpar_estrutura()
    total_departamentos = 0
    total_seccoes = 0
    total_admin = 0
    
    estatisticas_por_tipo = {
        'A': {'admin': 0, 'dept': 0, 'sec': 0},
        'B': {'admin': 0, 'dept': 0, 'sec': 0},
        'C': {'admin': 0, 'dept': 0, 'sec': 0},
        'D': {'admin': 0, 'dept': 0, 'sec': 0},
        'E': {'admin': 0, 'dept': 0, 'sec': 0},
    }
    
    # Buscar todas as administrações
    administracoes = Administracao.objects.all().order_by('tipo_municipio', 'nome')
    
    print(f"\n📊 Encontradas {administracoes.count()} administrações para processar...\n")
    
    for admin in administracoes:
        tipo = admin.tipo_municipio
        estrutura = ESTRUTURAS_POR_TIPO.get(tipo, {})
        
        if not estrutura:
            print(f"[!] Tipo desconhecido: {tipo} para {admin.nome}")
            continue
        
        print(f"\n{'='*60}")
        print(f"🏛️  {admin.nome} ({admin.provincia}) - Tipo {tipo}")
        print(f"{'='*60}")
        
        estatisticas_por_tipo[tipo]['admin'] += 1
        total_admin += 1
        
        dept_count = 0
        sec_count = 0
        
        for dept_nome, seccoes in estrutura.items():
            # Criar ou obter departamento
            departamento, dept_created = Departamento.objects.get_or_create(
                nome=dept_nome,
                administracao=admin,
                defaults={
                    'tipo_municipio': tipo,
                    'ativo': True,
                }
            )
            
            if dept_created:
                dept_count += 1
                total_departamentos += 1
                estatisticas_por_tipo[tipo]['dept'] += 1
                print(f"  [+] Criado: {dept_nome}")
            else:
                print(f"  [=] Existe:  {dept_nome}")
            
            # Criar secções do departamento
            for sec_nome in seccoes:
                seccao, sec_created = Seccoes.objects.get_or_create(
                    nome=sec_nome,
                    departamento=departamento,
                    defaults={
                        'ativo': True,
                    }
                )
                
                if sec_created:
                    sec_count += 1
                    total_seccoes += 1
                    estatisticas_por_tipo[tipo]['sec'] += 1
                    print(f"      [+] Secção: {sec_nome}")
        
        print(f"\n  📌 Resumo: {dept_count} dept. criados, {sec_count} secções criadas")
    
    # Resumo final
    print(f"\n\n{'='*70}")
    print(f"RESUMO FINAL - Decreto Presidencial n.º 270/24")
    print(f"{'='*70}")
    print(f"\n📊 Estatísticas por Tipo de Município:\n")
    print(f"{'Tipo':<8} {'Admins':<12} {'Direções':<12} {'Secções':<12}")
    print(f"{'-'*44}")
    
    for tipo in ['A', 'B', 'C', 'D', 'E']:
        stats = estatisticas_por_tipo[tipo]
        print(f"Tipo {tipo:<4} {stats['admin']:<12} {stats['dept']:<12} {stats['sec']:<12}")
    
    print(f"{'-'*44}")
    print(f"{'TOTAL':<8} {total_admin:<12} {total_departamentos:<12} {total_seccoes:<12}")
    print(f"{'='*70}")
    
    return total_admin, total_departamentos, total_seccoes


if __name__ == '__main__':
    print("="*70)
    print("POPULAR DEPARTAMENTOS E SECÇÕES")
    print("Decreto Presidencial n.º 270/24 de 29 de novembro")
    print("="*70)
    
    admin, dept, sec = popular_departamentos_seccoes()
    
    print(f"\n✅ Concluído!")
    print(f"   {admin} administrações processadas")
    print(f"   {dept} direcções criadas")
    print(f"   {sec} secções criadas")
