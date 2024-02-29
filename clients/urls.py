from django.urls import path
from .views import clientes_ruc_view

urlpatterns = [
    path('clientesruc/', clientes_ruc_view, name='clientesruc'),
]
