# Generated by Django 5.0.2 on 2024-03-19 13:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0011_alter_personafisica_fecha_nacimiento'),
    ]

    operations = [
        migrations.AlterField(
            model_name='personafisica',
            name='fecha_nacimiento',
            field=models.DateField(null=True),
        ),
    ]
