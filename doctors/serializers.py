from rest_framework import serializers
from accounts.models import DoctorProfile
from accounts.serializers import UserSerializer
from .models import Specialization, Availability, TimeSlot


class SpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialization
        fields = ['id', 'name', 'description', 'icon']


class DoctorListSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    specialization = SpecializationSerializer(read_only=True)

    class Meta:
        model = DoctorProfile
        fields = ['id', 'user', 'specialization', 'experience_years', 'consultation_fee', 'average_rating', 'hospital_name']


class DoctorDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    specialization = SpecializationSerializer(read_only=True)

    class Meta:
        model = DoctorProfile
        fields = ['id', 'user', 'specialization', 'license_number', 'experience_years', 'education', 'bio', 'consultation_fee', 'hospital_name', 'average_rating', 'total_reviews']


class AvailabilitySerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = Availability
        fields = ['id', 'day_of_week', 'day_name', 'start_time', 'end_time', 'is_active']


class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ['id', 'date', 'start_time', 'end_time', 'status']