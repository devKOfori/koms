# Generated by Django 5.1.2 on 2025-02-19 17:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_profileshiftassign_shift_end_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='profileshiftassign',
            name='shift_start_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
