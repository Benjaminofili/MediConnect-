from django.contrib import admin
from .models import Consultation, Prescription, PrescriptionItem


class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 1


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'diagnosis', 'followup_needed', 'created_at']
    list_filter = ['followup_needed', 'created_at']
    search_fields = ['appointment__appointment_number', 'diagnosis']
    readonly_fields = ['created_at', 'updated_at', 'started_at', 'ended_at']
    
    fieldsets = (
        ('Appointment', {
            'fields': ('appointment',)
        }),
        ('Patient Information', {
            'fields': ('chief_complaint', 'symptoms')
        }),
        ('Doctor Notes', {
            'fields': ('examination_notes', 'diagnosis', 'treatment_plan', 'notes', 'private_notes')
        }),
        ('Follow-up', {
            'fields': ('followup_needed', 'followup_date', 'followup_notes')
        }),
        ('Timing', {
            'fields': ('started_at', 'ended_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['prescription_number', 'consultation', 'issued_date', 'valid_until']
    list_filter = ['issued_date']
    search_fields = ['prescription_number', 'consultation__appointment__appointment_number']
    inlines = [PrescriptionItemInline]
    readonly_fields = ['prescription_number', 'issued_date', 'created_at']


@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(admin.ModelAdmin):
    list_display = ['medicine_name', 'prescription', 'dosage', 'frequency', 'duration']
    list_filter = ['frequency', 'duration']
    search_fields = ['medicine_name', 'prescription__prescription_number']