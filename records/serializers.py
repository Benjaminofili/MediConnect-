from rest_framework import serializers
from .models import HealthProfile, MedicalHistory, MedicalDocument


class HealthProfileSerializer(serializers.ModelSerializer):
    """Serializer for health profile."""
    
    bmi = serializers.FloatField(read_only=True)
    patient_email = serializers.CharField(source='patient.email', read_only=True)
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    
    class Meta:
        model = HealthProfile
        fields = [
            'id',
            'patient_email',
            'patient_name',
            'blood_type',
            'height_cm',
            'weight_kg',
            'bmi',
            'allergies',
            'chronic_conditions',
            'current_medications',
            'past_surgeries',
            'family_history',
            'smoking_status',
            'alcohol_consumption',
            'exercise_frequency',
            'emergency_contact_name',
            'emergency_contact_phone',
            'emergency_contact_relationship',
            'insurance_provider',
            'insurance_policy_number',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MedicalHistorySerializer(serializers.ModelSerializer):
    """Serializer for medical history."""
    
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    
    class Meta:
        model = MedicalHistory
        fields = [
            'id',
            'event_type',
            'event_type_display',
            'title',
            'description',
            'event_date',
            'doctor_name',
            'hospital_name',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MedicalDocumentSerializer(serializers.ModelSerializer):
    """Serializer for medical documents."""
    
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    file_url = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicalDocument
        fields = [
            'id',
            'title',
            'document_type',
            'document_type_display',
            'file',
            'file_url',
            'file_size',
            'file_size_display',
            'description',
            'document_date',
            'consultation',
            'uploaded_at',
        ]
        read_only_fields = ['id', 'file_size', 'uploaded_at']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_file_size_display(self, obj):
        """Convert bytes to human readable format."""
        size = obj.file_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"


class MedicalDocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading medical documents."""
    
    class Meta:
        model = MedicalDocument
        fields = [
            'title',
            'document_type',
            'file',
            'description',
            'document_date',
        ]
    
    def validate_file(self, value):
        # Max 5 MB
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("File size cannot exceed 5 MB")
        
        # Allowed types
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Only PDF, JPEG, and PNG files are allowed")
        
        return value