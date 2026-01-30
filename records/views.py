from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import HealthProfile, MedicalHistory, MedicalDocument
from .serializers import (
    HealthProfileSerializer,
    MedicalHistorySerializer,
    MedicalDocumentSerializer,
    MedicalDocumentUploadSerializer,
)


class HealthProfileView(generics.RetrieveUpdateAPIView):
    """Get or update patient's health profile."""
    
    serializer_class = HealthProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        # Get or create health profile for current user
        profile, created = HealthProfile.objects.get_or_create(
            patient=self.request.user
        )
        return profile


class MedicalHistoryListCreateView(generics.ListCreateAPIView):
    """List or create medical history entries."""
    
    serializer_class = MedicalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return MedicalHistory.objects.filter(patient=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(patient=self.request.user)


class MedicalHistoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a medical history entry."""
    
    serializer_class = MedicalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return MedicalHistory.objects.filter(patient=self.request.user)


class MedicalDocumentListView(generics.ListAPIView):
    """List patient's medical documents."""
    
    serializer_class = MedicalDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = MedicalDocument.objects.filter(patient=self.request.user)
        
        # Filter by document type
        doc_type = self.request.query_params.get('type')
        if doc_type:
            queryset = queryset.filter(document_type=doc_type)
        
        return queryset


class MedicalDocumentUploadView(generics.CreateAPIView):
    """Upload a medical document."""
    
    serializer_class = MedicalDocumentUploadSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def perform_create(self, serializer):
        serializer.save(patient=self.request.user)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save(patient=request.user)
        
        return Response({
            'message': 'Document uploaded successfully',
            'document': MedicalDocumentSerializer(document, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)


class MedicalDocumentDetailView(generics.RetrieveDestroyAPIView):
    """Get or delete a medical document."""
    
    serializer_class = MedicalDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return MedicalDocument.objects.filter(patient=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Delete the actual file
        if instance.file:
            instance.file.delete(save=False)
        
        self.perform_destroy(instance)
        
        return Response({
            'message': 'Document deleted successfully'
        }, status=status.HTTP_200_OK)


class PatientRecordsView(generics.RetrieveAPIView):
    """
    Doctor views patient records during consultation.
    Only accessible during active appointment.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, patient_id):
        # Only doctors can access
        if request.user.user_type != 'doctor':
            return Response(
                {'error': 'Only doctors can view patient records'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if doctor has an active appointment with this patient
        from appointments.models import Appointment
        has_appointment = Appointment.objects.filter(
            doctor=request.user.doctor_profile,
            patient_id=patient_id,
            status__in=['confirmed', 'in_progress']
        ).exists()
        
        if not has_appointment:
            return Response(
                {'error': 'You can only view records for patients with active appointments'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get patient data
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            patient = User.objects.get(id=patient_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Patient not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get health profile
        health_profile = None
        try:
            health_profile = HealthProfileSerializer(patient.health_profile).data
        except HealthProfile.DoesNotExist:
            pass
        
        # Get medical history
        medical_history = MedicalHistorySerializer(
            patient.medical_history.all()[:10],
            many=True
        ).data
        
        # Get recent documents
        documents = MedicalDocumentSerializer(
            patient.medical_documents.all()[:10],
            many=True,
            context={'request': request}
        ).data
        
        return Response({
            'patient': {
                'id': patient.id,
                'name': patient.full_name,
                'email': patient.email,
                'phone': patient.phone,
                'date_of_birth': patient.date_of_birth,
                'gender': patient.gender,
            },
            'health_profile': health_profile,
            'medical_history': medical_history,
            'documents': documents,
        })