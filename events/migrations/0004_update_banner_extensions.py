from django.db import migrations


def update_banner_extensions(apps, schema_editor):
    Event = apps.get_model('events', 'Event')
    for event in Event.objects.all():
        if event.banner:
            banner_str = str(event.banner)
            if banner_str.endswith('.jpg') or banner_str.endswith('.jpeg'):
                new_banner = banner_str.rsplit('.', 1)[0] + '.png'
                event.banner = new_banner
                event.save(update_fields=['banner'])


def reverse_banner_extensions(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0003_merge_20261120_1805'),
    ]

    operations = [
        migrations.RunPython(update_banner_extensions, reverse_banner_extensions),
    ]
