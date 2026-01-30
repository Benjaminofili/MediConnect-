import pytest
from datetime import date, time, timedelta
from decimal import Decimal
from django.db import IntegrityError, transaction
from rest_framework import status
from unittest.mock import patch, MagicMock

from doctors.models import Specialization, Availability, TimeSlot
from doctors.serializers import (
    SpecializationSerializer,
    DoctorListSerializer,
    DoctorDetailSerializer,
    AvailabilitySerializer,
    TimeSlotSerializer
)
from accounts.models import User, DoctorProfile


# ============================================
# SPECIALIZATION MODEL TESTS
# ============================================

@pytest.mark.django_db
class TestSpecializationModel:
    """Test Specialization model"""
    
    def test_create_specialization(self):
        """Verify specialization can be created"""
        spec = Specialization.objects.create(
            name='Cardiology',
            description='Heart specialist',
            icon='fa-heart',
            is_active=True
        )
        
        assert spec.pk is not None
        assert spec.name == 'Cardiology'
        assert str(spec) == 'Cardiology'
    
    def test_specialization_name_must_be_unique(self):
        """Verify duplicate specialization names are rejected"""
        Specialization.objects.create(name='Dermatology')
        
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Specialization.objects.create(name='Dermatology')
    
    def test_specialization_ordering(self):
        """Verify specializations are ordered by name"""
        Specialization.objects.create(name='Cardiology')
        Specialization.objects.create(name='Neurology')
        Specialization.objects.create(name='Dermatology')
        
        specs = list(Specialization.objects.values_list('name', flat=True))
        assert specs == ['Cardiology', 'Dermatology', 'Neurology']
    
    def test_inactive_specialization(self):
        """Verify is_active field works"""
        spec = Specialization.objects.create(
            name='Inactive Spec',
            is_active=False
        )
        
        active_specs = Specialization.objects.filter(is_active=True)
        assert spec not in active_specs


# ============================================
# AVAILABILITY MODEL TESTS
# ============================================

@pytest.mark.django_db
class TestAvailabilityModel:
    """Test doctor's weekly availability"""
    
    def test_create_availability(self, doctor_profile):
        """Verify availability can be created"""
        avail = Availability.objects.create(
            doctor=doctor_profile,
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(12, 0),
            is_active=True
        )
        
        assert avail.pk is not None
        assert avail.get_day_of_week_display() == 'Tuesday'
    
    def test_availability_string_representation(self, doctor_profile):
        """Verify __str__ returns doctor - day"""
        avail = Availability.objects.create(
            doctor=doctor_profile,
            day_of_week=4,
            start_time=time(14, 0),
            end_time=time(18, 0)
        )
        
        assert 'Friday' in str(avail)
    
    def test_duplicate_availability_same_time_rejected(self, doctor_profile):
        """Verify same doctor can't have duplicate slot on same day/time"""
        Availability.objects.create(
            doctor=doctor_profile,
            day_of_week=0,
            start_time=time(9, 0),
            end_time=time(12, 0)
        )
        
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Availability.objects.create(
                    doctor=doctor_profile,
                    day_of_week=0,
                    start_time=time(9, 0),
                    end_time=time(11, 0)
                )
    
    def test_different_days_allowed(self, doctor_profile):
        """Verify same doctor can have availability on different days"""
        avail1 = Availability.objects.create(
            doctor=doctor_profile,
            day_of_week=0,
            start_time=time(9, 0),
            end_time=time(12, 0)
        )
        avail2 = Availability.objects.create(
            doctor=doctor_profile,
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(12, 0)
        )
        
        assert avail1.pk != avail2.pk


# ============================================
# TIMESLOT MODEL TESTS
# ============================================

@pytest.mark.django_db
class TestTimeSlotModel:
    """Test specific bookable time slots"""
    
    def test_create_time_slot(self, doctor_profile):
        """Verify time slot can be created"""
        tomorrow = date.today() + timedelta(days=1)
        
        slot = TimeSlot.objects.create(
            doctor=doctor_profile,
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='available'
        )
        
        assert slot.pk is not None
        assert slot.status == 'available'
    
    def test_time_slot_default_status(self, doctor_profile):
        """Verify default status is 'available'"""
        tomorrow = date.today() + timedelta(days=1)
        
        slot = TimeSlot.objects.create(
            doctor=doctor_profile,
            date=tomorrow,
            start_time=time(15, 0),
            end_time=time(15, 30)
        )
        
        assert slot.status == 'available'
    
    def test_duplicate_slot_same_time_rejected(self, doctor_profile):
        """Verify same doctor can't have duplicate slot at same date/time"""
        tomorrow = date.today() + timedelta(days=1)
        
        TimeSlot.objects.create(
            doctor=doctor_profile,
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(10, 30)
        )
        
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                TimeSlot.objects.create(
                    doctor=doctor_profile,
                    date=tomorrow,
                    start_time=time(10, 0),
                    end_time=time(10, 30)
                )
    
    def test_different_dates_allowed(self, doctor_profile):
        """Verify same time on different dates is allowed"""
        tomorrow = date.today() + timedelta(days=1)
        day_after = date.today() + timedelta(days=2)
        
        slot1 = TimeSlot.objects.create(
            doctor=doctor_profile,
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(10, 30)
        )
        slot2 = TimeSlot.objects.create(
            doctor=doctor_profile,
            date=day_after,
            start_time=time(10, 0),
            end_time=time(10, 30)
        )
        
        assert slot1.pk != slot2.pk
    
    def test_slot_status_transitions(self, available_time_slot):
        """Verify slot can transition between statuses"""
        assert available_time_slot.status == 'available'
        
        available_time_slot.status = 'booked'
        available_time_slot.save()
        available_time_slot.refresh_from_db()
        
        assert available_time_slot.status == 'booked'


# ============================================
# SERIALIZER TESTS
# ============================================

@pytest.mark.django_db
class TestSpecializationSerializer:
    """Test SpecializationSerializer"""
    
    def test_serializes_correctly(self, specialization):
        """Verify serialization includes expected fields"""
        serializer = SpecializationSerializer(specialization)
        data = serializer.data
        
        assert 'id' in data
        assert 'name' in data
        assert 'description' in data
        assert 'icon' in data
        assert data['name'] == 'General Practice'


@pytest.mark.django_db
class TestDoctorListSerializer:
    """Test DoctorListSerializer"""
    
    def test_serializes_correctly(self, doctor_user):
        """Verify serialization includes expected fields"""
        profile = doctor_user.doctor_profile
        serializer = DoctorListSerializer(profile)
        data = serializer.data
        
        assert 'id' in data
        assert 'user' in data
        assert 'specialization' in data
        assert 'experience_years' in data
        assert 'consultation_fee' in data
        assert 'average_rating' in data


@pytest.mark.django_db
class TestAvailabilitySerializer:
    """Test AvailabilitySerializer"""
    
    def test_serializes_correctly(self, availability):
        """Verify serialization includes day_name"""
        serializer = AvailabilitySerializer(availability)
        data = serializer.data
        
        assert 'day_of_week' in data
        assert 'day_name' in data
        assert 'start_time' in data
        assert 'end_time' in data
        assert data['day_name'] == 'Monday'


@pytest.mark.django_db
class TestTimeSlotSerializer:
    """Test TimeSlotSerializer"""
    
    def test_serializes_correctly(self, available_time_slot):
        """Verify serialization includes expected fields"""
        serializer = TimeSlotSerializer(available_time_slot)
        data = serializer.data
        
        assert 'id' in data
        assert 'date' in data
        assert 'start_time' in data
        assert 'end_time' in data
        assert 'status' in data


# ============================================
# API TESTS - SPECIALIZATIONS (PUBLIC)
# ============================================

@pytest.mark.django_db
class TestSpecializationAPI:
    """Test specialization endpoints"""
    
    url = '/api/doctors/specializations/'
    
    def test_list_specializations(self, api_client, specialization):
        """Verify anyone can list specializations"""
        response = api_client.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_only_active_specializations_returned(self, api_client):
        """Verify only active specializations are listed"""
        Specialization.objects.create(name='Active Spec', is_active=True)
        Specialization.objects.create(name='Inactive Spec', is_active=False)
        
        response = api_client.get(self.url)
        
        names = [s['name'] for s in response.data]
        assert 'Active Spec' in names
        assert 'Inactive Spec' not in names
    
    def test_no_authentication_required(self, api_client):
        """Verify endpoint is public"""
        Specialization.objects.create(name='Test Spec', is_active=True)
        
        response = api_client.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK


# ============================================
# API TESTS - DOCTOR LIST (PUBLIC)
# ============================================

@pytest.mark.django_db
class TestDoctorListAPI:
    """Test doctor list endpoint"""
    
    url = '/api/doctors/'
    
    def test_list_doctors(self, api_client, doctor_user):
        """Verify anyone can list verified doctors"""
        response = api_client.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_only_verified_doctors_returned(self, api_client, specialization):
        """Verify only verified doctors are listed"""
        # Create verified doctor
        verified_user = User.objects.create_user(
            email='verified@test.com',
            password='pass123',
            first_name='Verified',
            last_name='Doctor',
            user_type='doctor'
        )
        DoctorProfile.objects.create(
            user=verified_user,
            specialization=specialization,
            license_number='VER123',
            experience_years=5,
            education='Test School',
            consultation_fee=Decimal('5000.00'),
            verification_status='verified'
        )
        
        # Create pending doctor
        pending_user = User.objects.create_user(
            email='pending@test.com',
            password='pass123',
            first_name='Pending',
            last_name='Doctor',
            user_type='doctor'
        )
        DoctorProfile.objects.create(
            user=pending_user,
            specialization=specialization,
            license_number='PEN123',
            experience_years=3,
            education='Test School',
            consultation_fee=Decimal('4000.00'),
            verification_status='pending'
        )
        
        response = api_client.get(self.url)
        
        emails = [d['user']['email'] for d in response.data['results']] if 'results' in response.data else [d['user']['email'] for d in response.data]
        assert 'verified@test.com' in emails
        assert 'pending@test.com' not in emails
    
    def test_filter_by_specialization(self, api_client, doctor_user, specialization):
        """Verify filtering by specialization works"""
        response = api_client.get(f'{self.url}?specialization={specialization.id}')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_filter_by_min_experience(self, api_client, doctor_user):
        """Verify filtering by minimum experience works"""
        response = api_client.get(f'{self.url}?min_experience=3')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_filter_by_max_fee(self, api_client, doctor_user):
        """Verify filtering by maximum fee works"""
        response = api_client.get(f'{self.url}?max_fee=10000')
        
        assert response.status_code == status.HTTP_200_OK


# ============================================
# API TESTS - DOCTOR DETAIL (PUBLIC)
# ============================================

@pytest.mark.django_db
class TestDoctorDetailAPI:
    """Test doctor detail endpoint"""
    
    def test_get_doctor_detail(self, api_client, doctor_user):
        """Verify anyone can view doctor details"""
        profile = doctor_user.doctor_profile
        url = f'/api/doctors/{profile.id}/'
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'license_number' in response.data
        assert 'education' in response.data
        assert 'bio' in response.data
    
    def test_unverified_doctor_not_accessible(self, api_client, specialization):
        """Verify unverified doctors return 404"""
        pending_user = User.objects.create_user(
            email='pending2@test.com',
            password='pass123',
            first_name='Pending',
            last_name='Doctor',
            user_type='doctor'
        )
        pending_profile = DoctorProfile.objects.create(
            user=pending_user,
            specialization=specialization,
            license_number='PEND456',
            experience_years=2,
            education='Test School',
            consultation_fee=Decimal('3000.00'),
            verification_status='pending'
        )
        
        url = f'/api/doctors/{pending_profile.id}/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================
# API TESTS - DOCTOR SLOTS (PUBLIC)
# ============================================

@pytest.mark.django_db
class TestDoctorSlotsAPI:
    """Test doctor time slots endpoint"""
    
    def test_list_available_slots(self, api_client, doctor_profile, available_time_slot):
        """Verify anyone can view available slots"""
        url = f'/api/doctors/{doctor_profile.id}/slots/'
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_only_available_slots_returned(self, api_client, doctor_profile):
        """Verify only available slots are listed"""
        tomorrow = date.today() + timedelta(days=1)
        
        # Create available slot
        TimeSlot.objects.create(
            doctor=doctor_profile,
            date=tomorrow,
            start_time=time(9, 0),
            end_time=time(9, 30),
            status='available'
        )
        
        # Create booked slot
        TimeSlot.objects.create(
            doctor=doctor_profile,
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='booked'
        )
        
        url = f'/api/doctors/{doctor_profile.id}/slots/'
        response = api_client.get(url)
        
        statuses = [s['status'] for s in response.data['results']] if 'results' in response.data else [s['status'] for s in response.data]
        assert all(s == 'available' for s in statuses)
    
    def test_filter_by_date(self, api_client, doctor_profile, available_time_slot):
        """Verify filtering by date works"""
        tomorrow = date.today() + timedelta(days=1)
        url = f'/api/doctors/{doctor_profile.id}/slots/?date={tomorrow}'
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_filter_by_date_range(self, api_client, doctor_profile, available_time_slot):
        """Verify filtering by date range works"""
        tomorrow = date.today() + timedelta(days=1)
        next_week = date.today() + timedelta(days=7)
        url = f'/api/doctors/{doctor_profile.id}/slots/?date_from={tomorrow}&date_to={next_week}'
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK


# ============================================
# API TESTS - MY AVAILABILITY (DOCTOR ONLY)
# ============================================

@pytest.mark.django_db
class TestMyAvailabilityAPI:
    """Test doctor's own availability management"""
    
    url = '/api/doctors/my/availability/'
    
    def test_doctor_can_list_own_availability(self, authenticated_doctor, availability):
        """Verify doctor can list their availability"""
        response = authenticated_doctor.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_doctor_can_create_availability(self, authenticated_doctor):
        """Verify doctor can create new availability"""
        data = {
            'day_of_week': 2,
            'start_time': '09:00:00',
            'end_time': '17:00:00',
            'is_active': True
        }
        
        response = authenticated_doctor.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['day_of_week'] == 2
        assert response.data['day_name'] == 'Wednesday'
    
    def test_patient_cannot_create_availability(self, authenticated_patient):
        """Verify patient cannot create doctor availability"""
        data = {
            'day_of_week': 2,
            'start_time': '09:00:00',
            'end_time': '17:00:00'
        }
    
        response = authenticated_patient.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_patient_gets_empty_availability_list(self, authenticated_patient):
        """Verify patient sees empty availability list"""
        response = authenticated_patient.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.data['results'] if 'results' in response.data else response.data
        assert len(data) == 0
    
    def test_unauthenticated_rejected(self, api_client):
        """Verify unauthenticated request is rejected"""
        response = api_client.get(self.url)
        
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


# ============================================
# API TESTS - DELETE AVAILABILITY (DOCTOR ONLY)
# ============================================

@pytest.mark.django_db
class TestDeleteAvailabilityAPI:
    """Test deleting availability"""
    
    def test_doctor_can_delete_own_availability(self, authenticated_doctor, availability):
        """Verify doctor can delete their own availability"""
        url = f'/api/doctors/my/availability/{availability.id}/'
        
        response = authenticated_doctor.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Availability.objects.filter(id=availability.id).exists()
    
    def test_doctor_cannot_delete_others_availability(self, authenticated_doctor, specialization):
        """Verify doctor cannot delete another doctor's availability"""
        # Create another doctor
        other_user = User.objects.create_user(
            email='other@test.com',
            password='pass123',
            first_name='Other',
            last_name='Doctor',
            user_type='doctor'
        )
        other_profile = DoctorProfile.objects.create(
            user=other_user,
            specialization=specialization,
            license_number='OTHER123',
            experience_years=3,
            education='Other School',
            consultation_fee=Decimal('4000.00'),
            verification_status='verified'
        )
        other_availability = Availability.objects.create(
            doctor=other_profile,
            day_of_week=3,
            start_time=time(10, 0),
            end_time=time(14, 0)
        )
        
        url = f'/api/doctors/my/availability/{other_availability.id}/'
        response = authenticated_doctor.delete(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Availability.objects.filter(id=other_availability.id).exists()


# ============================================
# API TESTS - GENERATE SLOTS (DOCTOR ONLY)
# ============================================

@pytest.mark.django_db
class TestGenerateSlotsAPI:
    """Test slot generation endpoint"""
    
    url = '/api/doctors/my/generate-slots/'
    
    def test_doctor_can_generate_slots(self, authenticated_doctor, availability):
        """Verify doctor can generate time slots"""
        with patch('doctors.views.generate_time_slots') as mock_generate:
            mock_generate.return_value = 10
            
            response = authenticated_doctor.post(self.url, {'days_ahead': 7}, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'slots_created' in response.data
    
    def test_patient_cannot_generate_slots(self, authenticated_patient):
        """Verify patient cannot generate slots"""
        response = authenticated_patient.post(self.url, {'days_ahead': 7}, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'Only doctors' in response.data.get('error', '')
    
    def test_default_days_ahead(self, authenticated_doctor, availability):
        """Verify default days_ahead is 30"""
        with patch('doctors.views.generate_time_slots') as mock_generate:
            mock_generate.return_value = 20
            
            response = authenticated_doctor.post(self.url, {}, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        # Check that generate_time_slots was called with 30 days
        mock_generate.assert_called_once()
        args = mock_generate.call_args[0]
        assert args[1] == 30
    
    def test_invalid_days_ahead_uses_default(self, authenticated_doctor, availability):
        """Verify invalid days_ahead falls back to 30"""
        with patch('doctors.views.generate_time_slots') as mock_generate:
            mock_generate.return_value = 15
            
            response = authenticated_doctor.post(self.url, {'days_ahead': 'invalid'}, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        args = mock_generate.call_args[0]
        assert args[1] == 30
    
    def test_days_ahead_capped_at_90(self, authenticated_doctor, availability):
        """Verify days_ahead over 90 is reset to 30"""
        with patch('doctors.views.generate_time_slots') as mock_generate:
            mock_generate.return_value = 25
            
            response = authenticated_doctor.post(self.url, {'days_ahead': 100}, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        args = mock_generate.call_args[0]
        assert args[1] == 30
    
    def test_unauthenticated_rejected(self, api_client):
        """Verify unauthenticated request is rejected"""
        response = api_client.post(self.url, {}, format='json')
        
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]