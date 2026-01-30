# landing/urls.py
from django.urls import path
from . import views

app_name = 'landing'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('services/', views.services, name='services'),
    path('service-details/', views.service_details, name='service_details'),
    path('service-details/<int:service_id>/', views.service_details, name='service_details_dynamic'),

    path('team/', views.team, name='team'),
    path('team-details/', views.team_details, name='team_details'),
    path('appointment/', views.appointment, name='appointment'),
    path('faq/', views.faq, name='faq'),

]