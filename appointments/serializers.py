from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, timedelta

from accounts.serializers import UserSerializer, DoctorProfileSerializer
from doctors.models import TimeSlot
from doctors.serializers import TimeSlotSerializer
from .models import Appointment


class AppointmentListSerializer(serializers.ModelSerializer):
    """Serializer for listing appointments"""
    
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.full_name', read_only=True)
    doctor_specialization = serializers.CharField(source='doctor.specialization.name', read_only=True)
    can_cancel = serializers.BooleanField(read_only=True)
    can_reschedule = serializers.BooleanField(read_only=True)
    can_join = serializers.BooleanField(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id',
            'appointment_number',
            'patient_name',
            'doctor_name',
            'doctor_specialization',
            'date',
            'start_time',
            'end_time',
            'status',
            'reason',
            'can_cancel',
            'can_reschedule',
            'can_join',
            'created_at',
        ]


class AppointmentDetailSerializer(serializers.ModelSerializer):
    """Serializer for appointment details"""
    
    patient = UserSerializer(read_only=True)
    doctor = DoctorProfileSerializer(read_only=True)
    time_slot = TimeSlotSerializer(read_only=True)
    can_cancel = serializers.BooleanField(read_only=True)
    can_reschedule = serializers.BooleanField(read_only=True)
    can_join = serializers.BooleanField(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id',
            'appointment_number',
            'patient',
            'doctor',
            'time_slot',
            'date',
            'start_time',
            'end_time',
            'status',
            'reason',
            'symptoms',
            'video_room_url',
            'video_host_url',
            'can_cancel',
            'can_reschedule',
            'can_join',
            'reschedule_count',
            'created_at',
            'updated_at',
        ]


class BookAppointmentSerializer(serializers.Serializer):
    """Serializer for booking an appointment"""
    
    doctor_id = serializers.IntegerField()
    time_slot_id = serializers.IntegerField()
    reason = serializers.CharField(required=False, allow_blank=True)
    symptoms = serializers.CharField(required=False, allow_blank=True)

    def validate_doctor_id(self, value):
        from accounts.models import DoctorProfile
        try:
            doctor = DoctorProfile.objects.get(id=value)
            if not doctor.is_verified:
                raise serializers.ValidationError("Doctor is not verified")
            return value
        except DoctorProfile.DoesNotExist:
            raise serializers.ValidationError("Doctor not found")

    def validate_time_slot_id(self, value):
        try:
            slot = TimeSlot.objects.get(id=value)
            
            # Check if slot is available
            if slot.status != 'available':
                raise serializers.ValidationError("This time slot is not available")
            
            # Check if slot is in the future
            slot_datetime = datetime.combine(slot.date, slot.start_time)
            if slot_datetime <= datetime.now():
                raise serializers.ValidationError("Cannot book a slot in the past")
            
            return value
        except TimeSlot.DoesNotExist:
            raise serializers.ValidationError("Time slot not found")

    def validate(self, attrs):
        # Verify slot belongs to the doctor
        from accounts.models import DoctorProfile
        
        doctor = DoctorProfile.objects.get(id=attrs['doctor_id'])
        slot = TimeSlot.objects.get(id=attrs['time_slot_id'])
        
        if slot.doctor_id != doctor.id:
            raise serializers.ValidationError({
                "time_slot_id": "This slot does not belong to the selected doctor"
            })
        
        return attrs

    def create(self, validated_data):
        from accounts.models import DoctorProfile
        
        patient = self.context['request'].user
        doctor = DoctorProfile.objects.get(id=validated_data['doctor_id'])
        slot = TimeSlot.objects.get(id=validated_data['time_slot_id'])
        
        # Create appointment
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            time_slot=slot,
            date=slot.date,
            start_time=slot.start_time,
            end_time=slot.end_time,
            reason=validated_data.get('reason', ''),
            symptoms=validated_data.get('symptoms', ''),
            status='confirmed'
        )
        
        # Mark slot as booked
        slot.status = 'booked'
        slot.save()
        
        return appointment


class CancelAppointmentSerializer(serializers.Serializer):
    """Serializer for cancelling an appointment"""
    
    cancellation_reason = serializers.CharField(required=True, min_length=10)

    def validate(self, attrs):
        appointment = self.context.get('appointment')
        
        if not appointment.can_cancel:
            raise serializers.ValidationError(
                "This appointment cannot be cancelled. "
                "Either it's already cancelled/completed or less than 2 hours before start time."
            )
        
        return attrs


class RescheduleAppointmentSerializer(serializers.Serializer):
    """Serializer for rescheduling an appointment"""
    
    new_time_slot_id = serializers.IntegerField()

    def validate_new_time_slot_id(self, value):
        try:
            slot = TimeSlot.objects.get(id=value)
            
            if slot.status != 'available':
                raise serializers.ValidationError("This time slot is not available")
            
            slot_datetime = datetime.combine(slot.date, slot.start_time)
            if slot_datetime <= datetime.now():
                raise serializers.ValidationError("Cannot reschedule to a past slot")
            
            return value
        except TimeSlot.DoesNotExist:
            raise serializers.ValidationError("Time slot not found")

    def validate(self, attrs):
        appointment = self.context.get('appointment')
        
        if not appointment.can_reschedule:
            raise serializers.ValidationError(
                "This appointment cannot be rescheduled. "
                "Either maximum reschedules reached or less than 2 hours before start time."
            )
        
        # Verify new slot belongs to same doctor
        new_slot = TimeSlot.objects.get(id=attrs['new_time_slot_id'])
        if new_slot.doctor_id != appointment.doctor_id:
            raise serializers.ValidationError({
                "new_time_slot_id": "New slot must be with the same doctor"
            })
        
        return attrs