from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from accounts.models import DoctorProfile
from .models import Specialization, Availability, TimeSlot
from .serializers import (
    SpecializationSerializer, DoctorListSerializer,
    DoctorDetailSerializer, AvailabilitySerializer, TimeSlotSerializer,
)
from .services import generate_time_slots


class SpecializationListView(generics.ListAPIView):
    queryset = Specialization.objects.filter(is_active=True)
    serializer_class = SpecializationSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class DoctorListView(generics.ListAPIView):
    serializer_class = DoctorListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = DoctorProfile.objects.filter(
            verification_status='verified'
        ).select_related('user', 'specialization').order_by('id')
        
        # Filter by specialization
        specialization = self.request.query_params.get('specialization')
        if specialization:
            queryset = queryset.filter(specialization_id=specialization)
        
        # Filter by min experience
        min_experience = self.request.query_params.get('min_experience')
        if min_experience:
            queryset = queryset.filter(experience_years__gte=min_experience)
        
        # Filter by max fee
        max_fee = self.request.query_params.get('max_fee')
        if max_fee:
            queryset = queryset.filter(consultation_fee__lte=max_fee)
        
        return queryset


class DoctorDetailView(generics.RetrieveAPIView):
    serializer_class = DoctorDetailSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return DoctorProfile.objects.filter(
            verification_status='verified'
        ).select_related('user', 'specialization')


class DoctorSlotsView(generics.ListAPIView):
    serializer_class = TimeSlotSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        doctor_id = self.kwargs.get('doctor_id')
        
        queryset = TimeSlot.objects.filter(
            doctor_id=doctor_id,
            status='available'
        )
        
        # Filter by date
        date = self.request.query_params.get('date')
        if date:
            queryset = queryset.filter(date=date)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        return queryset.order_by('date', 'start_time')


class MyAvailabilityView(generics.ListCreateAPIView):
    serializer_class = AvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.user_type != 'doctor':
            return Availability.objects.none()
        return Availability.objects.filter(doctor=self.request.user.doctor_profile)

    def perform_create(self, serializer):
        # Add this check!
        if self.request.user.user_type != 'doctor':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only doctors can create availability")
        serializer.save(doctor=self.request.user.doctor_profile)

class GenerateSlotsView(APIView):
    """Generate time slots for current doctor based on availability"""
    
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.user_type != 'doctor':
            return Response(
                {'error': 'Only doctors can generate slots'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        days_ahead = request.data.get('days_ahead', 30)
        
        try:
            days_ahead = int(days_ahead)
            if days_ahead < 1 or days_ahead > 90:
                days_ahead = 30
        except (ValueError, TypeError):
            days_ahead = 30
        
        slots_created = generate_time_slots(
            request.user.doctor_profile,
            days_ahead
        )
        
        return Response({
            'message': f'Generated {slots_created} time slots for the next {days_ahead} days',
            'slots_created': slots_created
        })


class DeleteAvailabilityView(generics.DestroyAPIView):
    """Delete an availability slot"""
    
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.user_type != 'doctor':
            return Availability.objects.none()
        return Availability.objects.filter(doctor=self.request.user.doctor_profile)