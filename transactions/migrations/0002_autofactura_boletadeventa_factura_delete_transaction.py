# Generated by Django 5.0.2 on 2024-03-01 19:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0001_initial'),
        ('transactions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Autofactura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cliente_persona_fisica', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='autofacturas', to='clients.personafisica')),
                ('cliente_persona_juridica', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='autofacturas', to='clients.personajuridica')),
            ],
        ),
        migrations.CreateModel(
            name='BoletaDeVenta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cliente_persona_fisica', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='boletas_de_venta', to='clients.personafisica')),
                ('cliente_persona_juridica', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='boletas_de_venta', to='clients.personajuridica')),
            ],
        ),
        migrations.CreateModel(
            name='Factura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cliente_persona_fisica', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='facturas', to='clients.personafisica')),
                ('cliente_persona_juridica', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='facturas', to='clients.personajuridica')),
            ],
        ),
        migrations.DeleteModel(
            name='Transaction',
        ),
    ]
