# Generated by Django 5.1.2 on 2025-02-20 10:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_roomkeepingassign_member_shifts_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='roomkeepingassign',
            name='member_shifts',
        ),
        migrations.AddField(
            model_name='roomkeepingassign',
            name='member_shift',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='room_keeping_assignments', to='api.profileshiftassign'),
        ),
    ]
