import uuid
from django.db import migrations, models

def fill_uuids(apps, schema_editor):
    for model_name in ["Administracao", "Departamento", "Documento", "MovimentacaoDocumento", "Seccoes"]:
        Model = apps.get_model("ARQUIVOS", model_name)
        for obj in Model.objects.all():
            obj.uuid_sinc = uuid.uuid4()
            obj.save(update_fields=["uuid_sinc"])

class Migration(migrations.Migration):
    dependencies = [("ARQUIVOS", "0045_adicionar_campos_sincronizacao_offline")]
    operations = [
        migrations.RunPython(fill_uuids, migrations.RunPython.noop),
        migrations.AlterField(model_name="administracao", name="uuid_sinc", field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
        migrations.AlterField(model_name="departamento", name="uuid_sinc", field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
        migrations.AlterField(model_name="documento", name="uuid_sinc", field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
        migrations.AlterField(model_name="movimentacaodocumento", name="uuid_sinc", field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
        migrations.AlterField(model_name="seccoes", name="uuid_sinc", field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
    ]
