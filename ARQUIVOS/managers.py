from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from ARQUIVOS.models.mixins import SoftDeleteManager


class DocumentoManager(SoftDeleteManager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'tipo_documento',
            'departamento_origem',
            'departamento_atual',
            'seccao_atual',
            'criado_por',
            'responsavel_atual'
        )

    def para_usuario(self, user):
        """
        Filtra documentos visíveis para o usuário baseado na hierarquia, 
        ADMINISTRAÇÃO e HISTÓRICO de movimentação.
        """
        qs = self.get_queryset()

        if not user.is_superuser and user.administracao:
            if not user.administracao:
                return qs.none()
            
            # Filtro Multi-Tenant: Apenas documentos da administração
            qs = qs.filter(
                Q(administracao=user.administracao) | 
                Q(departamento_atual__administracao=user.administracao) |
                Q(movimentacoes__departamento_destino__administracao=user.administracao) |
                Q(movimentacoes__seccao_destino__departamento__administracao=user.administracao)
            ).distinct()

        # --- NOVA LÓGICA DE CONFIDENCIALIDADE E HIERARQUIA ---
        
        # Se for Técnico (Nível 0), aplica filtro restritivo "NEED-TO-KNOW"
        # MAS: Permite ver todos os expedientes registados HOJE na sua administração
        if getattr(user, 'eh_tecnico', lambda: False)():
             from django.utils import timezone
             hoje = timezone.now().date()
             
             # 1. Meus documentos (criados ou atribuídos ou histórico)
             q_meus = Q(criado_por=user) | Q(responsavel_atual=user) | Q(movimentacoes__usuario=user)
             
             # 2. Documentos da minha administração criados hoje (Acesso solicitado)
             q_hoje = Q(administracao=user.administracao, data_criacao__date=hoje)
             
             # 3. PLUS: Qualquer documento finalizado (Arquivo Morto) do meu departamento/secção
             status_mortos = ['despacho', 'aprovado', 'reprovado', 'arquivado']
             if user.seccao:
                 q_arquivo_morto = Q(seccao_atual=user.seccao, status__in=status_mortos)
             elif user.departamento:
                 q_arquivo_morto = Q(departamento_atual=user.departamento, seccao_atual__isnull=True, status__in=status_mortos)
             else:
                 q_arquivo_morto = Q(pk__in=[])
                  
             return qs.filter(q_meus | q_hoje | q_arquivo_morto).distinct()

        # Se for Chefia/Direção (Nivel >= 1), vê tudo do seu setor + Histórico
        # (Mantém lógica original de setor, mas agora restrita a chefes)

        # 2. Usuário de Secção (Chefia Nível 1)
        if hasattr(user, 'seccao') and user.seccao:
            # ISOLAMENTO ESTRITO:
            # Vê APENAS documentos que estão fisicamente na secção (seccao_atual = secção)
            # OU documentos que foram enviados para a secção (movimentacao destino = secção)
            # OU histórico próprio (criou ou movimentou)
            return qs.filter(
                Q(seccao_atual=user.seccao) |
                Q(movimentacoes__seccao_destino=user.seccao) |
                Q(criado_por=user) |
                Q(movimentacoes__usuario=user)
            ).distinct()

        # 3. Usuário de Departamento (Direção Nível 2)
        if hasattr(user, 'departamento') and user.departamento:
            # ISOLAMENTO: Diretor vê documentos no nível do departamento (seccao_atual IS NULL)
            # Se o documento entrar em uma secção, o Diretor "perde" a visão direta (isolamento)
            # a menos que ele tenha participado do histórico.
            return qs.filter(
                Q(departamento_atual=user.departamento, seccao_atual__isnull=True) |
                Q(movimentacoes__departamento_origem=user.departamento) |
                Q(movimentacoes__departamento_destino=user.departamento) |
                Q(criado_por=user) |
                Q(movimentacoes__usuario=user)
            ).distinct()

        # 4. Fallback (Garante pelo menos o que ele criou ou movimentou)
        return qs.filter(
            Q(criado_por=user) |
            Q(movimentacoes__usuario=user)
        ).distinct()


class AdministracaoManager(models.Manager):
    """Manager para Administracao com suporte a Natural Keys"""
    def get_by_natural_key(self, uuid_sinc):
        return self.get(uuid_sinc=uuid_sinc)


class DepartamentoManager(models.Manager):
    """Manager para Departamento com lógica de isolamento e Natural Keys"""
    def get_by_natural_key(self, uuid_sinc):
        return self.get(uuid_sinc=uuid_sinc)

    def para_administracao(self, administracao):
        """
        Retorna departamentos que a administração pode ver:
        1. Departamentos genéricos do mesmo tipo da administração (ex: Tipo A)
        2. Departamentos específicos vinculados a esta administração
        """
        if not administracao:
            return self.none()

        return self.filter(
            Q(tipo_municipio=administracao.tipo_municipio, administracao__isnull=True) |  # Genéricos do mesmo tipo
            Q(administracao=administracao)  # Específicos desta administração
        ).distinct()


class SeccaoManager(models.Manager):
    """Manager para Secção com suporte a Natural Keys"""
    def get_by_natural_key(self, uuid_sinc):
        return self.get(uuid_sinc=uuid_sinc)


from django.contrib.auth.models import UserManager as BaseUserManager

class UsuarioManager(BaseUserManager):
    """Manager para CustomUser com lógica de isolamento e Natural Keys"""
    def get_by_natural_key(self, identifier):
        try:
            # Tenta tratar o identificador como UUID (para sincronização entre instâncias)
            return self.get(uuid_sinc=identifier)
        except (self.model.DoesNotExist, ValidationError, ValueError, TypeError):
            # Fallback para username (para autenticação padrão do Django / ModelBackend)
            return self.get(username=identifier)

    def da_mesma_administracao(self, usuario):
        """
        Retorna apenas usuários da mesma administração do usuário solicitante.
        Se o usuário for admin de sistema, pode ver todos.
        """
        if not usuario or not usuario.is_authenticated:
            return self.none()

        # Admin Sistema (sem administração vinculada) vê TODAS
        if usuario.nivel_acesso == 'admin_sistema':
            return self.all()

        if not usuario.administracao:
            return self.none()

        return self.filter(administracao=usuario.administracao)

    def para_usuario(self, usuario):
        """Alias para da_mesma_administracao"""
        return self.da_mesma_administracao(usuario)