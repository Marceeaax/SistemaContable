# Generated by Django 5.0.2 on 2024-03-19 10:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0008_alter_personafisica_direccion_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='personajuridica',
            name='direccion_fiscal',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='personajuridica',
            name='representante_legal',
            field=models.CharField(blank=True, max_length=150),
        ),
    ]
