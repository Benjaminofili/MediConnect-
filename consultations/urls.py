from django.urls import path
from .views import (
    ConsultationDetailView,
    ConsultationUpdateView,
    MyConsultationsView,
    CreatePrescriptionView,
    PrescriptionListView,
    PrescriptionDetailView,
    StartConsultationView,
    EndConsultationView,
)

urlpatterns = [
    # My consultations
    path('', MyConsultationsView.as_view(), name='my-consultations'),
    
    # Consultation by appointment
    path('<int:appointment_id>/', ConsultationDetailView.as_view(), name='consultation-detail'),
    path('<int:appointment_id>/update/', ConsultationUpdateView.as_view(), name='consultation-update'),
    path('<int:appointment_id>/start/', StartConsultationView.as_view(), name='start-consultation'),
    path('<int:appointment_id>/end/', EndConsultationView.as_view(), name='end-consultation'),
    path('<int:appointment_id>/prescription/', CreatePrescriptionView.as_view(), name='create-prescription'),
    
    # Prescriptions
    path('prescriptions/', PrescriptionListView.as_view(), name='prescription-list'),
    path('prescriptions/<int:pk>/', PrescriptionDetailView.as_view(), name='prescription-detail'),
]