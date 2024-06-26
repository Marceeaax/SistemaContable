from django.db import models


class Persona(models.Model):
    ruc = models.CharField(max_length=11, unique=True)
    contrasena = models.CharField(max_length=25, default='', )
    vencimiento = models.CharField(max_length=10, default='', )
    telefono = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    class Meta:
        abstract = True

class PersonaFisica(Persona):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    cedula = models.CharField(max_length=8)
    fecha_nacimiento = models.DateField(null=True)
    direccion = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class PersonaJuridica(Persona):
    razon_social = models.CharField(max_length=150, blank=True)
    direccion_fiscal = models.TextField(blank=True)
    representante_legal = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return self.razon_social

