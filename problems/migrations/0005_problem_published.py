# Generated by Django 5.0.7 on 2024-09-08 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0004_alter_valuefield_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='published',
            field=models.BooleanField(default=True),
        ),
    ]
