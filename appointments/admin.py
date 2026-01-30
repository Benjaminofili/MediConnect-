from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'appointment_number',
        'patient',
        'doctor',
        'date',
        'start_time',
        'status',
        'created_at',
    ]
    list_filter = ['status', 'date', 'doctor__specialization']
    search_fields = [
        'appointment_number',
        'patient__email',
        'patient__first_name',
        'doctor__user__email',
        'doctor__user__first_name',
    ]
    date_hierarchy = 'date'
    readonly_fields = ['appointment_number', 'video_room_url', 'video_room_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Appointment Info', {
            'fields': ('appointment_number', 'status')
        }),
        ('Parties', {
            'fields': ('patient', 'doctor')
        }),
        ('Schedule', {
            'fields': ('time_slot', 'date', 'start_time', 'end_time')
        }),
        ('Details', {
            'fields': ('reason', 'symptoms')
        }),
        ('Video Consultation', {
            'fields': ('video_room_url', 'video_room_id')
        }),
        ('Cancellation', {
            'fields': ('cancellation_reason', 'cancelled_by', 'cancelled_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )