from django.urls import path
from .views import (
    HealthProfileView,
    MedicalHistoryListCreateView,
    MedicalHistoryDetailView,
    MedicalDocumentListView,
    MedicalDocumentUploadView,
    MedicalDocumentDetailView,
    PatientRecordsView,
)

urlpatterns = [
    # Health Profile
    path('profile/', HealthProfileView.as_view(), name='health-profile'),
    
    # Medical History
    path('history/', MedicalHistoryListCreateView.as_view(), name='medical-history-list'),
    path('history/<int:pk>/', MedicalHistoryDetailView.as_view(), name='medical-history-detail'),
    
    # Documents
    path('documents/', MedicalDocumentListView.as_view(), name='document-list'),
    path('documents/upload/', MedicalDocumentUploadView.as_view(), name='document-upload'),
    path('documents/<int:pk>/', MedicalDocumentDetailView.as_view(), name='document-detail'),
    
    # Doctor access to patient records
    path('patient/<int:patient_id>/', PatientRecordsView.as_view(), name='patient-records'),
]