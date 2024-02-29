from django.db import models


class Persona(models.Model):
    ruc = models.CharField(max_length=11, unique=True, help_text="RUC de 11 dígitos")
    telefono = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    class Meta:
        abstract = True

class PersonaFisica(Persona):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    cedula = models.CharField(max_length=8, unique=True, help_text="DNI de 8 dígitos")
    fecha_nacimiento = models.DateField()
    direccion = models.TextField()

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class PersonaJuridica(Persona):
    razon_social = models.CharField(max_length=150)
    direccion_fiscal = models.TextField()
    representante_legal = models.CharField(max_length=150)

    def __str__(self):
        return self.razon_social

