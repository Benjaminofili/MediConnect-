import pytest
import os
from datetime import date, time, timedelta
from decimal import Decimal
from django.utils import timezone
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock
from django.db import connection


REAL_API_TESTS = os.getenv('REAL_API_TESTS', 'false').lower() == 'true'


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def patient_user(db):
    from accounts.models import User, PatientProfile
    
    user = User.objects.create_user(
        email='patient@test.com',
        password='testpass123',
        first_name='Test',
        last_name='Patient',
        user_type='patient'
    )
    PatientProfile.objects.create(
        user=user,
        blood_type='O+',
        allergies='None'
    )
    return user


@pytest.fixture
def second_patient_user(db):
    """Second patient for double-booking tests"""
    from accounts.models import User, PatientProfile
    
    user = User.objects.create_user(
        email='patient2@test.com',
        password='testpass123',
        first_name='Second',
        last_name='Patient',
        user_type='patient'
    )
    PatientProfile.objects.create(user=user)
    return user

@pytest.fixture
def valid_patient_data():
    """Valid patient registration payload"""
    return {
        'email': 'newpatient@test.com',
        'password': 'SecurePass123!',
        'password_confirm': 'SecurePass123!',
        'first_name': 'John',
        'last_name': 'Doe',
        'phone': '+2341234567890',
        'date_of_birth': '1990-05-15',
        'gender': 'male'
    }

@pytest.fixture
def specialization(db):
    from doctors.models import Specialization
    
    spec, _ = Specialization.objects.get_or_create(
        name='General Practice',
        defaults={
            'description': 'General medical care',
            'icon': 'fa-stethoscope',
            'is_active': True
        }
    )
    return spec



@pytest.fixture
def valid_doctor_data(specialization):
    """Valid doctor registration payload"""
    return {
        'email': 'newdoctor@test.com',
        'password': 'SecurePass123!',
        'password_confirm': 'SecurePass123!',
        'first_name': 'Jane',
        'last_name': 'Smith',
        'phone': '+2349876543210',
        'date_of_birth': '1985-03-20',
        'gender': 'female',
        'license_number': 'NEWDOC12345',
        'specialization_id': specialization.id,
        'experience_years': 10,
        'education': 'Lagos Medical School',
        'consultation_fee': '7500.00'
    }



@pytest.fixture
def doctor_user(db, specialization):
    from accounts.models import User, DoctorProfile
    
    user = User.objects.create_user(
        email='doctor@test.com',
        password='testpass123',
        first_name='Test',
        last_name='Doctor',
        user_type='doctor'
    )
    
    DoctorProfile.objects.create(
        user=user,
        specialization=specialization,
        license_number='DOC12345',
        experience_years=5,
        education='Test Medical School',
        consultation_fee=Decimal('5000.00'),
        verification_status='verified'
    )
    return user


@pytest.fixture
def doctor_profile(doctor_user):
    """Returns the DoctorProfile, not the User"""
    return doctor_user.doctor_profile


@pytest.fixture
def availability(db, doctor_profile):
    """Create weekly availability for doctor"""
    from doctors.models import Availability
    
    return Availability.objects.create(
        doctor=doctor_profile,
        day_of_week=0,  # Monday
        start_time=time(9, 0),
        end_time=time(17, 0),
        is_active=True
    )


@pytest.fixture
def available_time_slot(db, doctor_profile):
    """Create an available time slot for tomorrow"""
    from doctors.models import TimeSlot
    
    tomorrow = date.today() + timedelta(days=1)
    
    return TimeSlot.objects.create(
        doctor=doctor_profile,
        date=tomorrow,
        start_time=time(10, 0),
        end_time=time(10, 30),
        status='available'
    )


@pytest.fixture
def booked_time_slot(db, doctor_profile):
    """Create an already booked time slot"""
    from doctors.models import TimeSlot
    
    tomorrow = date.today() + timedelta(days=1)
    
    return TimeSlot.objects.create(
        doctor=doctor_profile,
        date=tomorrow,
        start_time=time(11, 0),
        end_time=time(11, 30),
        status='booked'
    )


@pytest.fixture
def appointment(db, patient_user, doctor_profile, available_time_slot):
    """Create a confirmed appointment"""
    from appointments.models import Appointment
    
    # Mark slot as booked
    available_time_slot.status = 'booked'
    available_time_slot.save()
    
    return Appointment.objects.create(
        patient=patient_user,
        doctor=doctor_profile,
        time_slot=available_time_slot,
        date=available_time_slot.date,
        start_time=available_time_slot.start_time,
        end_time=available_time_slot.end_time,
        status='confirmed',
        reason='Regular checkup',
        symptoms='Headache'
    )


@pytest.fixture
def past_appointment(db, patient_user, doctor_profile):
    """Create an appointment in the past"""
    from appointments.models import Appointment
    
    yesterday = date.today() - timedelta(days=1)
    
    return Appointment.objects.create(
        patient=patient_user,
        doctor=doctor_profile,
        date=yesterday,
        start_time=time(10, 0),
        end_time=time(10, 30),
        status='completed'
    )


@pytest.fixture
def authenticated_patient(api_client, patient_user):
    api_client.force_authenticate(user=patient_user)
    return api_client


@pytest.fixture
def authenticated_doctor(api_client, doctor_user):
    api_client.force_authenticate(user=doctor_user)
    return api_client

@pytest.fixture
def mock_email_service():
    """Mock email service to prevent sending real emails"""
    with patch('accounts.views.EmailService') as mock:
        mock.send_welcome_email = MagicMock(return_value=None)
        yield mock

# @pytest.fixture(autouse=True)
# def enable_db_access_for_all_tests(db):
#     """Ensure database is available for all tests"""
#     pass

# @pytest.fixture(scope="function", autouse=True)
# def reset_db_connections():
#     """Reset connections after each test"""
#     yield
#     connection.close()


# @pytest.fixture(scope="session")
# def django_db_setup():
#     """Skip test database creation - use existing Supabase database"""
#     pass

# @pytest.fixture(scope="session")
# def django_db_modify_db_settings(django_db_modify_db_settings_xdist_suffix):
#     """Use the main database for tests (not recommended for production, but works for Supabase)"""
#     pass





@pytest.fixture(autouse=True)
def mock_whereby_api(request):
    """
    Mock Whereby API for tests - SKIP if REAL_API_TESTS=true or test is marked with 'real_api'
    
    Usage:
    - Set REAL_API_TESTS=true to disable mocking for all tests
    - Or mark specific test with @pytest.mark.real_api to disable mocking for that test
    """
    from appointments.models import Appointment  # Import inside fixture
    
    # Check if test is marked to use real API
    use_real_api = REAL_API_TESTS or request.node.get_closest_marker('real_api')
    
    if use_real_api:
        # Don't mock - use real API
        yield None
        return
    
    # Define the mock function BEFORE the patch
    def mock_generate_video_room(self):
        """Mock function that sets video URLs on the appointment instance"""
        self.video_room_url = 'https://whereby.com/test-room-mock'
        self.video_host_url = 'https://whereby.com/test-room-mock?host'
        self.video_room_id = 'test-room-mock'
    
    # Use patch.object with the function directly (NOT as side_effect)
    with patch.object(Appointment, 'generate_video_room', mock_generate_video_room):
        yield
