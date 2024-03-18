from django.urls import path
from .views import clientes_ruc_view, crear_cliente, editar_cliente, datos_faltantes

urlpatterns = [
    path('clientesruc/', clientes_ruc_view, name='clientesruc'),
    path('crear/', crear_cliente, name='crear_cliente'),
    path('editar/', editar_cliente, name='editar_cliente'),
    path('datos-faltantes/<str:ruc>/', datos_faltantes, name='datos_faltantes')
]
