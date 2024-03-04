from django.shortcuts import render, redirect
from django.urls import reverse
from .models import PersonaFisica, PersonaJuridica
from .forms import PersonaFisicaForm, PersonaJuridicaForm
from django.contrib import messages

def clientes_ruc_view(request):
    form_persona_fisica = PersonaFisicaForm()
    form_persona_juridica = PersonaJuridicaForm()
    personas_fisicas = PersonaFisica.objects.all()
    personas_juridicas = PersonaJuridica.objects.all()
    
    # Comprueba si se ha establecido el indicador para mostrar el modal
    show_modal = request.session.pop('show_modal', False)
    form_errors = messages.get_messages(request)
    
    return render(request, 'clients/clientesruc.html', {
        'personas_fisicas': personas_fisicas, 
        'personas_juridicas': personas_juridicas,
        'form_persona_fisica': form_persona_fisica,
        'form_persona_juridica': form_persona_juridica,
        'show_modal': show_modal,  # Añade esta línea para controlar el modal
        'form_errors': form_errors,  # Añade esta línea para pasar los errores del formulario
    })




def crear_cliente(request):
    print("Iniciar vista crear_cliente")
    # Inicializa los formularios fuera del if para poder reutilizarlos
    form_persona_fisica = PersonaFisicaForm()
    form_persona_juridica = PersonaJuridicaForm()

    if request.method == 'POST':
        print("Se recibe un post")
        if 'form_type' in request.POST and request.POST['form_type'] == 'fisica':
            print("Si se trata de un form de persona fisica")
            form_persona_fisica = PersonaFisicaForm(request.POST)
            if form_persona_fisica.is_valid():
                messages.error(request, "Por favor, corrija los errores abajo.")
                for error in form_persona_fisica.errors.values():
                    messages.error(request, error)
                request.session['show_modal'] = True
                return redirect('clients:clientesruc')
            else:
                # Si el formulario no es válido, asegúrate de pasar la instancia con errores al contexto.
                print("si el form es invalido")
                context = {'form_persona_fisica': form_persona_fisica}
                request.session['show_modal'] = True
                return render(request, 'clients/clientesruc.html', context)

        elif 'form_type' in request.POST and request.POST['form_type'] == 'juridica':
            form_persona_juridica = PersonaJuridicaForm(request.POST)
            if form_persona_juridica.is_valid():
                form_persona_juridica.save()
                return redirect(reverse('clients:clientesruc'))
            else:
                # Lo mismo para el formulario de persona jurídica
                context = {'form_persona_juridica': form_persona_juridica}
                return render(request, 'clients/clientesruc.html', context)

    # Si no es un POST, renderiza la plantilla con el contexto de formularios vacíos o con errores.
    context = {
        'form_persona_fisica': form_persona_fisica,
        'form_persona_juridica': form_persona_juridica,
    }
    print("Renderizar página con formularios")  # Impresión de depuración
    return render(request, 'clients/clientesruc.html', context)

