from django.shortcuts import render
from django.http import JsonResponse
from .models import PersonaFisica, PersonaJuridica
from .forms import PersonaFisicaForm, PersonaJuridicaForm

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

def calcular_vencimiento_ruc(ruc):
    ultimo_digito = int(ruc[-3])
    vencimiento = ultimo_digito * 2 + 7
    return str(vencimiento)

def crear_cliente(request):
    if request.method == 'POST':
        form_type = request.POST.get('form_type', None)
        print(form_type)
        if form_type == 'fisica':
            form = PersonaFisicaForm(request.POST)
        elif form_type == 'juridica':
            form = PersonaJuridicaForm(request.POST)
        else:
            # Devuelve un error si no se especifica el tipo de formulario
            return JsonResponse({'success': False, 'message': 'Tipo de formulario no especificado'}, status=400)

        if form.is_valid():
            cliente = form.save(commit=False)
            if form_type == 'fisica':
                ruc = form.cleaned_data['ruc']
                vencimiento_ruc = calcular_vencimiento_ruc(ruc)
                cliente.vencimiento = vencimiento_ruc
            cliente.save()
            return JsonResponse({'success': True, 'message': 'Cliente creado con éxito'})
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'errors': errors}, status=400)
    else:
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

def editar_cliente(request):
    if request.method == 'POST':
        cliente_id = request.POST.get('clientId', None)
        form_type = request.POST.get('form_type', None)
        
        if form_type == 'fisica':
            cliente = PersonaFisica.objects.get(pk=cliente_id)
            form = PersonaFisicaForm(request.POST, instance=cliente)
        elif form_type == 'juridica':
            cliente = PersonaJuridica.objects.get(pk=cliente_id)
            form = PersonaJuridicaForm(request.POST, instance=cliente)
        else:
            return JsonResponse({'success': False, 'message': 'Tipo de formulario no especificado'}, status=400)

        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Cliente actualizado con éxito'})
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'errors': errors}, status=400)
    else:
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
