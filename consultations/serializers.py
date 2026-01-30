from rest_framework import serializers
from .models import Consultation, Prescription, PrescriptionItem


class PrescriptionItemSerializer(serializers.ModelSerializer):
    """Serializer for prescription items."""
    
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    duration_display = serializers.CharField(source='get_duration_display', read_only=True)
    
    class Meta:
        model = PrescriptionItem
        fields = [
            'id',
            'medicine_name',
            'dosage',
            'frequency',
            'frequency_display',
            'duration',
            'duration_display',
            'quantity',
            'instructions',
        ]


class PrescriptionSerializer(serializers.ModelSerializer):
    """Serializer for prescriptions."""
    
    items = PrescriptionItemSerializer(many=True, read_only=True)
    doctor_name = serializers.CharField(source='consultation.appointment.doctor.user.full_name', read_only=True)
    patient_name = serializers.CharField(source='consultation.appointment.patient.full_name', read_only=True)
    
    class Meta:
        model = Prescription
        fields = [
            'id',
            'prescription_number',
            'consultation',
            'doctor_name',
            'patient_name',
            'diagnosis',
            'notes',
            'issued_date',
            'valid_until',
            'items',
            'created_at',
        ]
        read_only_fields = ['id', 'prescription_number', 'issued_date', 'created_at']


class CreatePrescriptionSerializer(serializers.Serializer):
    """Serializer for creating a prescription with items."""
    
    diagnosis = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    valid_days = serializers.IntegerField(default=30, min_value=1, max_value=365)
    items = PrescriptionItemSerializer(many=True)
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one medicine is required")
        return value


class ConsultationSerializer(serializers.ModelSerializer):
    """Serializer for consultations."""
    
    appointment_number = serializers.CharField(source='appointment.appointment_number', read_only=True)
    patient_name = serializers.CharField(source='appointment.patient.full_name', read_only=True)
    patient_id = serializers.IntegerField(source='appointment.patient.id', read_only=True)
    doctor_name = serializers.CharField(source='appointment.doctor.user.full_name', read_only=True)
    date = serializers.DateField(source='appointment.date', read_only=True)
    duration_minutes = serializers.IntegerField(read_only=True)
    prescriptions = PrescriptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Consultation
        fields = [
            'id',
            'appointment',
            'appointment_number',
            'patient_id',
            'patient_name',
            'doctor_name',
            'date',
            'chief_complaint',
            'symptoms',
            'examination_notes',
            'diagnosis',
            'treatment_plan',
            'notes',
            'private_notes',
            'followup_needed',
            'followup_date',
            'followup_notes',
            'started_at',
            'ended_at',
            'duration_minutes',
            'prescriptions',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'appointment', 'created_at', 'updated_at']


class ConsultationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating consultation notes."""
    
    class Meta:
        model = Consultation
        fields = [
            'chief_complaint',
            'symptoms',
            'examination_notes',
            'diagnosis',
            'treatment_plan',
            'notes',
            'private_notes',
            'followup_needed',
            'followup_date',
            'followup_notes',
        ]


class ConsultationListSerializer(serializers.ModelSerializer):
    """Serializer for listing consultations."""
    
    appointment_number = serializers.CharField(source='appointment.appointment_number', read_only=True)
    patient_name = serializers.CharField(source='appointment.patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='appointment.doctor.user.full_name', read_only=True)
    date = serializers.DateField(source='appointment.date', read_only=True)
    
    class Meta:
        model = Consultation
        fields = [
            'id',
            'appointment_number',
            'patient_name',
            'doctor_name',
            'date',
            'diagnosis',
            'followup_needed',
            'created_at',
        ]