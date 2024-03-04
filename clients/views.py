from django.shortcuts import render, redirect
from django.urls import reverse
from .models import PersonaFisica, PersonaJuridica
from .forms import PersonaFisicaForm, PersonaJuridicaForm
from django.contrib import messages

def clientes_ruc_view(request):
    form_persona_fisica = PersonaFisicaForm(request.session.pop('form_data', None) if request.session.get('form_type') == 'fisica' else None)
    form_persona_juridica = PersonaJuridicaForm(request.session.pop('form_data', None) if request.session.get('form_type') == 'juridica' else None)
    
    personas_fisicas = PersonaFisica.objects.all()
    personas_juridicas = PersonaJuridica.objects.all()
    
    return render(request, 'clients/clientesruc.html', {
        'personas_fisicas': personas_fisicas,
        'personas_juridicas': personas_juridicas,
        'form_persona_fisica': form_persona_fisica,
        'form_persona_juridica': form_persona_juridica,
        'show_modal': 'form_type' in request.session,
    })




def crear_cliente(request):
    if request.method == 'POST':
        form_type = request.POST.get('form_type', None)
        if form_type == 'fisica':
            form = PersonaFisicaForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('clients:clientesruc')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                request.session['form_data'] = request.POST
                request.session['form_type'] = 'fisica'
                return redirect('clients:clientesruc')

        elif form_type == 'juridica':
            form = PersonaJuridicaForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('clients:clientesruc')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                request.session['form_data'] = request.POST
                request.session['form_type'] = 'juridica'
                return redirect('clients:clientesruc')

    return redirect('clients:clientesruc')