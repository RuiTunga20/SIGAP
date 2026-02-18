from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from ARQUIVOS.managers import AdministracaoManager, UsuarioManager

class Administracao(models.Model):
    TIPO_MUNICIPIO_CHOICES = [
        ('A', 'Tipo A'),
        ('B', 'Tipo B'),
        ('C', 'Tipo C'),
        ('D', 'Tipo D'),
        ('E', 'Tipo E'),
        ('G', 'Governo Provincial'),
        ('M', 'Ministério'),
    ]
    nome = models.CharField(max_length=255)
    tipo_municipio = models.CharField(max_length=1, choices=TIPO_MUNICIPIO_CHOICES, default='A')
    provincia = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.nome   
    
    objects = AdministracaoManager()
    
    class GovernoManager(models.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(tipo_municipio='G')
            
    class MunicipalManager(models.Manager):
        def get_queryset(self):
            return super().get_queryset().exclude(tipo_municipio__in=['G', 'M'])
    
    class MinisterioManager(models.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(tipo_municipio='M')

    class Meta:
        verbose_name = "Administração"
        verbose_name_plural = "Administrações" 

class GovernoProvincial(Administracao):
    objects = Administracao.GovernoManager()
    class Meta:
        proxy = True
        verbose_name = "Governo Provincial"
        verbose_name_plural = "Governos Provinciais"

class AdministracaoMunicipal(Administracao):
    objects = Administracao.MunicipalManager()
    class Meta:
        proxy = True
        verbose_name = "Administração Municipal"
        verbose_name_plural = "Administrações Municipais" 

class Ministerio(Administracao):
    objects = Administracao.MinisterioManager()
    class Meta:
        proxy = True
        verbose_name = "Ministério"
        verbose_name_plural = "Ministérios"

class CustomUser(AbstractUser):
    objects = UsuarioManager()

    NIVEL_CHOICES = [
        # --- Gestão (todos os tipos) ---
        ('admin_sistema', 'Administrador de Sistema'),

        # --- Gestão MAT ---
        ('ministro', 'Ministro'),
        ('secretario_estado', 'Secretário de Estado'),

        # --- Gestão Governo ---
        ('governador', 'Governador Provincial'),
        ('vice_governador', 'Vice-Governador'),

        # --- Gestão Administração Municipal ---
        ('admin_municipal', 'Administrador Municipal'),
        ('admin_adjunto', 'Administrador Adjunto'),

        # --- Direcção MAT ---
        ('diretor_nacional', 'Director Nacional e Equiparado'),

        # --- Direcção MAT + Governo ---
        ('chefe_departamento', 'Chefe de Departamento'),

        # --- Direcção Governo ---
        ('diretor_gabinete', 'Director de Gabinete Provincial e Equiparado'),

        # --- Direcção Administração Municipal ---
        ('diretor_municipal', 'Director Municipal e Equiparado'),
        ('chefe_seccao', 'Chefe de Secção'),

        # --- Operacional (todos os tipos) ---
        ('tecnico', 'Técnico'),
    ]

    # ============================================================
    # Constantes de Grupo de Permissões
    # ============================================================
    NIVEIS_GESTAO = [
        'admin_sistema',
        'ministro', 'secretario_estado',
        'governador', 'vice_governador',
        'admin_municipal', 'admin_adjunto',
    ]

    NIVEIS_DIRECAO = [
        'diretor_nacional', 'chefe_departamento',
        'diretor_gabinete',
        'diretor_municipal', 'chefe_seccao',
    ]

    NIVEIS_TECNICO = ['tecnico']

    # ============================================================
    # Mapeamento: Tipo de Administração → Níveis permitidos
    # ============================================================
    NIVEIS_POR_TIPO = {
        'M': [  # MAT / Ministério
            'admin_sistema', 'ministro', 'secretario_estado',
            'diretor_nacional', 'chefe_departamento', 'tecnico',
        ],
        'G': [  # Governo Provincial
            'admin_sistema', 'governador', 'vice_governador',
            'diretor_gabinete', 'chefe_departamento', 'tecnico',
        ],
        '_default': [  # Administrações Municipais (A-E)
            'admin_sistema', 'admin_municipal', 'admin_adjunto',
            'diretor_municipal', 'chefe_seccao', 'tecnico',
        ],
    }

    @classmethod
    def niveis_para_tipo(cls, tipo_municipio):
        """Retorna os NIVEL_CHOICES filtrados pelo tipo de administração."""
        codigos = cls.NIVEIS_POR_TIPO.get(tipo_municipio, cls.NIVEIS_POR_TIPO['_default'])
        return [(k, v) for k, v in cls.NIVEL_CHOICES if k in codigos]

    nivel_acesso = models.CharField(max_length=30, choices=NIVEL_CHOICES, default='tecnico')

    # Nível de Sigilo para Confidencialidade e Hierarquia
    # 0 = Técnico (Vê apenas atribuídos/públicos)
    # 1 = Chefia (Vê tudo do setor + Restritos)
    # 2 = Direção (Vê tudo + Confidenciais)
    nivel_sigilo = models.IntegerField(default=0, help_text="0=Técnico, 1=Chefia, 2=Direção")

    def pode_distribuir(self):
        """Retorna True se o usuário pode distribuir documentos (Chefia/Direção)."""
        return self.nivel_sigilo >= 1

    @property
    def eh_tecnico(self):
        """Retorna True se for apenas técnico (nível 0)."""
        return self.nivel_sigilo == 0

    # Departamento pode ser opcional se o usuário está em uma secção
    departamento = models.ForeignKey(
        'Departamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_departamento',
        default=1
    )

    # Secção é opcional - nem todos estão em secções específicas
    seccao = models.ForeignKey(
        'Seccoes',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_seccao'
    )

    telefone = models.CharField(max_length=15, blank=True)
    # Usuário DEVE pertencer a uma administração (OBRIGATÓRIO - Multi-Tenant)
    administracao = models.ForeignKey(
        'Administracao',
        on_delete=models.PROTECT,  # Não pode deletar admin com usuários
        null=True,  # TEMPORARY FIX: Allow null to enable hydration
        blank=True,
        related_name='usuarios_administracao'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """Valida a consistência entre departamento e secção"""
        super().clean()

        # Se tem secção, valida se pertence ao departamento
        if self.seccao and self.departamento:
            if self.seccao.departamento != self.departamento:
                raise ValidationError({
                    'seccao': 'A secção selecionada não pertence ao departamento escolhido.'
                })

        # Validação: deve ter pelo menos departamento OU secção
        if not self.departamento and not self.seccao:
            raise ValidationError(
                'O utilizador deve pertencer a pelo menos um departamento ou secção.'
            )
            
        # Validação Redundante de Segurança (Isolamento)
        if self.administracao and self.departamento and self.departamento.administracao:
            if self.departamento.administracao != self.administracao:
                raise ValidationError({
                    'departamento': f'O departamento "{self.departamento.nome}" pertence à administração "{self.departamento.administracao.nome}", mas o usuário está na administração "{self.administracao.nome}".'
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def departamento_efetivo(self):
        """
        Retorna o departamento do usuário
        PRIORIZA a secção se existir
        """
        if self.seccao:
            return self.seccao.departamento
        elif self.departamento:
            return self.departamento
        return None

    @property
    def localizacao_atual(self):
        """
        Retorna a localização específica (secção ou departamento)
        Para uso em formulários e views
        """
        return {
            'seccao': self.seccao,
            'departamento': self.departamento if not self.seccao else self.seccao.departamento
        }

    def pode_ver_usuario(self, outro_usuario):
        """
        Verifica se este usuário pode ver o outro_usuario.
        """
        # Admin sistema vê todos
        if self.nivel_acesso == 'admin_sistema':
            return True
        
        # Se não tem administração, não vê ninguém (ou só a si mesmo?)
        if not self.administracao:
            return False
            
        # Mesma administração
        return self.administracao == outro_usuario.administracao


    def __str__(self):
        if self.seccao:
            return f"{self.username} - {self.seccao.nome} ({self.seccao.departamento.nome})"
        elif self.departamento:
            return f"{self.username} - {self.departamento.nome}"
        return f"{self.username} - {self.get_nivel_acesso_display()}"
