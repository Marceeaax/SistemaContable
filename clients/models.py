from django.db import models

class PersonaFisica(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=8, unique=True)  # Suponiendo DNI de 8 dígitos
    fecha_nacimiento = models.DateField()
    direccion = models.TextField()
    telefono = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class PersonaJuridica(models.Model):
    razon_social = models.CharField(max_length=150)
    ruc = models.CharField(max_length=11, unique=True)  # Suponiendo RUC de 11 dígitos
    direccion_fiscal = models.TextField()
    telefono = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    representante_legal = models.ForeignKey(PersonaFisica, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.razon_social
