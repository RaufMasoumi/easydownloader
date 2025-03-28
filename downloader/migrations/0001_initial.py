# Generated by Django 5.1.5 on 2025-01-26 10:17

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Content',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=300, null=True)),
                ('download_url', models.URLField(blank=True, null=True)),
                ('processed_at', models.DateTimeField(auto_now_add=True)),
                ('expiration_date', models.DateTimeField(blank=True)),
            ],
        ),
    ]
