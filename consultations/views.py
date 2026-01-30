from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from notifications.services import EmailService
from appointments.models import Appointment
from .models import Consultation, Prescription, PrescriptionItem
from .serializers import (
    ConsultationSerializer,
    ConsultationUpdateSerializer,
    ConsultationListSerializer,
    PrescriptionSerializer,
    CreatePrescriptionSerializer,
)


class ConsultationDetailView(generics.RetrieveAPIView):
    """Get consultation details for an appointment."""
    
    serializer_class = ConsultationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        appointment_id = self.kwargs.get('appointment_id')
        user = self.request.user
        
        # Get appointment
        if user.user_type == 'patient':
            appointment = get_object_or_404(Appointment, pk=appointment_id, patient=user)
        elif user.user_type == 'doctor':
            appointment = get_object_or_404(Appointment, pk=appointment_id, doctor=user.doctor_profile)
        else:
            appointment = get_object_or_404(Appointment, pk=appointment_id)
        
        # Get or create consultation
        consultation, created = Consultation.objects.get_or_create(
            appointment=appointment
        )
        
        return consultation


class ConsultationUpdateView(generics.UpdateAPIView):
    """Update consultation notes (doctor only)."""
    
    serializer_class = ConsultationUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        appointment_id = self.kwargs.get('appointment_id')
        user = self.request.user
        
        if user.user_type != 'doctor':
            self.permission_denied(self.request, message="Only doctors can update consultations")
        
        appointment = get_object_or_404(Appointment, pk=appointment_id, doctor=user.doctor_profile)
        
        consultation, created = Consultation.objects.get_or_create(
            appointment=appointment
        )
        
        return consultation
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'message': 'Consultation updated successfully',
            'consultation': ConsultationSerializer(instance).data
        })


class MyConsultationsView(generics.ListAPIView):
    """List consultations for current user."""
    
    serializer_class = ConsultationListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'patient':
            return Consultation.objects.filter(
                appointment__patient=user
            ).select_related('appointment', 'appointment__doctor__user')
        elif user.user_type == 'doctor':
            return Consultation.objects.filter(
                appointment__doctor=user.doctor_profile
            ).select_related('appointment', 'appointment__patient')
        else:
            return Consultation.objects.all()


class CreatePrescriptionView(APIView):
    """Create a prescription for a consultation (doctor only)."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, appointment_id):
        user = request.user
        
        if user.user_type != 'doctor':
            return Response(
                {'error': 'Only doctors can create prescriptions'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        appointment = get_object_or_404(
            Appointment,
            pk=appointment_id,
            doctor=user.doctor_profile
        )
        
        consultation, _ = Consultation.objects.get_or_create(appointment=appointment)
        
        serializer = CreatePrescriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        valid_until = timezone.now().date() + timedelta(days=data.get('valid_days', 30))
        
        prescription = Prescription.objects.create(
            consultation=consultation,
            diagnosis=data.get('diagnosis', ''),
            notes=data.get('notes', ''),
            valid_until=valid_until
        )
        
        for item_data in data['items']:
            PrescriptionItem.objects.create(
                prescription=prescription,
                **item_data
            )
        
        # Send prescription notification
        EmailService.send_prescription_ready(prescription)
        
        return Response({
            'message': 'Prescription created successfully',
            'prescription': PrescriptionSerializer(prescription).data
        }, status=status.HTTP_201_CREATED)

class PrescriptionListView(generics.ListAPIView):
    """List prescriptions for current user."""
    
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'patient':
            return Prescription.objects.filter(
                consultation__appointment__patient=user
            ).select_related('consultation__appointment')
        elif user.user_type == 'doctor':
            return Prescription.objects.filter(
                consultation__appointment__doctor=user.doctor_profile
            ).select_related('consultation__appointment')
        else:
            return Prescription.objects.all()


class PrescriptionDetailView(generics.RetrieveAPIView):
    """Get prescription details."""
    
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'patient':
            return Prescription.objects.filter(
                consultation__appointment__patient=user
            )
        elif user.user_type == 'doctor':
            return Prescription.objects.filter(
                consultation__appointment__doctor=user.doctor_profile
            )
        else:
            return Prescription.objects.all()


class StartConsultationView(APIView):
    """Start a consultation (set start time)."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, appointment_id):
        user = request.user
        
        if user.user_type != 'doctor':
            return Response(
                {'error': 'Only doctors can start consultations'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        appointment = get_object_or_404(
            Appointment,
            pk=appointment_id,
            doctor=user.doctor_profile
        )
        
        consultation, _ = Consultation.objects.get_or_create(appointment=appointment)
        
        if consultation.started_at:
            return Response(
                {'error': 'Consultation already started'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consultation.started_at = timezone.now()
        consultation.save()
        
        # Update appointment status
        appointment.status = 'in_progress'
        appointment.save()
        
        return Response({
            'message': 'Consultation started',
            'started_at': consultation.started_at
        })


class EndConsultationView(APIView):
    """End a consultation (set end time)."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, appointment_id):
        user = request.user
        
        if user.user_type != 'doctor':
            return Response(
                {'error': 'Only doctors can end consultations'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        appointment = get_object_or_404(
            Appointment,
            pk=appointment_id,
            doctor=user.doctor_profile
        )
        
        consultation, _ = Consultation.objects.get_or_create(appointment=appointment)
        
        if consultation.ended_at:
            return Response(
                {'error': 'Consultation already ended'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consultation.ended_at = timezone.now()
        consultation.save()
        
        appointment.status = 'completed'
        appointment.save()
        
        # Send consultation completed email
        EmailService.send_consultation_completed(appointment)
        
        return Response({
            'message': 'Consultation ended',
            'ended_at': consultation.ended_at,
            'duration_minutes': consultation.duration_minutes
        })  
