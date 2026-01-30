from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import PatientProfile, DoctorProfile

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'full_name': self.user.full_name,
            'user_type': self.user.user_type,
        }
        return data


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'user_type', 'phone', 'date_of_birth', 'gender', 'profile_picture', 'created_at']
        read_only_fields = ['id', 'email', 'user_type', 'created_at']


class PatientRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    # Explicitly require these fields
    phone = serializers.CharField(required=True)
    date_of_birth = serializers.DateField(required=True)
    gender = serializers.CharField(required=True)

    class Meta:
        model = User
        # Added phone, dob, gender. Removed medical fields.
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name', 'phone', 'date_of_birth', 'gender']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        validated_data['user_type'] = 'patient'
        
        # Create user with all the demographic info
        user = User.objects.create_user(**validated_data)
        
        # Create empty profile (to be filled later)
        PatientProfile.objects.create(user=user)
        return user

class DoctorRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    license_number = serializers.CharField()
    specialization_id = serializers.IntegerField()
    experience_years = serializers.IntegerField()
    education = serializers.CharField()
    consultation_fee = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name', 'phone', 'date_of_birth', 'gender', 'license_number', 'specialization_id', 'experience_years', 'education', 'consultation_fee']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match'})
        if DoctorProfile.objects.filter(license_number=attrs['license_number']).exists():
            raise serializers.ValidationError({'license_number': 'License number already exists'})
        return attrs

    def create(self, validated_data):
        license_number = validated_data.pop('license_number')
        specialization_id = validated_data.pop('specialization_id')
        experience_years = validated_data.pop('experience_years')
        education = validated_data.pop('education')
        consultation_fee = validated_data.pop('consultation_fee')
        validated_data.pop('password_confirm')
        validated_data['user_type'] = 'doctor'
        user = User.objects.create_user(**validated_data)
        DoctorProfile.objects.create(
            user=user,
            license_number=license_number,
            specialization_id=specialization_id,
            experience_years=experience_years,
            education=education,
            consultation_fee=consultation_fee
        )
        return user


class PatientProfileSerializer(serializers.ModelSerializer):
    # Make user writable via nested serializer logic below
    user = UserSerializer(read_only=False)

    class Meta:
        model = PatientProfile
        # Includes all medical fields (blood_type, etc.) + nested user data
        fields = '__all__' 

    def update(self, instance, validated_data):
        # 1. Update Nested User Data (Name, Phone, etc.)
        user_data = validated_data.pop('user', {})
        user = instance.user
        for attr, value in user_data.items():
            if attr not in ['email', 'password']: # Don't update sensitive/immutable fields here
                setattr(user, attr, value)
        user.save()

        # 2. Update PatientProfile Data (Blood Type, Height, Allergies)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class DoctorProfileSerializer(serializers.ModelSerializer):
    # Allow writing to the nested user object
    user = UserSerializer(read_only=False)
    specialization_name = serializers.CharField(source='specialization.name', read_only=True)

    class Meta:
        model = DoctorProfile
        fields = '__all__'
        # License number is read-only for compliance
        read_only_fields = ['license_number', 'verification_status', 'specialization']

    def update(self, instance, validated_data):
        # 1. Update Nested User Data (Name, Phone, Profile Pic)
        user_data = validated_data.pop('user', {})
        user = instance.user
        
        for attr, value in user_data.items():
            if attr not in ['email', 'password']: 
                setattr(user, attr, value)
        user.save()

        # 2. Update DoctorProfile Data (Bio, Fee, etc.)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
