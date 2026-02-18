from django.db import models
from django.db.models import Q
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
        if getattr(user, 'eh_tecnico', True): # Default True se não tiver atributo
             return qs.filter(
                Q(criado_por=user) |            # Meus documentos (criados)
                Q(responsavel_atual=user)       # Atribuídos a mim (distribuídos)
             ).distinct()

        # Se for Chefia/Direção (Nivel >= 1), vê tudo do seu setor + Histórico
        # (Mantém lógica original de setor, mas agora restrita a chefes)

        # 2. Usuário de Secção (Chefia)
        if hasattr(user, 'seccao') and user.seccao:
            return qs.filter(
                Q(seccao_atual=user.seccao) |
                Q(movimentacoes__seccao_origem=user.seccao) |
                Q(movimentacoes__seccao_destino=user.seccao)
            ).distinct()

        # 3. Usuário de Departamento (Direção)
        if hasattr(user, 'departamento') and user.departamento:
            return qs.filter(
                Q(departamento_atual=user.departamento) |
                Q(movimentacoes__departamento_origem=user.departamento) |
                Q(movimentacoes__departamento_destino=user.departamento)
            ).distinct()

        # 4. Fallback
        return qs.filter(criado_por=user).distinct()


class AdministracaoManager(models.Manager):
    """Manager para Administracao"""
    pass


class DepartamentoManager(models.Manager):
    """Manager para Departamento com lógica de isolamento"""

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


from django.contrib.auth.models import UserManager as BaseUserManager

class UsuarioManager(BaseUserManager):
    """Manager para CustomUser com lógica de isolamento"""

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