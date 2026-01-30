from django.contrib import admin
from .models import Specialization, Availability, TimeSlot


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'day_of_week', 'start_time', 'end_time', 'is_active']


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'date', 'start_time', 'status']
    list_filter = ['status', 'date']