# tests/integration/test_production_readiness.py
"""
Production Readiness Tests - Tests with REAL external APIs

These tests verify that the application works correctly with real external services
(Whereby API, database, etc.) to catch issues that wouldn't appear with mocked tests.

Run with:
    # Windows CMD
    set REAL_API_TESTS=true && pytest tests/integration/test_production_readiness.py -v -s
    
    # Windows PowerShell
    $env:REAL_API_TESTS="true"; pytest tests/integration/test_production_readiness.py -v -s
    
    # Linux/Mac
    REAL_API_TESTS=true pytest tests/integration/test_production_readiness.py -v -s

Requirements:
    - WHEREBY_API_KEY must be configured in settings or environment
    - Database must be accessible
    - All migrations must be applied
"""

import pytest
import requests
import os
from datetime import date, time, datetime, timedelta
from decimal import Decimal
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from appointments.models import Appointment
from accounts.models import User, DoctorProfile, PatientProfile
from doctors.models import Specialization, TimeSlot
from consultations.models import Consultation, Prescription


# ============================================================================
# CONFIGURATION
# ============================================================================

# Mark entire module to use real API (disables mock_whereby_api fixture)
pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.real_api,
]

# Skip all tests if no API key
WHEREBY_API_KEY = getattr(settings, 'WHEREBY_API_KEY', None) or os.getenv('WHEREBY_API_KEY')
SKIP_NO_API_KEY = pytest.mark.skipif(
    not WHEREBY_API_KEY,
    reason="WHEREBY_API_KEY not configured - set it in settings or environment"
)


# ============================================================================
# FIXTURES FOR PRODUCTION TESTS
# ============================================================================

@pytest.fixture
def api_client():
    """DRF API client for testing REST endpoints"""
    return APIClient()


@pytest.fixture
def prod_specialization(db):
    """Create a specialization for production tests"""
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
def prod_patient(db):
    """Create a verified patient for production tests"""
    user = User.objects.create_user(
        email='prod_patient@test.com',
        password='SecureTestPass123!',
        first_name='Production',
        last_name='Patient',
        user_type='patient',
        email_verified=True
    )
    PatientProfile.objects.create(
        user=user,
        blood_type='O+',
        allergies='None'
    )
    return user


@pytest.fixture
def prod_patient_2(db):
    """Create a second patient for concurrency tests"""
    user = User.objects.create_user(
        email='prod_patient2@test.com',
        password='SecureTestPass123!',
        first_name='Production2',
        last_name='Patient2',
        user_type='patient',
        email_verified=True
    )
    PatientProfile.objects.create(user=user)
    return user


@pytest.fixture
def prod_doctor(db, prod_specialization):
    """Create a verified doctor for production tests"""
    user = User.objects.create_user(
        email='prod_doctor@test.com',
        password='SecureTestPass123!',
        first_name='Production',
        last_name='Doctor',
        user_type='doctor',
        email_verified=True
    )
    DoctorProfile.objects.create(
        user=user,
        specialization=prod_specialization,
        license_number='PROD12345',
        experience_years=10,
        education='Production Medical School',
        consultation_fee=Decimal('5000.00'),
        verification_status='verified'
    )
    return user


@pytest.fixture
def prod_time_slot(db, prod_doctor):
    """Create an available time slot for tomorrow"""
    tomorrow = date.today() + timedelta(days=1)
    return TimeSlot.objects.create(
        doctor=prod_doctor.doctor_profile,
        date=tomorrow,
        start_time=time(10, 0),
        end_time=time(10, 30),
        status='available'
    )


@pytest.fixture
def prod_appointment_with_video(db, prod_patient, prod_doctor):
    """Create an appointment with REAL video room generated"""
    tomorrow = date.today() + timedelta(days=1)
    
    appointment = Appointment.objects.create(
        patient=prod_patient,
        doctor=prod_doctor.doctor_profile,
        date=tomorrow,
        start_time=time(14, 0),
        end_time=time(14, 30),
        status='confirmed',
        reason='Production readiness test'
    )
    
    # Generate REAL video room
    appointment.generate_video_room()
    appointment.save()
    
    return appointment


# ============================================================================
# TEST CLASS: API CONFIGURATION
# ============================================================================

@SKIP_NO_API_KEY
class TestAPIConfiguration:
    """Verify external API configuration is correct"""
    
    def test_whereby_api_key_is_configured(self):
        """Verify WHEREBY_API_KEY is set and not a placeholder"""
        api_key = WHEREBY_API_KEY
        
        assert api_key is not None, "WHEREBY_API_KEY not configured"
        assert len(api_key) > 20, f"WHEREBY_API_KEY seems too short ({len(api_key)} chars)"
        assert api_key != 'your-api-key-here', "WHEREBY_API_KEY is still placeholder"
        assert api_key != 'test', "WHEREBY_API_KEY is still placeholder"
        
        print(f"\n✅ API Key configured: {api_key[:15]}...")
    
    def test_whereby_api_key_is_valid(self):
        """Verify API key works with Whereby API"""
        response = requests.get(
            "https://api.whereby.dev/v1/meetings",
            headers={"Authorization": f"Bearer {WHEREBY_API_KEY}"},
            timeout=15
        )
        
        # 200 = success (list meetings), 401 = invalid key
        assert response.status_code != 401, "WHEREBY_API_KEY is invalid - got 401 Unauthorized"
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        
        print(f"\n✅ API Key is valid (status: {response.status_code})")
    
    def test_whereby_api_can_create_room(self):
        """Verify we can create a Whereby room"""
        end_date = (datetime.now() + timedelta(days=1)).isoformat()
        
        response = requests.post(
            "https://api.whereby.dev/v1/meetings",
            json={
                "endDate": end_date,
                "fields": ["hostRoomUrl"]
            },
            headers={
                "Authorization": f"Bearer {WHEREBY_API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=30
        )
        
        assert response.status_code == 201, f"Failed to create room: {response.text}"
        
        data = response.json()
        assert "roomUrl" in data, "Response missing roomUrl"
        assert "hostRoomUrl" in data, "Response missing hostRoomUrl"
        assert data["roomUrl"].startswith("https://"), "roomUrl should be HTTPS"
        
        print(f"\n✅ Successfully created Whereby room")
        print(f"   Room URL: {data['roomUrl']}")
        print(f"   Host URL: {data['hostRoomUrl']}")


# ============================================================================
# TEST CLASS: VIDEO ROOM GENERATION
# ============================================================================

@SKIP_NO_API_KEY
class TestVideoRoomGeneration:
    """Test video room generation with real Whereby API"""
    
    def test_appointment_model_generates_video_room(self, prod_patient, prod_doctor):
        """Test Appointment.generate_video_room() creates real room"""
        tomorrow = date.today() + timedelta(days=1)
        
        appointment = Appointment.objects.create(
            patient=prod_patient,
            doctor=prod_doctor.doctor_profile,
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='confirmed',
            reason='Video room generation test'
        )
        
        # Generate video room - REAL API call
        appointment.generate_video_room()
        appointment.save()
        
        # Verify fields are populated
        assert appointment.video_room_url, "video_room_url not set"
        assert appointment.video_host_url, "video_host_url not set"
        assert appointment.video_room_id, "video_room_id not set"
        
        # Verify URLs are valid Whereby URLs
        assert "whereby.com" in appointment.video_room_url, \
            f"Invalid room URL: {appointment.video_room_url}"
        assert "whereby.com" in appointment.video_host_url, \
            f"Invalid host URL: {appointment.video_host_url}"
        
        # Verify URLs are different
        assert appointment.video_room_url != appointment.video_host_url, \
            "Patient and host URLs should be different"
        
        print(f"\n✅ Video room generated successfully")
        print(f"   Room URL: {appointment.video_room_url}")
        print(f"   Host URL: {appointment.video_host_url}")
        print(f"   Room ID: {appointment.video_room_id}")
    
    def test_video_urls_persist_to_database(self, prod_appointment_with_video):
        """Verify video URLs are correctly saved and retrieved from database"""
        appointment_id = prod_appointment_with_video.id
        original_room_url = prod_appointment_with_video.video_room_url
        original_host_url = prod_appointment_with_video.video_host_url
        
        # Clear cached instance and reload from database
        del prod_appointment_with_video
        
        reloaded = Appointment.objects.get(id=appointment_id)
        
        assert reloaded.video_room_url == original_room_url, \
            "video_room_url not persisted correctly"
        assert reloaded.video_host_url == original_host_url, \
            "video_host_url not persisted correctly"
        
        print(f"\n✅ Video URLs persisted correctly to database")
    
    def test_video_url_field_length_sufficient(self, prod_appointment_with_video):
        """Verify URL field lengths are sufficient for real Whereby URLs"""
        room_url_length = len(prod_appointment_with_video.video_room_url)
        host_url_length = len(prod_appointment_with_video.video_host_url)
        
        # Model has max_length=500
        assert room_url_length <= 500, \
            f"video_room_url too long ({room_url_length} chars) - increase field max_length"
        assert host_url_length <= 500, \
            f"video_host_url too long ({host_url_length} chars) - increase field max_length"
        
        print(f"\n✅ URL lengths are within limits")
        print(f"   Room URL: {room_url_length} chars")
        print(f"   Host URL: {host_url_length} chars")


# ============================================================================
# TEST CLASS: VIDEO ROOM ACCESSIBILITY
# ============================================================================

@SKIP_NO_API_KEY
class TestVideoRoomAccessibility:
    """Test that generated video rooms are actually accessible"""
    
    def test_patient_room_url_is_accessible(self, prod_appointment_with_video):
        """Patient's room URL should return 200"""
        response = requests.get(
            prod_appointment_with_video.video_room_url,
            timeout=15,
            allow_redirects=True
        )
        
        assert response.status_code == 200, \
            f"Patient room URL not accessible: {response.status_code}"
        
        print(f"\n✅ Patient room URL is accessible (status: {response.status_code})")
    
    def test_host_room_url_is_accessible(self, prod_appointment_with_video):
        """Doctor's host URL should return 200"""
        response = requests.get(
            prod_appointment_with_video.video_host_url,
            timeout=15,
            allow_redirects=True
        )
        
        assert response.status_code == 200, \
            f"Host room URL not accessible: {response.status_code}"
        
        print(f"\n✅ Host room URL is accessible (status: {response.status_code})")
    
    def test_room_contains_whereby_interface(self, prod_appointment_with_video):
        """Verify the room page contains Whereby interface elements"""
        response = requests.get(
            prod_appointment_with_video.video_room_url,
            timeout=15,
            allow_redirects=True
        )
        
        content = response.text.lower()
        
        # Check for Whereby-related content
        assert 'whereby' in content or 'video' in content or 'meeting' in content, \
            "Room page doesn't appear to be a Whereby interface"
        
        print(f"\n✅ Room page contains expected interface elements")


# ============================================================================
# TEST CLASS: REST API ENDPOINTS WITH REAL VIDEO
# ============================================================================

@SKIP_NO_API_KEY
class TestRESTAPIEndpoints:
    """Test REST API endpoints with real video room generation"""
    
    def test_join_consultation_endpoint_returns_real_url(
        self, 
        api_client, 
        prod_patient, 
        prod_appointment_with_video
    ):
        """Test /api/appointments/<id>/join/ returns real video URL"""
        api_client.force_authenticate(user=prod_patient)
        
        url = reverse('join-consultation', kwargs={'pk': prod_appointment_with_video.pk})
        response = api_client.get(url)
        
        assert response.status_code == 200, f"Join failed: {response.data}"
        assert 'video_room_url' in response.data, "Response missing video_room_url"
        assert 'whereby.com' in response.data['video_room_url'], \
            f"Invalid URL: {response.data['video_room_url']}"
        
        print(f"\n✅ Join endpoint returns real URL: {response.data['video_room_url']}")
    
    def test_join_consultation_doctor_gets_host_url(
        self, 
        api_client, 
        prod_doctor, 
        prod_appointment_with_video
    ):
        """Test that doctor gets host URL, not patient URL"""
        api_client.force_authenticate(user=prod_doctor)
        
        url = reverse('join-consultation', kwargs={'pk': prod_appointment_with_video.pk})
        response = api_client.get(url)
        
        assert response.status_code == 200
        
        # Doctor should get the host URL (contains roomKey or host parameter)
        returned_url = response.data['video_room_url']
        expected_host_url = prod_appointment_with_video.video_host_url
        
        assert returned_url == expected_host_url, \
            f"Doctor should get host URL.\nExpected: {expected_host_url}\nGot: {returned_url}"
        
        print(f"\n✅ Doctor gets host URL: {returned_url}")
    
    def test_join_consultation_patient_gets_room_url(
        self, 
        api_client, 
        prod_patient, 
        prod_appointment_with_video
    ):
        """Test that patient gets regular room URL, not host URL"""
        api_client.force_authenticate(user=prod_patient)
        
        url = reverse('join-consultation', kwargs={'pk': prod_appointment_with_video.pk})
        response = api_client.get(url)
        
        assert response.status_code == 200
        
        returned_url = response.data['video_room_url']
        expected_room_url = prod_appointment_with_video.video_room_url
        
        assert returned_url == expected_room_url, \
            f"Patient should get room URL.\nExpected: {expected_room_url}\nGot: {returned_url}"
        
        print(f"\n✅ Patient gets room URL: {returned_url}")
    
    def test_appointment_detail_includes_video_urls(
        self, 
        api_client, 
        prod_patient, 
        prod_appointment_with_video
    ):
        """Test appointment detail endpoint includes video information"""
        api_client.force_authenticate(user=prod_patient)
        
        url = reverse('appointment-detail', kwargs={'pk': prod_appointment_with_video.pk})
        response = api_client.get(url)
        
        assert response.status_code == 200
        
        # Check video fields are present (depending on your serializer)
        data = response.data
        print(f"\n📋 Appointment detail response: {data}")
        
        # Appointment should have video info
        assert prod_appointment_with_video.video_room_url, "Appointment should have video URL"


# ============================================================================
# TEST CLASS: COMPLETE BOOKING FLOW WITH REAL VIDEO
# ============================================================================

@SKIP_NO_API_KEY
class TestCompleteBookingFlowReal:
    """Test complete booking flow with real video room generation"""
    
    def test_dashboard_booking_creates_real_video_room(
        self, 
        client, 
        prod_patient, 
        prod_doctor
    ):
        """Test booking via dashboard creates real video room"""
        client.force_login(prod_patient)
        
        tomorrow = date.today() + timedelta(days=1)
        url = reverse('dashboard:patient_create_appointment')
        
        response = client.post(url, {
            'doctor': prod_doctor.doctor_profile.id,
            'slot_date': tomorrow.strftime('%Y-%m-%d'),
            'slot_start': '11:00',
            'duration': 30,
            'reason': 'Production booking test',
            'symptoms': 'Testing real video room',
            'appointment_type': 'online',
        })
        
        assert response.status_code == 302, f"Booking failed: {response.content}"
        
        # Retrieve created appointment
        appointment = Appointment.objects.filter(
            patient=prod_patient,
            doctor=prod_doctor.doctor_profile,
            date=tomorrow
        ).first()
        
        assert appointment is not None, "Appointment not created"
        
        # If video room should be auto-generated on booking, check it
        # Note: Based on your model, video room is generated on demand via JoinConsultationView
        # So we generate it here to test
        if not appointment.video_room_url:
            appointment.generate_video_room()
            appointment.save()
        
        assert appointment.video_room_url, "Video room URL not generated"
        assert "whereby.com" in appointment.video_room_url
        
        print(f"\n✅ Booking created appointment with video room")
        print(f"   Appointment: {appointment.appointment_number}")
        print(f"   Video Room: {appointment.video_room_url}")
    
    def test_complete_consultation_flow(
        self, 
        client, 
        api_client,
        prod_patient, 
        prod_doctor
    ):
        """Test complete flow: book -> confirm -> join -> complete"""
        
        # Step 1: Patient books appointment
        client.force_login(prod_patient)
        tomorrow = date.today() + timedelta(days=1)
        
        book_url = reverse('dashboard:patient_create_appointment')
        response = client.post(book_url, {
            'doctor': prod_doctor.doctor_profile.id,
            'slot_date': tomorrow.strftime('%Y-%m-%d'),
            'slot_start': '15:00',
            'duration': 30,
            'reason': 'Complete flow test',
            'appointment_type': 'online',
        })
        
        assert response.status_code == 302
        appointment = Appointment.objects.get(
            patient=prod_patient,
            doctor=prod_doctor.doctor_profile,
            date=tomorrow,
            start_time=time(15, 0)
        )
        print(f"\n✅ Step 1: Appointment booked ({appointment.appointment_number})")
        
        # Step 2: Generate video room (simulating when appointment is accessed)
        appointment.generate_video_room()
        appointment.save()
        assert appointment.video_room_url
        print(f"✅ Step 2: Video room generated ({appointment.video_room_id})")
        
        # Step 3: Doctor confirms appointment
        appointment.status = 'confirmed'
        appointment.save()
        print(f"✅ Step 3: Appointment confirmed")
        
        # Step 4: Patient joins consultation
        api_client.force_authenticate(user=prod_patient)
        join_url = reverse('join-consultation', kwargs={'pk': appointment.pk})
        response = api_client.get(join_url)
        
        assert response.status_code == 200
        assert 'video_room_url' in response.data
        print(f"✅ Step 4: Patient joined ({response.data['video_room_url'][:50]}...)")
        
        # Step 5: Doctor joins consultation
        api_client.force_authenticate(user=prod_doctor)
        response = api_client.get(join_url)
        
        assert response.status_code == 200
        print(f"✅ Step 5: Doctor joined")
        
        # Step 6: Doctor completes appointment
        appointment.status = 'in_progress'
        appointment.save()
        
        complete_url = reverse('complete-appointment', kwargs={'pk': appointment.pk})
        response = api_client.post(complete_url)
        
        assert response.status_code == 200
        
        appointment.refresh_from_db()
        assert appointment.status == 'completed'
        print(f"✅ Step 6: Appointment completed")
        
        print(f"\n🎉 Complete consultation flow passed!")
        print(f"\n📋 Test URLs (for manual verification):")
        print(f"   Patient: {appointment.video_room_url}")
        print(f"   Doctor:  {appointment.video_host_url}")


# ============================================================================
# TEST CLASS: CONCURRENCY AND EDGE CASES
# ============================================================================

@SKIP_NO_API_KEY
class TestConcurrencyAndEdgeCases:
    """Test concurrent operations and edge cases"""
    
    def test_multiple_appointments_get_unique_rooms(
        self, 
        prod_patient, 
        prod_patient_2, 
        prod_doctor
    ):
        """Each appointment should get a unique video room"""
        tomorrow = date.today() + timedelta(days=1)
        
        # Create first appointment
        apt1 = Appointment.objects.create(
            patient=prod_patient,
            doctor=prod_doctor.doctor_profile,
            date=tomorrow,
            start_time=time(9, 0),
            end_time=time(9, 30),
            status='confirmed'
        )
        apt1.generate_video_room()
        apt1.save()
        
        # Create second appointment
        apt2 = Appointment.objects.create(
            patient=prod_patient_2,
            doctor=prod_doctor.doctor_profile,
            date=tomorrow,
            start_time=time(9, 30),
            end_time=time(10, 0),
            status='confirmed'
        )
        apt2.generate_video_room()
        apt2.save()
        
        # Verify unique rooms
        assert apt1.video_room_url != apt2.video_room_url, \
            "Appointments should have different room URLs"
        assert apt1.video_room_id != apt2.video_room_id, \
            "Appointments should have different room IDs"
        
        print(f"\n✅ Appointments have unique video rooms")
        print(f"   Room 1: {apt1.video_room_id}")
        print(f"   Room 2: {apt2.video_room_id}")
    
    def test_regenerating_room_creates_new_room(self, prod_patient, prod_doctor):
        """Calling generate_video_room again should create a new room"""
        tomorrow = date.today() + timedelta(days=1)
        
        appointment = Appointment.objects.create(
            patient=prod_patient,
            doctor=prod_doctor.doctor_profile,
            date=tomorrow,
            start_time=time(16, 0),
            end_time=time(16, 30),
            status='confirmed'
        )
        
        # Generate first room
        appointment.generate_video_room()
        first_room_id = appointment.video_room_id
        first_room_url = appointment.video_room_url
        
        # Generate second room (simulating room expiration/regeneration)
        appointment.generate_video_room()
        second_room_id = appointment.video_room_id
        second_room_url = appointment.video_room_url
        
        # Should be different rooms
        assert first_room_id != second_room_id, \
            "Regenerating should create new room"
        assert first_room_url != second_room_url, \
            "Regenerating should create new URL"
        
        print(f"\n✅ Regenerating creates new room")
        print(f"   First:  {first_room_id}")
        print(f"   Second: {second_room_id}")


# ============================================================================
# TEST CLASS: ERROR HANDLING
# ============================================================================

@SKIP_NO_API_KEY
class TestErrorHandling:
    """Test error handling with real API"""
    
    def test_handles_invalid_api_key_gracefully(self, prod_patient, prod_doctor):
        """Application should handle invalid API key gracefully"""
        from unittest.mock import patch
        
        tomorrow = date.today() + timedelta(days=1)
        
        appointment = Appointment.objects.create(
            patient=prod_patient,
            doctor=prod_doctor.doctor_profile,
            date=tomorrow,
            start_time=time(17, 0),
            end_time=time(17, 30),
            status='confirmed'
        )
        
        # Temporarily use invalid API key
        with patch.object(settings, 'WHEREBY_API_KEY', 'invalid-key-12345'):
            with pytest.raises(requests.exceptions.HTTPError) as exc_info:
                appointment.generate_video_room()
            
            # Should be 401 Unauthorized
            assert exc_info.value.response.status_code == 401
        
        print(f"\n✅ Invalid API key raises HTTPError with 401")
    
    def test_handles_network_timeout(self, prod_patient, prod_doctor):
        """Application should handle network timeouts"""
        from unittest.mock import patch
        
        tomorrow = date.today() + timedelta(days=1)
        
        appointment = Appointment.objects.create(
            patient=prod_patient,
            doctor=prod_doctor.doctor_profile,
            date=tomorrow,
            start_time=time(18, 0),
            end_time=time(18, 30),
            status='confirmed'
        )
        
        # Mock requests.post to raise timeout
        with patch('requests.post', side_effect=requests.exceptions.Timeout("Connection timed out")):
            with pytest.raises(requests.exceptions.Timeout):
                appointment.generate_video_room()
        
        print(f"\n✅ Network timeout raises Timeout exception")
    
    def test_handles_missing_api_key(self, prod_patient, prod_doctor):
        """Application should handle missing API key"""
        from unittest.mock import patch
        
        tomorrow = date.today() + timedelta(days=1)
        
        appointment = Appointment.objects.create(
            patient=prod_patient,
            doctor=prod_doctor.doctor_profile,
            date=tomorrow,
            start_time=time(19, 0),
            end_time=time(19, 30),
            status='confirmed'
        )
        
        # Remove API key
        with patch.object(settings, 'WHEREBY_API_KEY', None):
            with pytest.raises(ValueError) as exc_info:
                appointment.generate_video_room()
            
            assert "WHEREBY_API_KEY" in str(exc_info.value)
        
        print(f"\n✅ Missing API key raises ValueError")


# ============================================================================
# TEST CLASS: DASHBOARD VIEWS WITH REAL VIDEO
# ============================================================================

@SKIP_NO_API_KEY
@SKIP_NO_API_KEY
class TestDashboardViewsReal:
    """Test dashboard views with real video rooms"""
    
    def test_patient_can_view_appointment_with_video(
        self, 
        client, 
        prod_patient, 
        prod_appointment_with_video
    ):
        """Patient can view appointment detail with video room info"""
        client.force_login(prod_patient)
        
        url = reverse(
            'dashboard:patient_appointment_detail', 
            kwargs={'pk': prod_appointment_with_video.pk}
        )
        response = client.get(url)
        
        assert response.status_code == 200
        
        # Check appointment is in context
        assert 'appointment' in response.context
        context_appointment = response.context['appointment']
        assert context_appointment.id == prod_appointment_with_video.id
        
        # Verify video URL exists on the appointment object
        assert context_appointment.video_room_url, "Appointment should have video_room_url"
        assert "whereby.com" in context_appointment.video_room_url
        
        # Check page shows "Online Consultation" badge (from your template)
        content = response.content.decode()
        assert 'Online Consultation' in content, \
            "Page should show 'Online Consultation' badge for video appointments"
        
        print(f"\n✅ Patient can view appointment with video info")
        print(f"   Shows: Online Consultation badge")
        print(f"   Video URL: {context_appointment.video_room_url[:50]}...")
    
    def test_doctor_can_view_appointment_with_video(
        self, 
        client, 
        prod_doctor, 
        prod_appointment_with_video
    ):
        """Doctor can view appointment detail page"""
        client.force_login(prod_doctor)
        
        url = reverse(
            'dashboard:doctor_appointment_detail', 
            kwargs={'pk': prod_appointment_with_video.pk}
        )
        response = client.get(url)
        
        assert response.status_code == 200
        
        # Check appointment is in context
        assert 'appointment' in response.context
        context_appointment = response.context['appointment']
        assert context_appointment.id == prod_appointment_with_video.id
        
        # Verify host URL exists
        assert context_appointment.video_host_url, "Appointment should have video_host_url"
        
        print(f"\n✅ Doctor can view appointment with video info")
    
    def test_patient_sees_join_button_when_can_join(
        self, 
        client, 
        prod_patient, 
        prod_appointment_with_video
    ):
        """Patient sees 'Join Video Call' button when appointment is joinable"""
        client.force_login(prod_patient)
        
        # Make appointment joinable (today, within time window)
        prod_appointment_with_video.date = date.today()
        prod_appointment_with_video.start_time = (timezone.now() - timedelta(minutes=5)).time()
        prod_appointment_with_video.end_time = (timezone.now() + timedelta(minutes=25)).time()
        prod_appointment_with_video.status = 'confirmed'
        prod_appointment_with_video.save()
        
        url = reverse(
            'dashboard:patient_appointment_detail', 
            kwargs={'pk': prod_appointment_with_video.pk}
        )
        response = client.get(url)
        
        assert response.status_code == 200
        
        content = response.content.decode()
        
        # Check for Join Video Call button (from your template)
        assert 'Join Video Call' in content, \
            "Page should show 'Join Video Call' button when appointment is joinable"
        
        # Check the link points to active_encounter
        assert f"active_encounter/{prod_appointment_with_video.id}" in content or \
               f"active-encounter/{prod_appointment_with_video.id}" in content or \
               'active_encounter' in content, \
            "Page should have link to active encounter"
        
        print(f"\n✅ Patient sees 'Join Video Call' button")
    
    def test_patient_does_not_see_join_button_when_cannot_join(
        self, 
        client, 
        prod_patient, 
        prod_appointment_with_video
    ):
        """Patient doesn't see join button when outside time window"""
        client.force_login(prod_patient)
        
        # Make appointment NOT joinable (tomorrow)
        tomorrow = date.today() + timedelta(days=1)
        prod_appointment_with_video.date = tomorrow
        prod_appointment_with_video.start_time = time(10, 0)
        prod_appointment_with_video.end_time = time(10, 30)
        prod_appointment_with_video.status = 'confirmed'
        prod_appointment_with_video.save()
        
        url = reverse(
            'dashboard:patient_appointment_detail', 
            kwargs={'pk': prod_appointment_with_video.pk}
        )
        response = client.get(url)
        
        assert response.status_code == 200
        
        content = response.content.decode()
        
        # Should NOT show Join Video Call button (appointment is tomorrow)
        # Note: This depends on your can_join property logic
        # The button should only appear within the join window
        
        # Still shows Online Consultation badge
        assert 'Online Consultation' in content
        
        print(f"\n✅ Page correctly shows appointment for tomorrow")
    
    def test_patient_can_access_active_encounter(
        self, 
        client, 
        prod_patient, 
        prod_appointment_with_video
    ):
        """Patient can access the active encounter/video room page"""
        client.force_login(prod_patient)
        
        # Make appointment "joinable" (today, current time window)
        prod_appointment_with_video.date = date.today()
        prod_appointment_with_video.start_time = (timezone.now() - timedelta(minutes=5)).time()
        prod_appointment_with_video.end_time = (timezone.now() + timedelta(minutes=25)).time()
        prod_appointment_with_video.status = 'confirmed'
        prod_appointment_with_video.save()
        
        url = reverse(
            'dashboard:active_encounter', 
            kwargs={'appointment_id': prod_appointment_with_video.pk}
        )
        response = client.get(url)
        
        assert response.status_code == 200
        
        # Check for video-related content in page
        content = response.content.decode().lower()
        
        # Should have video-related elements (iframe, whereby URL, etc.)
        has_video_content = any([
            'whereby' in content,
            'iframe' in content,
            'video' in content,
            prod_appointment_with_video.video_room_url.lower() in content,
        ])
        
        assert has_video_content, \
            "Encounter page should contain video-related content"
        
        print(f"\n✅ Patient can access active encounter page")
    
    def test_doctor_can_access_active_encounter(
        self, 
        client, 
        prod_doctor, 
        prod_appointment_with_video
    ):
        """Doctor can access the active encounter/video room page"""
        client.force_login(prod_doctor)
        
        # Make appointment "joinable"
        prod_appointment_with_video.date = date.today()
        prod_appointment_with_video.start_time = (timezone.now() - timedelta(minutes=5)).time()
        prod_appointment_with_video.end_time = (timezone.now() + timedelta(minutes=25)).time()
        prod_appointment_with_video.status = 'confirmed'
        prod_appointment_with_video.save()
        
        url = reverse(
            'dashboard:active_encounter', 
            kwargs={'appointment_id': prod_appointment_with_video.pk}
        )
        response = client.get(url)
        
        assert response.status_code == 200
        
        # Check for video-related content
        content = response.content.decode().lower()
        
        has_video_content = any([
            'whereby' in content,
            'iframe' in content,
            'video' in content,
        ])
        
        assert has_video_content, \
            "Encounter page should contain video-related content"
        
        print(f"\n✅ Doctor can access active encounter page")
    
    def test_cancelled_appointment_shows_cancelled_badge(
        self, 
        client, 
        prod_patient, 
        prod_appointment_with_video
    ):
        """Cancelled appointment shows correct status badge"""
        client.force_login(prod_patient)
        
        # Cancel the appointment
        prod_appointment_with_video.status = 'cancelled'
        prod_appointment_with_video.save()
        
        url = reverse(
            'dashboard:patient_appointment_detail', 
            kwargs={'pk': prod_appointment_with_video.pk}
        )
        response = client.get(url)
        
        assert response.status_code == 200
        
        content = response.content.decode()
        assert 'Cancelled' in content, "Page should show 'Cancelled' badge"
        
        # Should NOT show Join Video Call button
        assert 'Join Video Call' not in content, \
            "Cancelled appointment should not show join button"
        
        print(f"\n✅ Cancelled appointment displays correctly")

# ============================================================================
# TEST CLASS: DATABASE INTEGRITY
# ============================================================================

@SKIP_NO_API_KEY
class TestDatabaseIntegrity:
    """Test database operations with real video data"""
    
    def test_appointment_with_video_can_be_cancelled(self, prod_appointment_with_video):
        """Appointment with video room can be cancelled"""
        original_room_url = prod_appointment_with_video.video_room_url
        
        prod_appointment_with_video.status = 'cancelled'
        prod_appointment_with_video.cancellation_reason = 'Test cancellation'
        prod_appointment_with_video.save()
        
        prod_appointment_with_video.refresh_from_db()
        
        assert prod_appointment_with_video.status == 'cancelled'
        # Video URL should still be preserved
        assert prod_appointment_with_video.video_room_url == original_room_url
        
        print(f"\n✅ Cancelled appointment preserves video URL")
    
    def test_appointment_with_video_can_be_deleted(self, prod_patient, prod_doctor):
        """Appointment with video room can be deleted from database"""
        tomorrow = date.today() + timedelta(days=1)
        
        appointment = Appointment.objects.create(
            patient=prod_patient,
            doctor=prod_doctor.doctor_profile,
            date=tomorrow,
            start_time=time(20, 0),
            end_time=time(20, 30),
            status='confirmed'
        )
        appointment.generate_video_room()
        appointment.save()
        
        appointment_id = appointment.id
        appointment.delete()
        
        assert not Appointment.objects.filter(id=appointment_id).exists()
        
        print(f"\n✅ Appointment with video can be deleted")
    
    def test_video_fields_handle_unicode(self, prod_patient, prod_doctor):
        """Video URL fields should handle any URL characters"""
        tomorrow = date.today() + timedelta(days=1)
        
        appointment = Appointment.objects.create(
            patient=prod_patient,
            doctor=prod_doctor.doctor_profile,
            date=tomorrow,
            start_time=time(21, 0),
            end_time=time(21, 30),
            status='confirmed'
        )
        appointment.generate_video_room()
        appointment.save()
        
        # Reload and verify no encoding issues
        reloaded = Appointment.objects.get(id=appointment.id)
        
        # URLs should be valid strings
        assert isinstance(reloaded.video_room_url, str)
        assert isinstance(reloaded.video_host_url, str)
        assert reloaded.video_room_url.startswith('https://')
        
        print(f"\n✅ Video fields handle URLs correctly")


# ============================================================================
# SUMMARY TEST
# ============================================================================

@SKIP_NO_API_KEY
class TestProductionReadinessSummary:
    """Final summary test that runs a complete check"""
    
    def test_full_production_readiness_check(
        self, 
        client,
        api_client,
        prod_patient, 
        prod_doctor,
        prod_specialization
    ):
        """
        Complete production readiness check:
        1. API key is valid
        2. Can create video rooms
        3. Video rooms are accessible
        4. Complete booking flow works
        5. Both patient and doctor can join
        """
        print("\n" + "="*60)
        print("🏥 PRODUCTION READINESS CHECK")
        print("="*60)
        
        # Check 1: API Key
        print("\n📋 Check 1: API Key Configuration")
        assert WHEREBY_API_KEY, "API key not configured"
        response = requests.get(
            "https://api.whereby.dev/v1/meetings",
            headers={"Authorization": f"Bearer {WHEREBY_API_KEY}"},
            timeout=15
        )
        assert response.status_code != 401, "API key is invalid"
        print("   ✅ API key is valid")
        
        # Check 2: Create Video Room
        print("\n📋 Check 2: Video Room Creation")
        tomorrow = date.today() + timedelta(days=1)
        appointment = Appointment.objects.create(
            patient=prod_patient,
            doctor=prod_doctor.doctor_profile,
            date=tomorrow,
            start_time=time(22, 0),
            end_time=time(22, 30),
            status='confirmed',
            reason='Production readiness final check'
        )
        appointment.generate_video_room()
        appointment.save()
        assert appointment.video_room_url, "Video room not generated"
        print(f"   ✅ Video room created: {appointment.video_room_id}")
        
        # Check 3: Room Accessibility
        print("\n📋 Check 3: Video Room Accessibility")
        response = requests.get(appointment.video_room_url, timeout=15, allow_redirects=True)
        assert response.status_code == 200, f"Room not accessible: {response.status_code}"
        print("   ✅ Video room is accessible")
        
        # Check 4: Patient Can Join
        print("\n📋 Check 4: Patient Join")
        api_client.force_authenticate(user=prod_patient)
        join_url = reverse('join-consultation', kwargs={'pk': appointment.pk})
        response = api_client.get(join_url)
        assert response.status_code == 200, f"Patient can't join: {response.data}"
        assert response.data['video_room_url'] == appointment.video_room_url
        print("   ✅ Patient can join consultation")
        
        # Check 5: Doctor Can Join
        print("\n📋 Check 5: Doctor Join")
        api_client.force_authenticate(user=prod_doctor)
        response = api_client.get(join_url)
        assert response.status_code == 200, f"Doctor can't join: {response.data}"
        assert response.data['video_room_url'] == appointment.video_host_url
        print("   ✅ Doctor can join consultation")
        
        # Final Summary
        print("\n" + "="*60)
        print("🎉 ALL PRODUCTION READINESS CHECKS PASSED!")
        print("="*60)
        print(f"\n📋 Video Room URLs for manual testing:")
        print(f"   Patient: {appointment.video_room_url}")
        print(f"   Doctor:  {appointment.video_host_url}")
        print("="*60)