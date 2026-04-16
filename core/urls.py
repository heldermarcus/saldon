from django.urls import path
from . import views

urlpatterns = [
    path('', views.LandingPageView.as_view(), name='landing'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('onboarding/', views.onboarding_view, name='onboarding'),
    path('subscription/', views.subscription_view, name='subscription'),
    path('checkout/<str:plan>/', views.create_checkout, name='create_checkout'),
    path('webhook/abacatepay/', views.webhook_abacatepay, name='webhook_abacatepay'),
    # Configurações
    path('settings/', views.settings_view, name='settings'),
    path('settings/category/add/', views.category_create_api, name='category_create'),
    path('settings/category/<int:pk>/edit/', views.category_edit_api, name='category_edit'),
    path('settings/category/<int:pk>/delete/', views.category_delete_api, name='category_delete'),
]
