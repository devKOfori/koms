# Generated by Django 5.1.2 on 2025-03-31 04:41

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0026_booking_note'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='checkin',
            options={'verbose_name': 'Check-In', 'verbose_name_plural': 'Check-Ins'},
        ),
        migrations.RemoveField(
            model_name='checkin',
            name='receipt',
        ),
        migrations.RemoveField(
            model_name='checkin',
            name='security_deposit',
        ),
        migrations.AddField(
            model_name='checkin',
            name='total_payment',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=11, null=True),
        ),
        migrations.AlterField(
            model_name='checkin',
            name='booking_code',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='checkin',
            name='number_of_guests',
            field=models.PositiveIntegerField(blank=True, default=1, null=True),
        ),
        migrations.AlterModelTable(
            name='checkin',
            table='checkin',
        ),
        migrations.CreateModel(
            name='CheckinPayment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=11)),
                ('payment_timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('check_in', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='api.checkin')),
                ('receipt', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.receipt')),
                ('received_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.profile')),
            ],
            options={
                'verbose_name': 'Check-In Payment',
                'verbose_name_plural': 'Check-In Payments',
                'db_table': 'checkinpayment',
            },
        ),
    ]
