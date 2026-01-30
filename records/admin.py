from django.contrib import admin
from .models import HealthProfile, MedicalHistory, MedicalDocument


@admin.register(HealthProfile)
class HealthProfileAdmin(admin.ModelAdmin):
    list_display = ['patient', 'blood_type', 'smoking_status', 'updated_at']
    list_filter = ['blood_type', 'smoking_status', 'alcohol_consumption']
    search_fields = ['patient__email', 'patient__first_name', 'patient__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Patient', {
            'fields': ('patient',)
        }),
        ('Physical Information', {
            'fields': ('blood_type', 'height_cm', 'weight_kg')
        }),
        ('Medical History', {
            'fields': ('allergies', 'chronic_conditions', 'current_medications', 'past_surgeries', 'family_history')
        }),
        ('Lifestyle', {
            'fields': ('smoking_status', 'alcohol_consumption', 'exercise_frequency')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship')
        }),
        ('Insurance', {
            'fields': ('insurance_provider', 'insurance_policy_number')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MedicalHistory)
class MedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ['patient', 'event_type', 'title', 'event_date', 'created_at']
    list_filter = ['event_type', 'event_date']
    search_fields = ['patient__email', 'title', 'description']
    date_hierarchy = 'event_date'


@admin.register(MedicalDocument)
class MedicalDocumentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'title', 'document_type', 'file_size', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['patient__email', 'title']
    date_hierarchy = 'uploaded_at'
    readonly_fields = ['file_size', 'uploaded_at']