from django.urls import path
from . import views

urlpatterns = [
    path('api/status/<int:store_id>/', views.get_whatsapp_status, name='whatsapp_status'),
    path('webhook/<str:instance_name>/', views.whatsapp_webhook, name='whatsapp_webhook'),
]
