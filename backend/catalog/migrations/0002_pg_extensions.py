from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
    ]

    # CREATE EXTENSION pg_trgm: serve prima di creare l'indice gin_trgm_ops
    operations = [TrigramExtension()]
