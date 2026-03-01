import os
import django
import collections

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SGA.settings')
django.setup()

from ARQUIVOS.models import Seccoes, CustomUser, Documento, MovimentacaoDocumento, Departamento

def migrate_data(old_id, new_id, name):
    try:
        old_sec = Seccoes.objects.get(id=old_id)
        new_sec = Seccoes.objects.get(id=new_id)
    except Seccoes.DoesNotExist:
        return

    print(f"    [Migrando] ID {old_id} -> ID {new_id} ({name})")
    
    # Migrar Usuários
    users = CustomUser.objects.filter(seccao=old_sec)
    count_users = users.count()
    users.update(seccao=new_sec)
    
    # Migrar Documentos
    docs = Documento.objects.filter(seccao_atual=old_sec)
    count_docs = docs.count()
    docs.update(seccao_atual=new_sec)
    
    # Migrar Movimentações
    mov_orig = MovimentacaoDocumento.objects.filter(seccao_origem=old_sec)
    count_mov_orig = mov_orig.count()
    mov_orig.update(seccao_origem=new_sec)
    
    mov_dest = MovimentacaoDocumento.objects.filter(seccao_destino=old_sec)
    count_mov_dest = mov_dest.count()
    mov_dest.update(seccao_destino=new_sec)
    
    print(f"      - Sincronizados: {count_users} usuários, {count_docs} docs, {count_mov_orig+count_mov_dest} movs")
    
    # Deletar antiga
    old_sec.delete()

def cleanup_sections():
    print("="*80)
    print("INICIANDO LIMPEZA E DESDUPLICAÇÃO DE SECÇÕES (REFINADO)")
    print("="*80)
    
    # 1. Tratar "Diretor" vs "Director"
    diretor_seccs = list(Seccoes.objects.filter(nome__icontains='Diretor').order_by('id'))
    print(f"Encontradas {len(diretor_seccs)} secções com 'Diretor'.")
    
    for s in diretor_seccs:
        # Re-buscar para garantir que ainda existe (pode ter sido deletada em merge anterior)
        try:
            s = Seccoes.objects.get(id=s.id)
        except Seccoes.DoesNotExist:
            continue
            
        old_name = s.nome
        new_name = s.nome.replace('Diretor', 'Director')
        
        if old_name == new_name:
            continue
            
        # Verificar se já existe uma com o novo nome no mesmo departamento
        existing = Seccoes.objects.filter(nome=new_name, departamento=s.departamento).exclude(id=s.id).first()
        
        if existing:
            print(f"  [Merge Necessário] {old_name} já existe como {new_name}")
            migrate_data(s.id, existing.id, new_name)
        else:
            print(f"  [Renomeando] {old_name} -> {new_name}")
            s.nome = new_name
            s.save()

    # 2. Mesclar duplicatas exatas residuais
    print("\nBuscando duplicatas exatas residuais...")
    from django.db.models import Count
    duplicates = Seccoes.objects.values('nome', 'departamento').annotate(count=Count('id')).filter(count__gt=1)
    
    total_merged = 0
    for dup in duplicates:
        name = dup['nome']
        dept_id = dup['departamento']
        seccs = list(Seccoes.objects.filter(nome=name, departamento_id=dept_id).order_by('id'))
        
        primary = seccs[0]
        others = seccs[1:]
        
        for other in others:
            migrate_data(other.id, primary.id, name)
            total_merged += 1

    print(f"\nTotal de merges realizados: {total_merged}")
    print("="*80)
    print("LIMPEZA CONCLUÍDA COM SUCESSO!")
    print("="*80)

if __name__ == "__main__":
    cleanup_sections()
