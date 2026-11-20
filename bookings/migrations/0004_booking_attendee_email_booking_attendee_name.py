from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0003_booking_checkout_request_id_booking_mpesa_receipt_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='attendee_email',
            field=models.EmailField(blank=True, default='', max_length=254),
        ),
        migrations.AddField(
            model_name='booking',
            name='attendee_name',
            field=models.CharField(blank=True, default='', max_length=150),
        ),
    ]
