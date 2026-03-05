from django.db import models
import uuid
from tinymce.models import HTMLField
from django.conf import settings
from django.core.validators import RegexValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from ARQUIVOS.managers import DocumentoManager
from ARQUIVOS.models.mixins import SoftDeleteModel, AuditoriaModel, SyncMixin

class TipoDocumento(SyncMixin):
    """
    Tipos de documentos que podem ser cadastrados
    """
    nome = models.CharField(max_length=50, unique=True)
    descricao = models.TextField(blank=True)
    prazo_dias = models.IntegerField(default=30, help_text="Prazo padrão em dias para processamento")
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documentos"


class StatusDocumento(models.TextChoices):
    CRIACAO = 'criacao', 'Criação'
    RECEBIMENTO = 'recebimento', 'Recebimento'
    ENCAMINHAMENTO = 'encaminhamento', 'Encaminhamento'
    DESPACHO = 'despacho', 'Despacho'
    APROVADO = 'aprovado', 'Aprovado'
    REPROVADO = 'reprovado', 'Reprovado'
    ARQUIVADO = 'arquivado', 'Arquivado'


class Documento(SoftDeleteModel, AuditoriaModel, SyncMixin):
    """
    Modelo principal para documentos
    """
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa 🟢'),
        ('normal', 'Normal 🟡'),
        ('alta', 'Alta 🟠'),
        ('urgente', 'Urgente 🔴'),
        ('muito_urgente', 'Muito Urgente 🔥'),
    ]
    ORIGEM_CHOICES = [
        ('Pessoa Singular', 'Pessoa Singular'),
        ('Instituição do Estado', 'Instituição do Estado'),
        ('Instituição Pública', 'Instituição Pública'),
        ('Instituição Privada', 'Instituição Privada'),
        ('Organização cívil', 'Organização cívil'),
    ]
    NIVEIS_CHOICES = [
        ('Público', 'Público'),
        ('Restrito', 'Restrito'),
        ('Confidencial', 'Confidencial'),
    ]
    objects = DocumentoManager()

    token_verificacao = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Token único para verificação pública via QR Code"
    )
    numero_protocolo = models.CharField(max_length=20, unique=True, editable=False)
    titulo = models.CharField('Assunto', max_length=200)
    conteudo = models.TextField(blank=True, null=True)
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.PROTECT)
    arquivo = models.FileField(
        upload_to='documentos/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'png'])]
    )
    arquivo_digitalizado = models.FileField(
        upload_to='digitalizados/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'png'])]
    )
    data_ultima_movimentacao = models.DateTimeField(auto_now=True)

    status = models.CharField(
        max_length=20,
        choices=StatusDocumento.choices,
        default=StatusDocumento.ENCAMINHAMENTO
    )
    prioridade = models.CharField(max_length=13, choices=PRIORIDADE_CHOICES, default='normal')
    niveis = models.CharField('Niveis de Acesso', max_length=50, choices=NIVEIS_CHOICES, default='Público')

    departamento_origem = models.ForeignKey('Departamento', on_delete=models.PROTECT, related_name='documentos_origem')
    departamento_atual = models.ForeignKey('Departamento', on_delete=models.PROTECT, related_name='documentos_atual')
    seccao_atual = models.ForeignKey(
        'Seccoes',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_atuais',
        help_text="Secção específica onde o documento está atualmente"
    )
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='documentos_criados')
    responsavel_atual = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='documentos_responsavel')
    
    # Campo CRÍTICO para isolamento Multi-Tenant (OBRIGATÓRIO)
    administracao = models.ForeignKey(
        'ARQUIVOS.Administracao',
        on_delete=models.PROTECT,
        related_name='documentos',
        null=True,  # TEMPORARY FIX: Allow null to enable hydration
        blank=True
    )

    data_criacao = models.DateTimeField(auto_now_add=True)
    data_prazo = models.DateTimeField(null=True, blank=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)

    tags = models.CharField(max_length=500, blank=True, help_text="O numero do Armario pasta  Armario-1/doc-335")
    referencia = models.CharField(max_length=500, blank=True, help_text="referência")

    observacoes = models.TextField(blank=True, help_text="Conteúdo do documento", null=True)


    utente = models.CharField('Remetente', max_length=200, null=True, blank=True)
    telefone = models.CharField(max_length=9, validators=[RegexValidator(r'^\d{9}$', 'O telefone deve ter 9 dígitos.')], null=True, blank=True)
    email = models.EmailField(blank=True, default='')
    # Entidade removed as it was duplicate of origem
    origem = models.CharField('Origem', max_length=52, choices=ORIGEM_CHOICES, default='Pessoa Singular')

    @property
    def dias_na_caixa(self):
        """Retorna quantos dias o documento está parado no setor atual"""
        from django.utils import timezone
        delta = timezone.now() - self.data_ultima_movimentacao
        return delta.days

    def save(self, *args, **kwargs):
        if not self.numero_protocolo:
            super().save(*args, **kwargs)
            ano = timezone.now().year
            self.numero_protocolo = f"{self.pk}/{ano}"
            # Update only the protocol field to avoid race conditions and double saves of other fields
            self.__class__.objects.filter(pk=self.pk).update(numero_protocolo=self.numero_protocolo)
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero_protocolo} - {self.titulo}"

    def get_status_color(self):
        colors = {
            StatusDocumento.RECEBIMENTO: 'primary',
            'em_analise': 'warning', # Not in choices?
            StatusDocumento.APROVADO: 'success',
            StatusDocumento.REPROVADO: 'danger',
            StatusDocumento.ARQUIVADO: 'secondary',
            StatusDocumento.ENCAMINHAMENTO: 'info',
        }
        return colors.get(self.status, 'secondary')

    def clean(self):
        super().clean()
        if self.data_prazo and not self.pk:
            if self.data_prazo < timezone.now():
                raise ValidationError({'data_prazo': 'A data de prazo não pode ser no passado.'})

    def is_vencido(self):
        return timezone.now() > self.data_prazo and self.status not in [
            StatusDocumento.APROVADO,
            StatusDocumento.REPROVADO,
            StatusDocumento.ARQUIVADO
        ]

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ['-data_criacao']


class Anexo(SyncMixin):
    """
    Anexos adicionais aos documentos
    """
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='anexos')
    arquivo = models.FileField(upload_to='anexos/%Y/%m/')
    nome = models.CharField(max_length=200)
    descricao = HTMLField(blank=True, null=True)
    usuario_upload = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    data_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.documento.numero_protocolo} - {self.nome}"

    class Meta:
        verbose_name = "Anexo"
        verbose_name_plural = "Anexos"
