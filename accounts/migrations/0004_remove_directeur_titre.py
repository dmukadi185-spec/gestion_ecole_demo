from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_professeur"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="directeur",
            name="titre",
        ),
    ]
