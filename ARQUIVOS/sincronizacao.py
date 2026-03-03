"""
Utilitário de Sincronização Offline para o SIGAP.

Permite exportar e importar pacotes de movimentações de documentos
entre instâncias que não possuem conexão permanente com o servidor central.

Fluxo:
  1. A instância ONLINE cria o pacote via `exportar_pacote()`
  2. O pacote (JSON cifrado ou simples) é transportado fisicamente (pendrive, etc.)
  3. A instância OFFLINE importa o pacote via `importar_pacote()`
  4. Movimentações importadas são marcadas com `via_sincronizacao=True`
"""

import json
import uuid
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from ARQUIVOS.models import (
    Documento,
    MovimentacaoDocumento,
    Departamento,
    Seccoes,
    Notificacao,
    CustomUser,
)


def exportar_pacote(administracao_origem, administracao_destino=None):
    """
    Exporta todas as movimentações pendentes de sincronização para um pacote JSON.

    Args:
        administracao_origem: Administração que está a exportar os dados.
        administracao_destino: (Opcional) Filtrar movimentações destinadas a uma
                               administração específica.

    Returns:
        dict: Pacote JSON serializado com as movimentações pendentes.
    """
    movimentacoes = MovimentacaoDocumento.objects.filter(
        estado_sync='pendente',
    )

    # Filtrar por administração de origem (via departamento)
    movimentacoes = movimentacoes.filter(
        departamento_origem__administracao=administracao_origem
    )

    # Se houver destino específico, filtrar
    if administracao_destino:
        movimentacoes = movimentacoes.filter(
            departamento_destino__administracao=administracao_destino
        )

    pacote = {
        'versao': '1.0',
        'data_exportacao': timezone.now().isoformat(),
        'origem': {
            'administracao_id': administracao_origem.id,
            'administracao_nome': administracao_origem.nome,
            'tipo': administracao_origem.tipo_municipio,
        },
        'movimentacoes': [],
    }

    for mov in movimentacoes.select_related(
        'documento', 'departamento_origem', 'departamento_destino',
        'seccao_origem', 'seccao_destino', 'usuario'
    ):
        # Atribuir sync_id se ainda não tiver
        if not mov.sync_id:
            mov.sync_id = uuid.uuid4()
            mov.save(update_fields=['sync_id'])

        item = {
            'sync_id': str(mov.sync_id),
            'documento': {
                'numero_protocolo': mov.documento.numero_protocolo,
                'titulo': mov.documento.titulo,
                'status': mov.documento.status,
                'prioridade': mov.documento.prioridade,
                'niveis': mov.documento.niveis,
            },
            'tipo_movimentacao': mov.tipo_movimentacao,
            'departamento_origem': mov.departamento_origem.nome if mov.departamento_origem else None,
            'departamento_destino': mov.departamento_destino.nome if mov.departamento_destino else None,
            'seccao_origem': mov.seccao_origem.nome if mov.seccao_origem else None,
            'seccao_destino': mov.seccao_destino.nome if mov.seccao_destino else None,
            'usuario': mov.usuario.username,
            'data_movimentacao': mov.data_movimentacao.isoformat(),
            'observacoes': mov.observacoes or '',
            'despacho': mov.despacho or '',
        }
        pacote['movimentacoes'].append(item)

    return pacote


def marcar_como_sincronizado(administracao_origem, administracao_destino=None):
    """
    Marca todas as movimentações pendentes como sincronizadas após a exportação.
    Deve ser chamado DEPOIS de confirmar que o pacote foi entregue com sucesso.
    """
    qs = MovimentacaoDocumento.objects.filter(
        estado_sync='pendente',
        departamento_origem__administracao=administracao_origem,
    )
    if administracao_destino:
        qs = qs.filter(departamento_destino__administracao=administracao_destino)

    total = qs.update(estado_sync='sincronizado')
    return total


@transaction.atomic
def importar_pacote(pacote_json, administracao_destino):
    """
    Importa um pacote de movimentações de outra instância.

    Args:
        pacote_json: dict com o pacote exportado.
        administracao_destino: Administração que está a receber os dados.

    Returns:
        dict com estatísticas da importação.
    """
    resultados = {
        'importados': 0,
        'duplicados': 0,
        'erros': [],
    }

    for item in pacote_json.get('movimentacoes', []):
        sync_id = item.get('sync_id')

        # Evitar duplicados
        if MovimentacaoDocumento.objects.filter(sync_id=sync_id).exists():
            resultados['duplicados'] += 1
            continue

        try:
            # Localizar departamento de destino na administração local
            dept_destino = None
            if item.get('departamento_destino'):
                dept_destino = Departamento.objects.filter(
                    nome=item['departamento_destino'],
                    administracao=administracao_destino,
                ).first()

            seccao_destino = None
            if item.get('seccao_destino') and dept_destino:
                seccao_destino = Seccoes.objects.filter(
                    nome=item['seccao_destino'],
                    departamento=dept_destino,
                ).first()

            # Localizar o documento pelo número de protocolo
            doc = Documento.objects.filter(
                numero_protocolo=item['documento']['numero_protocolo']
            ).first()

            if not doc:
                # Se não existir, criar o documento no destino
                from ARQUIVOS.models.documento import TipoDocumento
                
                # Assume-se que um TipoDocumento base pode ser resolvido ou criar um genérico localmente
                # Para simplificar na POC/Offline, usaremos o primeiro disponível ou "Ofício" se não tiver
                tipo_doc = TipoDocumento.objects.first()
                if not tipo_doc:
                    tipo_doc, _ = TipoDocumento.objects.get_or_create(nome="Importado Offline")

                # Localizar ou criar criador localmente 
                criador = CustomUser.objects.filter(username=item['usuario']).first()
                if not criador:
                    criador = CustomUser.objects.filter(is_superuser=True).first()

                doc = Documento.objects.create(
                    titulo=item['documento']['titulo'],
                    numero_protocolo=item['documento']['numero_protocolo'],
                    status=item['documento']['status'],
                    prioridade=item['documento']['prioridade'],
                    niveis=item['documento']['niveis'],
                    tipo_documento=tipo_doc,
                    criado_por=criador,
                    administracao=administracao_destino,
                    departamento_origem=dept_destino,
                    departamento_atual=dept_destino,
                )

            # Criar a movimentação importada
            mov = MovimentacaoDocumento(
                documento=doc,
                tipo_movimentacao=item['tipo_movimentacao'],
                departamento_destino=dept_destino,
                seccao_destino=seccao_destino,
                usuario=CustomUser.objects.filter(username=item['usuario']).first() or doc.criado_por,
                observacoes=item.get('observacoes', ''),
                despacho=item.get('despacho', ''),
                via_sincronizacao=True,
                estado_sync='sincronizado',
                sync_id=uuid.UUID(sync_id),
            )
            mov.save()

            # Atualizar posição atual do documento
            if dept_destino:
                doc.departamento_atual = dept_destino
            if seccao_destino:
                doc.seccao_atual = seccao_destino
            doc.save()

            # Criar notificação para o departamento de destino
            if dept_destino:
                usuarios_destino = CustomUser.objects.filter(
                    departamento=dept_destino,
                    administracao=administracao_destino,
                )
                origem_nome = pacote_json.get('origem', {}).get('administracao_nome', 'Origem desconhecida')
                for user in usuarios_destino:
                    Notificacao.objects.create(
                        usuario=user,
                        mensagem=f"📥 Documento {doc.numero_protocolo} recebido via sincronização de {origem_nome}",
                        link=f"/detalhe/{doc.pk}/",
                    )

            resultados['importados'] += 1

        except Exception as e:
            resultados['erros'].append(f"Erro ao importar {sync_id}: {str(e)}")

    return resultados
