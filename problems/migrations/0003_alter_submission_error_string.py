# Generated by Django 5.0.7 on 2024-08-25 14:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0002_submission_reject_details'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='error_string',
            field=models.TextField(blank=True, null=True),
        ),
    ]
