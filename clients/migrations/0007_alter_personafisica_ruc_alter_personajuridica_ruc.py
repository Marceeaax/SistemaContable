# Generated by Django 5.0.2 on 2024-03-05 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0006_alter_personafisica_cedula'),
    ]

    operations = [
        migrations.AlterField(
            model_name='personafisica',
            name='ruc',
            field=models.CharField(max_length=11, unique=True),
        ),
        migrations.AlterField(
            model_name='personajuridica',
            name='ruc',
            field=models.CharField(max_length=11, unique=True),
        ),
    ]