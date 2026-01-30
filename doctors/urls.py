from django.urls import path
from .views import (
    SpecializationListView,
    DoctorListView,
    DoctorDetailView,
    DoctorSlotsView,
    MyAvailabilityView,
    GenerateSlotsView,
    DeleteAvailabilityView,
)

urlpatterns = [
    # Specializations
    path('specializations/', SpecializationListView.as_view(), name='specialization-list'),
    
    # Doctors
    path('', DoctorListView.as_view(), name='doctor-list'),
    path('<int:pk>/', DoctorDetailView.as_view(), name='doctor-detail'),
    path('<int:doctor_id>/slots/', DoctorSlotsView.as_view(), name='doctor-slots'),
    
    # Current doctor
    path('my/availability/', MyAvailabilityView.as_view(), name='my-availability'),
    path('my/availability/<int:pk>/', DeleteAvailabilityView.as_view(), name='delete-availability'),
    path('my/generate-slots/', GenerateSlotsView.as_view(), name='generate-slots'),
]