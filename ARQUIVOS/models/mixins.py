from django.db import models
from django.utils import timezone

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        return super().get_queryset()

    def deleted(self):
        return super().get_queryset().filter(is_deleted=True)

class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager() # Access everything including deleted

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self):
        super().delete()

class AuditoriaModel(models.Model):
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    class Meta:
        abstract = True


import uuid

class SyncMixin(models.Model):
    """
    Mixin para sincronização online/offline.
    Adiciona um UUID global (para evitar colisões de PK entre instâncias),
    um flag de sincronização pendente e um timestamp de última sincronização.
    """
    uuid_sinc = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
        help_text="Identificador universal para sincronização entre instâncias"
    )
    pendente_sinc = models.BooleanField(
        default=True,
        db_index=True,
        help_text="True se este registo ainda não foi sincronizado com o servidor central"
    )
    ultima_sincronizacao = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Última vez que este registo foi sincronizado"
    )
    origem_instancia = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Identificador da instância que criou este registo (ex: 'admin_municipal_cabinda')"
    )

    class Meta:
        abstract = True
