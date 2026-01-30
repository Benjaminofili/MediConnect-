from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PatientProfile, DoctorProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'user_type', 'is_active']
    list_filter = ['user_type', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-created_at']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal', {'fields': ('first_name', 'last_name', 'phone', 'date_of_birth', 'gender')}),
        ('Permissions', {'fields': ('user_type', 'is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'user_type')}),
    )


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'blood_type']


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialization', 'license_number', 'verification_status']
    list_filter = ['verification_status']
    actions = ['verify_doctors']

    @admin.action(description='Verify selected doctors')
    def verify_doctors(self, request, queryset):
        queryset.update(verification_status='verified')