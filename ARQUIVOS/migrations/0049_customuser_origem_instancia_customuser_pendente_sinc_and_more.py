import uuid
from django.db import migrations, models


def gen_uuid_for_model(apps, schema_editor, model_name):
    Model = apps.get_model('ARQUIVOS', model_name)
    for row in Model.objects.all():
        row.uuid_sinc = uuid.uuid4()
        row.save(update_fields=['uuid_sinc'])


def gen_uuid_customuser(apps, schema_editor):
    gen_uuid_for_model(apps, schema_editor, 'CustomUser')


def gen_uuid_tipodocumento(apps, schema_editor):
    gen_uuid_for_model(apps, schema_editor, 'TipoDocumento')


def gen_uuid_anexo(apps, schema_editor):
    gen_uuid_for_model(apps, schema_editor, 'Anexo')


def gen_uuid_notificacao(apps, schema_editor):
    gen_uuid_for_model(apps, schema_editor, 'Notificacao')


def gen_uuid_configuracaosistema(apps, schema_editor):
    gen_uuid_for_model(apps, schema_editor, 'ConfiguracaoSistema')


def gen_uuid_localarmazenamento(apps, schema_editor):
    gen_uuid_for_model(apps, schema_editor, 'LocalArmazenamento')


def gen_uuid_armazenamentodocumento(apps, schema_editor):
    gen_uuid_for_model(apps, schema_editor, 'ArmazenamentoDocumento')


class Migration(migrations.Migration):

    dependencies = [
        ('ARQUIVOS', '0048_add_unique_to_uuid'),
    ]

    operations = [
        # Models that ALREADY had SyncMixin
        migrations.AlterField(model_name='administracao', name='uuid_sinc',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
        migrations.AlterField(model_name='departamento', name='uuid_sinc',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
        migrations.AlterField(model_name='seccoes', name='uuid_sinc',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
        migrations.AlterField(model_name='documento', name='uuid_sinc',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
        migrations.AlterField(model_name='movimentacaodocumento', name='uuid_sinc',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),

        # CustomUser
        migrations.AddField(model_name='customuser', name='origem_instancia',
            field=models.CharField(blank=True, default='', max_length=100)),
        migrations.AddField(model_name='customuser', name='pendente_sinc',
            field=models.BooleanField(db_index=True, default=True)),
        migrations.AddField(model_name='customuser', name='ultima_sincronizacao',
            field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='customuser', name='uuid_sinc',
            field=models.UUIDField(db_index=True, editable=False, null=True)),
        migrations.RunPython(gen_uuid_customuser, migrations.RunPython.noop),
        migrations.AlterField(model_name='customuser', name='uuid_sinc',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),

        # TipoDocumento
        migrations.AddField(model_name='tipodocumento', name='origem_instancia',
            field=models.CharField(blank=True, default='', max_length=100)),
        migrations.AddField(model_name='tipodocumento', name='pendente_sinc',
            field=models.BooleanField(db_index=True, default=True)),
        migrations.AddField(model_name='tipodocumento', name='ultima_sincronizacao',
            field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='tipodocumento', name='uuid_sinc',
            field=models.UUIDField(db_index=True, editable=False, null=True)),
        migrations.RunPython(gen_uuid_tipodocumento, migrations.RunPython.noop),
        migrations.AlterField(model_name='tipodocumento', name='uuid_sinc',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),

        # Anexo
        migrations.AddField(model_name='anexo', name='origem_instancia',
            field=models.CharField(blank=True, default='', max_length=100)),
        migrations.AddField(model_name='anexo', name='pendente_sinc',
            field=models.BooleanField(db_index=True, default=True)),
        migrations.AddField(model_name='anexo', name='ultima_sincronizacao',
            field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='anexo', name='uuid_sinc',
            field=models.UUIDField(db_index=True, editable=False, null=True)),
        migrations.RunPython(gen_uuid_anexo, migrations.RunPython.noop),
        migrations.AlterField(model_name='anexo', name='uuid_sinc',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),

        # Notificacao
        migrations.AddField(model_name='notificacao', name='origem_instancia',
            field=models.CharField(blank=True, default='', max_length=100)),
        migrations.AddField(model_name='notificacao', name='pendente_sinc',
            field=models.BooleanField(db_index=True, default=True)),
        migrations.AddField(model_name='notificacao', name='ultima_sincronizacao',
            field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='notificacao', name='uuid_sinc',
            field=models.UUIDField(db_index=True, editable=False, null=True)),
        migrations.RunPython(gen_uuid_notificacao, migrations.RunPython.noop),
        migrations.AlterField(model_name='notificacao', name='uuid_sinc',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),

        # ConfiguracaoSistema
        migrations.AddField(model_name='configuracaosistema', name='origem_instancia',
            field=models.CharField(blank=True, default='', max_length=100)),
        migrations.AddField(model_name='configuracaosistema', name='pendente_sinc',
            field=models.BooleanField(db_index=True, default=True)),
        migrations.AddField(model_name='configuracaosistema', name='ultima_sincronizacao',
            field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='configuracaosistema', name='uuid_sinc',
            field=models.UUIDField(db_index=True, editable=False, null=True)),
        migrations.RunPython(gen_uuid_configuracaosistema, migrations.RunPython.noop),
        migrations.AlterField(model_name='configuracaosistema', name='uuid_sinc',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),

        # LocalArmazenamento
        migrations.AddField(model_name='localarmazenamento', name='origem_instancia',
            field=models.CharField(blank=True, default='', max_length=100)),
        migrations.AddField(model_name='localarmazenamento', name='pendente_sinc',
            field=models.BooleanField(db_index=True, default=True)),
        migrations.AddField(model_name='localarmazenamento', name='ultima_sincronizacao',
            field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='localarmazenamento', name='uuid_sinc',
            field=models.UUIDField(db_index=True, editable=False, null=True)),
        migrations.RunPython(gen_uuid_localarmazenamento, migrations.RunPython.noop),
        migrations.AlterField(model_name='localarmazenamento', name='uuid_sinc',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),

        # ArmazenamentoDocumento
        migrations.AddField(model_name='armazenamentodocumento', name='origem_instancia',
            field=models.CharField(blank=True, default='', max_length=100)),
        migrations.AddField(model_name='armazenamentodocumento', name='pendente_sinc',
            field=models.BooleanField(db_index=True, default=True)),
        migrations.AddField(model_name='armazenamentodocumento', name='ultima_sincronizacao',
            field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='armazenamentodocumento', name='uuid_sinc',
            field=models.UUIDField(db_index=True, editable=False, null=True)),
        migrations.RunPython(gen_uuid_armazenamentodocumento, migrations.RunPython.noop),
        migrations.AlterField(model_name='armazenamentodocumento', name='uuid_sinc',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
    ]
