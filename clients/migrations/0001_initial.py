# Generated by Django 5.0.2 on 2024-03-01 19:12

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PersonaFisica',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ruc', models.CharField(help_text='RUC de 11 dígitos', max_length=11, unique=True)),
                ('telefono', models.CharField(blank=True, max_length=15, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('nombre', models.CharField(max_length=100)),
                ('apellido', models.CharField(max_length=100)),
                ('cedula', models.CharField(help_text='DNI de 8 dígitos', max_length=8, unique=True)),
                ('fecha_nacimiento', models.DateField()),
                ('direccion', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PersonaJuridica',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ruc', models.CharField(help_text='RUC de 11 dígitos', max_length=11, unique=True)),
                ('telefono', models.CharField(blank=True, max_length=15, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('razon_social', models.CharField(max_length=150)),
                ('direccion_fiscal', models.TextField()),
                ('representante_legal', models.CharField(max_length=150)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
