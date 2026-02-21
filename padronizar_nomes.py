"""
Script de Migração de Dados - Padronização Decreto 270/24 (Versão Final Corrigida)
Unifica nomes de secções antigas e mescla duplicatas.
"""
import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SGA.settings')
django.setup()

from ARQUIVOS.models import Seccoes, CustomUser, Documento, MovimentacaoDocumento
from django.db import transaction

def mesclar_seccao(seccao_antiga, seccao_nova):
    """Move todos os registros da antiga para a nova e remove a antiga."""
    print(f"    [Merging] '{seccao_antiga.id}:{seccao_antiga.nome}' -> '{seccao_nova.id}:{seccao_nova.nome}' no depto {seccao_nova.departamento_id}")
    
    # 1. Usuários
    users_moved = CustomUser.objects.filter(seccao=seccao_antiga).update(seccao=seccao_nova)
    
    # 2. Documentos (como localização atual)
    docs_moved = Documento.objects.filter(seccao_atual=seccao_antiga).update(seccao_atual=seccao_nova)
    
    # 3. Movimentações (origem e destino)
    mov_dest_moved = MovimentacaoDocumento.objects.filter(seccao_destino=seccao_antiga).update(seccao_destino=seccao_nova)
    mov_orig_moved = MovimentacaoDocumento.objects.filter(seccao_origem=seccao_antiga).update(seccao_origem=seccao_nova)
    
    # 4. Remover a antiga
    seccao_antiga.delete()
    
    return users_moved, docs_moved

def padronizar_seccoes():
    # Ordem importa: as variantes mais específicas primeiro
    MAPEAMENTO = {
        'Secção de Orçamento, Finanças e Contratação Pública': 'Secção de Orçamento, Finanças e Contratação Pública', # No-op para garantir existência
        'Secção de Orçamento e Finanças': 'Secção de Orçamento, Finanças e Contratação Pública',
        'Secção de Orçamento e Finança': 'Secção de Orçamento, Finanças e Contratação Pública',
        'Secção de Património e Logística': 'Secção de Património, Logística e Protocolo',
        'Secção de Expediente Geral': 'Secção de Expediente',
    }

    print("--- INICIANDO PADRONIZAÇÃO FINAL (DECRETO 270/24) ---")
    
    total_corrigidos = 0
    total_mesclados = 0

    with transaction.atomic():
        for nome_antigo, nome_novo in MAPEAMENTO.items():
            if nome_antigo == nome_novo: continue
            
            print(f"\n[*] Analisando variantes de '{nome_antigo}'...")
            seccoes_antigas = list(Seccoes.objects.filter(nome__iexact=nome_antigo))
            
            for s_antiga in seccoes_antigas:
                depto = s_antiga.departamento
                
                # Verifica se já existe uma secção com o nome NOVO no mesmo departamento
                s_nova = Seccoes.objects.filter(departamento=depto, nome__iexact=nome_novo).exclude(id=s_antiga.id).first()
                
                if s_nova:
                    # EXISTEM AMBAS: Mesclar
                    u, d = mesclar_seccao(s_antiga, s_nova)
                    total_mesclados += 1
                else:
                    # SÓ EXISTE A ANTIGA: Simplesmente renomear
                    s_antiga.nome = nome_novo
                    s_antiga.save()
                    total_corrigidos += 1
                    print(f"    [Renamed] ID {s_antiga.id} no depto {depto.id}")

    print(f"\n--- RESUMO ---")
    print(f"Renomeados: {total_corrigidos}")
    print(f"Mesclados (Duplicatas): {total_mesclados}")
    print(f"---------------\n")

if __name__ == "__main__":
    padronizar_seccoes()
