# Generated by Django 5.1.2 on 2025-02-19 17:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_remove_processroomkeeping_room_state_trans_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profileshiftassign',
            name='shift_end_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
