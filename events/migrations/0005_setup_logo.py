import shutil
from pathlib import Path
from django.conf import settings
from django.db import migrations


def copy_clean_logo(apps, schema_editor):
    src = settings.MEDIA_ROOT / 'logo' / 'EventHub Campus Edition Logo.png'
    if src.exists():
        dst_media = settings.MEDIA_ROOT / 'logo' / 'logo.png'
        shutil.copy2(src, dst_media)

        static_img_dir = settings.BASE_DIR / 'static' / 'images'
        static_img_dir.mkdir(parents=True, exist_ok=True)
        dst_static = static_img_dir / 'logo.png'
        shutil.copy2(src, dst_static)


def reverse_logo(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0004_update_banner_extensions'),
    ]

    operations = [
        migrations.RunPython(copy_clean_logo, reverse_logo),
    ]
