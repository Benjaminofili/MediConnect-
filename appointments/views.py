import requests
import datetime
from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from notifications.services import EmailService

from doctors.models import TimeSlot
from .models import Appointment
from .serializers import (
    AppointmentListSerializer,
    AppointmentDetailSerializer,
    BookAppointmentSerializer,
    CancelAppointmentSerializer,
    RescheduleAppointmentSerializer,
)


class BookAppointmentView(generics.CreateAPIView):
    """Book a new appointment"""
    
    serializer_class = BookAppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if request.user.user_type != 'patient':
            return Response(
                {'error': 'Only patients can book appointments'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()
        
        # Send confirmation emails
        EmailService.send_appointment_confirmation(appointment)
        EmailService.send_appointment_confirmation_to_doctor(appointment)
        
        return Response({
            'message': 'Appointment booked successfully',
            'appointment': AppointmentDetailSerializer(appointment).data
        }, status=status.HTTP_201_CREATED)

class MyAppointmentsView(generics.ListAPIView):
    """List appointments for current user"""
    
    serializer_class = AppointmentListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'patient':
            queryset = Appointment.objects.filter(patient=user)
        elif user.user_type == 'doctor':
            queryset = Appointment.objects.filter(doctor=user.doctor_profile)
        else:
            queryset = Appointment.objects.all()
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        return queryset.select_related('patient', 'doctor__user', 'doctor__specialization')


class UpcomingAppointmentsView(generics.ListAPIView):
    """List upcoming appointments for current user"""
    
    serializer_class = AppointmentListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        today = timezone.now().date()
        
        if user.user_type == 'patient':
            queryset = Appointment.objects.filter(patient=user)
        elif user.user_type == 'doctor':
            queryset = Appointment.objects.filter(doctor=user.doctor_profile)
        else:
            queryset = Appointment.objects.all()
        
        return queryset.filter(
            date__gte=today,
            status__in=['pending', 'confirmed']
        ).select_related('patient', 'doctor__user', 'doctor__specialization')


class AppointmentDetailView(generics.RetrieveAPIView):
    """Get appointment details"""
    
    serializer_class = AppointmentDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'patient':
            return Appointment.objects.filter(patient=user)
        elif user.user_type == 'doctor':
            return Appointment.objects.filter(doctor=user.doctor_profile)
        else:
            return Appointment.objects.all()


class CancelAppointmentView(APIView):
    """Cancel an appointment"""
    
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        
        if user.user_type == 'patient':
            appointment = get_object_or_404(Appointment, pk=pk, patient=user)
            cancelled_by_type = 'patient'
        elif user.user_type == 'doctor':
            appointment = get_object_or_404(Appointment, pk=pk, doctor=user.doctor_profile)
            cancelled_by_type = 'doctor'
        else:
            appointment = get_object_or_404(Appointment, pk=pk)
            cancelled_by_type = 'admin'
        
        serializer = CancelAppointmentSerializer(
            data=request.data,
            context={'appointment': appointment}
        )
        serializer.is_valid(raise_exception=True)
        
        appointment.status = 'cancelled'
        appointment.cancellation_reason = serializer.validated_data['cancellation_reason']
        appointment.cancelled_by = user
        appointment.cancelled_at = timezone.now()
        appointment.save()
        
        appointment.time_slot.status = 'available'
        appointment.time_slot.save()
        
        # Send cancellation email
        EmailService.send_appointment_cancellation(appointment, cancelled_by_type)
        
        return Response({
            'message': 'Appointment cancelled successfully',
            'appointment': AppointmentDetailSerializer(appointment).data
        })

class RescheduleAppointmentView(APIView):
    """Reschedule an appointment"""
    
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        
        # Only patients can reschedule
        if user.user_type != 'patient':
            return Response(
                {'error': 'Only patients can reschedule appointments'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        appointment = get_object_or_404(Appointment, pk=pk, patient=user)
        
        # Validate rescheduling
        serializer = RescheduleAppointmentSerializer(
            data=request.data,
            context={'appointment': appointment}
        )
        serializer.is_valid(raise_exception=True)
        
        # Get new slot
        new_slot = TimeSlot.objects.get(id=serializer.validated_data['new_time_slot_id'])
        old_slot = appointment.time_slot
        
        # Update appointment
        appointment.time_slot = new_slot
        appointment.date = new_slot.date
        appointment.start_time = new_slot.start_time
        appointment.end_time = new_slot.end_time
        appointment.reschedule_count += 1
        appointment.save()
        
        # Update slots
        old_slot.status = 'available'
        old_slot.save()
        
        new_slot.status = 'booked'
        new_slot.save()
        
        return Response({
            'message': 'Appointment rescheduled successfully',
            'appointment': AppointmentDetailSerializer(appointment).data
        })


class JoinConsultationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        user = request.user
        
        # 1. Get Appointment
        if user.user_type == 'patient':
            appointment = get_object_or_404(Appointment, pk=pk, patient=user)
        elif user.user_type == 'doctor':
            appointment = get_object_or_404(Appointment, pk=pk, doctor=user.doctor_profile)
        else:
            appointment = get_object_or_404(Appointment, pk=pk)

        # 2. Ensure room exists (now centralized in model)
        if not appointment.video_room_url or (user.user_type == 'doctor' and not getattr(appointment, "video_host_url", "")):
            try:
                appointment.generate_video_room()
                appointment.save(update_fields=["video_room_url", "video_host_url", "video_room_id"])
            except Exception as e:
                return Response({'error': str(e)}, status=500)

        # 3. Return the correct URL based on user type
        host_url = getattr(appointment, "video_host_url", "") or appointment.video_room_url
        final_url = host_url if user.user_type == 'doctor' else appointment.video_room_url
        
        return Response({
            'video_room_url': final_url
        })

class CompleteAppointmentView(APIView):
    """Mark appointment as completed (Doctor only)"""
    
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        
        # Only doctors can complete appointments
        if user.user_type != 'doctor':
            return Response(
                {'error': 'Only doctors can complete appointments'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        appointment = get_object_or_404(Appointment, pk=pk, doctor=user.doctor_profile)
        
        if appointment.status not in ['confirmed', 'in_progress']:
            return Response(
                {'error': 'Only confirmed or in-progress appointments can be completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.status = 'completed'
        appointment.save()
        
        # Update doctor's total consultations
        doctor_profile = appointment.doctor
        doctor_profile.total_reviews += 1
        doctor_profile.save()
        
        return Response({
            'message': 'Appointment completed successfully',
            'appointment': AppointmentDetailSerializer(appointment).data
        })


class DoctorTodayAppointmentsView(generics.ListAPIView):
    """List today's appointments for doctor"""
    
    serializer_class = AppointmentListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.user_type != 'doctor':
            return Appointment.objects.none()
        
        today = timezone.now().date()
        
        return Appointment.objects.filter(
            doctor=user.doctor_profile,
            date=today,
            status__in=['confirmed', 'in_progress']
        ).select_related('patient', 'doctor__user').order_by('start_time')