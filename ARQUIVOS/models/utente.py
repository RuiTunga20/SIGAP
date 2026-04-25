from django.db import models
from .mixins import AuditoriaModel, SyncMixin

class Utente(AuditoriaModel, SyncMixin):
    """
    Representa uma pessoa singular, empresa ou instituição que envia/recebe documentos.
    A mesma entidade pode ser registada uma única vez e ter múltiplos documentos.
    """
    ORIGEM_CHOICES = [
        ('Pessoa Singular', 'Pessoa Singular'),
        ('Instituição do Estado', 'Instituição do Estado'),
        ('Instituição Pública', 'Instituição Pública'),
        ('Instituição Privada', 'Instituição Privada'),
        ('Organização cívil', 'Organização cívil'),
    ]

    nome = models.CharField('Nome / Designação', max_length=200)
    nif = models.CharField('NIF / BI', max_length=14, null=True, blank=True)
    telefone = models.CharField('Telefone', max_length=50, null=True, blank=True)
    email = models.EmailField('E-mail', blank=True, default='')
    tipo = models.CharField('Tipo de Utente', max_length=52, choices=ORIGEM_CHOICES, default='Pessoa Singular')
    
    administracao = models.ForeignKey(
        'ARQUIVOS.Administracao',
        on_delete=models.SET_NULL,
        related_name='utentes',
        null=True,
        blank=True,
        help_text="Opcional: Permite isolar os utentes por município."
    )

    def natural_key(self):
        return (str(self.uuid_sinc),)

    def __str__(self):
        if self.nif:
            return f"{self.nome} ({self.nif})"
        return self.nome

    class Meta:
        verbose_name = "Utente / Entidade"
        verbose_name_plural = "Utentes e Entidades"
        ordering = ['nome']
