from django.urls import path
from .views import clientes_ruc_view, crear_cliente

urlpatterns = [
    path('clientesruc/', clientes_ruc_view, name='clientesruc'),
    path('crear/', crear_cliente, name='crear_cliente'),
]
