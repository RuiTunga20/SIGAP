import os
import django
import sys

# Setup Django environment
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SGA.settings')
django.setup()

from ARQUIVOS.models import Administracao, Departamento, Seccoes
from limpar_estrutura_obsoleta import limpar_estrutura

# Definição da Estrutura
ESTRUTURA_GOVERNO = {
    "Gabinete do Governador Provincial": [
        "Governador Provincial",
        "Assessor do Governador",
        "Director de Gabinete do Governador",
        "Director Adjunto de Gabinete do Governador",
        "Secretário(a) do Governador"
    ],
    "Gabinete do Vice-Governador para o Sector Político, Social e Económico": [
        "Vice-Governador",
        "Assessor Vice-Governador para o Sector Político, Social e Económico",
        "Director de Gabinete do Vice-Governador para o Sector Político, Social e Económico",
        "Secretário(a) do Vice-Governador para o Sector Político, Social e Económico"
    ],
    "Gabinete do Vice-Governador para os Serviços Técnicos e Infra-estruturas": [
        "Vice-Governador",
        "Assessor do Vice-Governador para os Serviços Técnicos e Infra-estruturas",
        "Director do Gabinete do Vice-Governador para os Serviços Técnicos e Infra-estruturas",
        "Secretário(a) do Vice-Governador para os Serviços Técnicos e Infra-estruturas"
    ],
    "Secretaria Geral": [
        "Departamento de Gestão do Orçamento e Contabilidade",
        "Departamento de Logística e Património",
        "Departamento de Relações Públicas e Protocolo",
        "Departamento da Contratação Pública"
    ],
    "Gabinete Jurídico e de Intercâmbio": [
        "Departamento de Assessoria Jurídica e Contencioso",
        "Departamento de Intercâmbio"
    ],
    "Gabinete de Recursos Humanos": [
        "Departamento de Gestão Administrativa",
        "Departamento de Gestão de Carreiras e Capacitação Técnica"
    ],
    "Gabinete de Comunicação Social": [
        "Departamento de Comunicação Social",
        "Departamento de Comunicação Institucional e Imprensa"
    ],
    "Gabinete Provincial de Estudos, Planeamento e Estatística": [
        "Departamento de Estudos e Estatística",
        "Departamento de Planeamento",
        "Departamento de Monitorização e Controlo",
        "Departamento de Apoio Técnico aos Municípios"
    ],
    "Gabinete Provincial da Educação": [
        "Departamento de Educação e Ensino",
        "Departamento de Planeamento, Estatística e Recursos Humanos",
        "Departamento de Inspecção e Supervisão Pedagógica",
        "Departamento de Ciência, Tecnologia e Inovação"
    ],
    "Gabinete Provincial da Saúde": [
        "Departamento de Logística Hospitalar",
        "Departamento de Estatística, Planeamento e Recursos Humanos",
        "Departamento de Saúde Pública",
        "Departamento de Inspecção de Saúde"
    ],
    "Gabinete Provincial para Desenvolvimento Económico Integrado": [
        "Departamento de Promoção do Emprego e Fomento ao Empreendedorismo",
        "Departamento de Indústria",
        "Departamento de Comércio",
        "Departamento de Recursos Minerais"
    ],
    "Gabinete Provincial da Cultura e Turismo": [
        "Departamento do Turismo",
        "Departamento de Cultura, Património Histórico e Comunidades Tradicionais"
    ],
    "Gabinete Provincial da Juventude e Desportos": [
        "Departamento da Juventude",
        "Departamento dos Desportos"
    ],
    "Gabinete Provincial da Acção Social, Família e Igualdade de Género": [
        "Departamento de Acção Social",
        "Departamento da Família e Igualdade do Género"
    ],
    "Gabinete Provincial de Infra-estruturas e Serviços Técnicos": [
        "Departamento de Infra-estruturas Urbanas",
        "Departamento de Gestão Urbanística",
        "Departamento de Obras Públicas",
        "Departamento de Promoção, Reabilitação e Gestão Imobiliária"
    ],
    "Gabinete Provincial de Ambiente, Gestão de Resíduos e Serviços Comunitários": [
        "Departamento do Ambiente",
        "Departamento de Gestão de Resíduos",
        "Departamento de Serviços Comunitários"
    ],
    "Gabinete Provincial de Transportes, Tráfego e Mobilidade Urbana": [
        "Departamento de Transportes",
        "Departamento de Tráfego e Mobilidade"
    ],
    "Gabinete Provincial da Agricultura, Pecuária e Pescas": [
        "Departamento de Agricultura, Pecuária e Flora",
        "Departamento de Pescas e Aquicultura",
        "Departamento de Vigilância Epidemiológica, Animal e Vegetal"
    ],
    "Gabinete Provincial dos Registos e Modernização Administrativa": [
        "Departamento de Tecnologia de Informação e Comunicação",
        "Departamento de Registo Eleitoral Oficioso e Recenseamento Militar",
        "Departamento de Modernização Administrativa e Gestão do Balcão Único de Atendimento ao Público (BUAP)"
    ]
}

def popular_governos():
    limpar_estrutura()
    print("Iniciando população dos Governos Provinciais...")
    
    # Lista Oficial das Províncias de Angola (Nova Divisão)
    PROVINCIAS = [
        "Bengo", "Benguela", "Bié", "Cabinda", "Cuando", "Cubango",
        "Cuanza Norte", "Cuanza Sul", "Cunene", "Huambo", "Huíla", 
        "Ícolo e Bengo", "Luanda", "Lunda Norte", "Lunda Sul", 
        "Malanje", "Moxico", "Moxico Leste", "Namibe", "Uíge", "Zaire"
    ]
    
    for provincia_nome in PROVINCIAS:
        # Lógica de preposição para o nome do Governo
        prefixo = "de"
        if provincia_nome in ["Uíge", "Bié", "Zaire", "Moxico", "Bengo", "Huambo", "Namibe", "Cuando", "Cubango"]: 
             prefixo = "do"
        elif provincia_nome in ["Huíla", "Lunda Norte", "Lunda Sul", "Benguela", "Cabinda", "Moxico Leste"]:
             prefixo = "da"
        elif provincia_nome == "Ícolo e Bengo":
             prefixo = "do"
             
        nome_governo = f"Governo Provincial {prefixo} {provincia_nome}"
        
        print(f"Processando: {nome_governo}")
        
        # Criar ou Obter a Administração do Governo
        governo, created = Administracao.objects.get_or_create(
            nome=nome_governo,
            defaults={
                'tipo_municipio': 'G', # Novo tipo
                'provincia': provincia_nome
            }
        )
        
        if created:
            print(f"  > Criado novo Governo: {nome_governo}")
        else:
            print(f"  > Governo já existente: {nome_governo}")
            
        # Criar Estrutura Interna (Gabinetes e Departamentos)
        for gabinete_nome, sub_departamentos in ESTRUTURA_GOVERNO.items():
            # Criar o Gabinete (que é um Departamento no nosso sistema)
            gabinete, dept_created = Departamento.objects.get_or_create(
                nome=gabinete_nome,
                administracao=governo,
                defaults={
                    'tipo_municipio': 'G',
                    'descricao': f'{gabinete_nome} do {nome_governo}'
                }
            )
            
            if dept_created:
                print(f"    + Gabinete criado: {gabinete_nome}")
            
            # Criar os Sub-departamentos (que são Secções no nosso sistema)
            for sub_nome in sub_departamentos:
                seccao, sec_created = Seccoes.objects.get_or_create(
                    nome=sub_nome,
                    departamento=gabinete,
                    defaults={
                        'descricao': sub_nome
                    }
                )
                if sec_created:
                    print(f"      - Dept/Secção criado: {sub_nome}")

if __name__ == '__main__':
    popular_governos()
