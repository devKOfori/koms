# Generated by Django 5.1.2 on 2025-03-15 10:52

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0024_alter_paymentstatus_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('country_code', models.CharField(blank=True, max_length=255, null=True)),
                ('abbr', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'verbose_name': 'Country',
                'verbose_name_plural': 'Countries',
                'db_table': 'country',
            },
        ),
        migrations.CreateModel(
            name='IdentificationType',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'Identification Type',
                'verbose_name_plural': 'Identification Types',
                'db_table': 'identificationtype',
            },
        ),
        migrations.AddField(
            model_name='guest',
            name='country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.country'),
        ),
        migrations.AddField(
            model_name='guest',
            name='identification_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.identificationtype'),
        ),
    ]
