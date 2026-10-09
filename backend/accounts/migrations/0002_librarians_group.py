from django.contrib.auth.management import create_permissions
from django.db import migrations

PERMISSIONS = [
    "add_loan",
    "change_loan",
    "view_loan",
    "view_member",
    "view_copy",
    "change_copy",
]


def create_group(apps, schema_editor):
    # I permessi vengono creati dopo TUTTE le migrazioni (segnale post_migrate):
    # su un database nuovo qui non esisterebbero ancora, quindi li creiamo noi
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, verbosity=0)
        app_config.models_module = None

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    group, _ = Group.objects.get_or_create(name="Bibliotecari")
    group.permissions.set(Permission.objects.filter(codename__in=PERMISSIONS))


def delete_group(apps, schema_editor):
    apps.get_model("auth", "Group").objects.filter(name="Bibliotecari").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("circulation", "0001_initial"),
        ("inventory", "0001_initial"),
    ]

    operations = [migrations.RunPython(create_group, delete_group)]
