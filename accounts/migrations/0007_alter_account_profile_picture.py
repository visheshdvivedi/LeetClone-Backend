# Generated by Django 5.0.7 on 2024-08-30 07:51

import accounts.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_account_profile_picture'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to=accounts.models.path_and_rename),
        ),
    ]
