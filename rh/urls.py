from django.urls import path
from . import views

app_name = 'rh'

urlpatterns = [
    path('dashboard/', views.rh_dashboard, name='dashboard'),
    path('funcionarios/', views.employee_list, name='employee_list'),
    path('funcionarios/novo/', views.employee_create, name='employee_create'),
    path('funcionarios/<int:pk>/editar/', views.employee_update, name='employee_update'),
]
