from django.shortcuts import render
from .models import PersonaFisica, PersonaJuridica

def clientes_ruc_view(request):
    # Aquí puedes agregar lógica para pasar contexto a la plantilla, si es necesario
    personas_fisicas = PersonaFisica.objects.all()
    personas_juridicas = PersonaJuridica.objects.all()
    return render(request, 'clients/clientesruc.html', {'personas_fisicas': personas_fisicas, 'personas_juridicas': personas_juridicas})