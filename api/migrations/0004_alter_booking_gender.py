# Generated by Django 5.1.2 on 2024-12-29 15:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_paymentmethod_remove_room_room_status_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='gender',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.gender'),
        ),
    ]
