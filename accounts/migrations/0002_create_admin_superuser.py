from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_admin_user(apps, schema_editor):
    User = apps.get_model('auth', 'User')

    # Ensure 'admin' superuser exists
    admin_user = User.objects.filter(username='admin').first()
    if not admin_user:
        admin_user = User.objects.create(
            username='admin',
            email='admin@campus.eventhub.co.ke',
            first_name='Campus',
            last_name='Admin',
            is_staff=True,
            is_superuser=True,
            password=make_password('Admin@2026Pass!')
        )
    else:
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.password = make_password('Admin@2026Pass!')
        admin_user.save()

    # Also promote campus_admin if present
    c_admin = User.objects.filter(username='campus_admin').first()
    if c_admin:
        c_admin.is_staff = True
        c_admin.is_superuser = True
        c_admin.password = make_password('Admin@2026Pass!')
        c_admin.save()


def reverse_admin_user(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_admin_user, reverse_admin_user),
    ]
