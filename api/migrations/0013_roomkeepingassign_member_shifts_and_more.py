# Generated by Django 5.1.2 on 2025-02-20 10:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_profileshiftassign_shift_start_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='roomkeepingassign',
            name='member_shifts',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='room_keeping_assignments', to='api.profileshiftassign'),
        ),
        migrations.AlterField(
            model_name='roomkeepingassign',
            name='shift',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='room_keeping_assignments', to='api.shift'),
        ),
    ]
