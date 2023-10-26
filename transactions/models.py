from django.db import models
from clients.models import PersonaFisica, PersonaJuridica

class Autofactura(models.Model):
    cliente_persona_fisica = models.ForeignKey(
        PersonaFisica, 
        on_delete=models.CASCADE, 
        related_name="autofacturas", 
        null=True, 
        blank=True
    )
    cliente_persona_juridica = models.ForeignKey(
        PersonaJuridica, 
        on_delete=models.CASCADE, 
        related_name="autofacturas", 
        null=True, 
        blank=True
    )
    # Otros campos...

class BoletaDeVenta(models.Model):
    cliente_persona_fisica = models.ForeignKey(
        PersonaFisica, 
        on_delete=models.CASCADE, 
        related_name="boletas_de_venta", 
        null=True, 
        blank=True
    )
    cliente_persona_juridica = models.ForeignKey(
        PersonaJuridica, 
        on_delete=models.CASCADE, 
        related_name="boletas_de_venta", 
        null=True, 
        blank=True
    )
    # Otros campos...

class Factura(models.Model):
    cliente_persona_fisica = models.ForeignKey(
        PersonaFisica, 
        on_delete=models.CASCADE, 
        related_name="facturas", 
        null=True, 
        blank=True
    )
    cliente_persona_juridica = models.ForeignKey(
        PersonaJuridica, 
        on_delete=models.CASCADE, 
        related_name="facturas", 
        null=True, 
        blank=True
    )
    # Otros campos...
