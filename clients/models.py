from django.db import models

class Cliente(models.Model):
    # Definición de tipos de cliente
    PERSONA_FISICA = 'FISICA'
    PERSONA_JURIDICA = 'JURIDICA'
    TIPOS_DE_CLIENTE = [
        (PERSONA_FISICA, 'Persona Física'),
        (PERSONA_JURIDICA, 'Persona Jurídica'),
    ]

    # Campos comunes
    tipo_cliente = models.CharField(
        max_length=10,
        choices=TIPOS_DE_CLIENTE,
        default=PERSONA_FISICA,
    )
    nombre = models.CharField(max_length=200)
    direccion = models.TextField()
    telefono = models.CharField(max_length=15)
    correo = models.EmailField()

    # Campos específicos para Persona Física
    primer_nombre = models.CharField(max_length=100, blank=True, null=True)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    cedula = models.CharField(max_length=15, blank=True, null=True)

    # Campos específicos para Persona Jurídica
    razon_social = models.CharField(max_length=200, blank=True, null=True)
    ruc = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        # Aquí puedes agregar lógica para asegurarte de que los campos se rellenen adecuadamente según el tipo de cliente
        super().save(*args, **kwargs)
