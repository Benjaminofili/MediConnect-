# tests/integration/test_video_consultation_real.py
"""
REAL Whereby API Integration Tests for Video Consultation

These tests make actual API calls to Whereby and require WHEREBY_API_KEY.
They test the complete video consultation flow without mocking.

Run with:
    # Option 1: Set environment variable (disables mocking for all tests)
    REAL_API_TESTS=true pytest tests/integration/test_video_consultation_real.py -v -s
    
    # Option 2: Use pytest marker (only disables mocking for these tests)
    pytest tests/integration/test_video_consultation_real.py -v -s -m real_api
    
    # Option 3: Run directly (will skip if no API key)
    pytest tests/integration/test_video_consultation_real.py -v -s
"""

import pytest
import os
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
from appointments.models import Appointment


# Skip all tests if no API key
pytestmark = [
    pytest.mark.django_db,
    pytest.mark.real_api,  # This marker disables the mock_whereby_api fixture
    pytest.mark.skipif(
        not os.getenv('WHEREBY_API_KEY') and not getattr(settings, 'WHEREBY_API_KEY', None),
        reason="WHEREBY_API_KEY not configured - set it in .env or environment"
    )
]


@pytest.fixture
def api_key():
    """Get Whereby API key"""
    return getattr(settings, 'WHEREBY_API_KEY', None) or os.getenv('WHEREBY_API_KEY')


class TestVideoConsultationRealAPI:
    """Test video consultation with real Whereby API"""
    
    def test_api_key_configured(self, api_key):
        """Verify API key is configured"""
        assert api_key, "WHEREBY_API_KEY must be set in .env or environment"
        assert len(api_key) > 10, "API key seems too short"
        print(f"\n✅ API Key configured: {api_key[:10]}...")
    
    def test_appointment_generates_real_video_room(self, patient_user, doctor_profile, api_key):
        """Test that appointment.generate_video_room() creates a real Whereby room"""
        tomorrow = date.today() + timedelta(days=1)
        
        appointment = Appointment.objects.create(
            patient=patient_user,
            doctor=doctor_profile,
            date=tomorrow,
            start_time="10:00",
            end_time="10:30",
            status='confirmed',
            reason='Real API test consultation'
        )
        
        # This will make a REAL API call to Whereby
        appointment.generate_video_room()
        appointment.save()
        
        print(f"\n📋 Appointment: {appointment.appointment_number}")
        print(f"🎥 Video Room URL: {appointment.video_room_url}")
        print(f"🎥 Host URL: {appointment.video_host_url}")
        print(f"🎥 Room ID: {appointment.video_room_id}")
        
        # Verify URLs were generated
        assert appointment.video_room_url, "No video_room_url generated"
        assert appointment.video_host_url, "No video_host_url generated"
        assert appointment.video_room_id, "No video_room_id generated"
        assert "whereby.com" in appointment.video_room_url, "URL should contain whereby.com"
        assert "whereby.com" in appointment.video_host_url, "Host URL should contain whereby.com"
    
    def test_patient_can_access_video_room(self, client, patient_user, doctor_profile, api_key):
        """Test patient can access the video consultation page with real room"""
        patient_user.email_verified = True
        patient_user.save()
        client.force_login(patient_user)
        
        tomorrow = date.today() + timedelta(days=1)
        appointment = Appointment.objects.create(
            patient=patient_user,
            doctor=doctor_profile,
            date=tomorrow,
            start_time="14:00",
            end_time="14:30",
            status='confirmed',
        )
        
        # Generate real video room
        appointment.generate_video_room()
        appointment.save()
        
        url = reverse('dashboard:active_encounter', kwargs={'appointment_id': appointment.pk})
        response = client.get(url)
        
        assert response.status_code == 200
        # Check that video URL is in the response
        assert appointment.video_room_url in str(response.content) or \
               'whereby' in str(response.content).lower()
        
        print(f"\n✅ Patient can access video room: {appointment.video_room_url}")
    
    def test_doctor_can_access_video_room(self, client, doctor_user, patient_user, api_key):
        """Test doctor can access the video consultation page with real room"""
        doctor_user.email_verified = True
        doctor_user.save()
        client.force_login(doctor_user)
        
        tomorrow = date.today() + timedelta(days=1)
        appointment = Appointment.objects.create(
            patient=patient_user,
            doctor=doctor_user.doctor_profile,
            date=tomorrow,
            start_time="15:00",
            end_time="15:30",
            status='confirmed',
        )
        
        # Generate real video room
        appointment.generate_video_room()
        appointment.save()
        
        url = reverse('dashboard:active_encounter', kwargs={'appointment_id': appointment.pk})
        response = client.get(url)
        
        assert response.status_code == 200
        # Doctor should get host URL
        assert appointment.video_host_url in str(response.content) or \
               'whereby' in str(response.content).lower()
        
        print(f"\n✅ Doctor can access video room: {appointment.video_host_url}")
    
    def test_complete_booking_flow_with_real_video(self, client, patient_user, doctor_profile, api_key):
        """Test complete appointment booking flow with real video room generation"""
        patient_user.email_verified = True
        patient_user.save()
        client.force_login(patient_user)
        
        tomorrow = date.today() + timedelta(days=1)
        url = reverse('dashboard:patient_create_appointment')
        
        data = {
            'doctor': doctor_profile.id,
            'slot_date': tomorrow.strftime('%Y-%m-%d'),
            'slot_start': '16:00',
            'duration': 30,
            'reason': 'Real API test',
            'symptoms': 'Testing video consultation',
            'appointment_type': 'online',
        }
        
        response = client.post(url, data)
        
        # Should redirect to appointments list
        assert response.status_code == 302
        
        # Verify appointment was created with video room
        appointment = Appointment.objects.filter(
            patient=patient_user,
            doctor=doctor_profile,
            date=tomorrow
        ).first()
        
        assert appointment is not None
        assert appointment.status == 'pending'
        
        # Video room should be generated for online appointments
        assert appointment.video_room_url, "Video room should be generated for online appointments"
        assert appointment.video_host_url, "Host URL should be generated"
        
        print(f"\n✅ Appointment created: {appointment.appointment_number}")
        print(f"🎥 Video Room: {appointment.video_room_url}")
        print(f"🎥 Host Room: {appointment.video_host_url}")


class TestVideoRoomAccessibility:
    """Test that generated video rooms are actually accessible"""
    
    def test_video_room_url_is_accessible(self, patient_user, doctor_profile, api_key):
        """Test that generated video room URL is accessible via HTTP"""
        import requests
        
        tomorrow = date.today() + timedelta(days=1)
        appointment = Appointment.objects.create(
            patient=patient_user,
            doctor=doctor_profile,
            date=tomorrow,
            start_time="17:00",
            end_time="17:30",
            status='confirmed',
        )
        
        appointment.generate_video_room()
        appointment.save()
        
        # Check if room URL is accessible
        try:
            response = requests.get(
                appointment.video_room_url,
                timeout=10,
                allow_redirects=True
            )
            
            print(f"\n🌐 Room URL Status: {response.status_code}")
            print(f"🌐 Final URL: {response.url}")
            
            # Whereby returns 200 for valid room pages
            assert response.status_code == 200, \
                f"Room URL not accessible: {response.status_code}"
            
            print(f"✅ Video room is accessible")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to access video room: {e}")
    
    def test_host_room_url_is_accessible(self, patient_user, doctor_profile, api_key):
        """Test that generated host room URL is accessible via HTTP"""
        import requests
        
        tomorrow = date.today() + timedelta(days=1)
        appointment = Appointment.objects.create(
            patient=patient_user,
            doctor=doctor_profile,
            date=tomorrow,
            start_time="18:00",
            end_time="18:30",
            status='confirmed',
        )
        
        appointment.generate_video_room()
        appointment.save()
        
        # Check if host URL is accessible
        try:
            response = requests.get(
                appointment.video_host_url,
                timeout=10,
                allow_redirects=True
            )
            
            print(f"\n🌐 Host URL Status: {response.status_code}")
            print(f"🌐 Final URL: {response.url}")
            
            assert response.status_code == 200, \
                f"Host URL not accessible: {response.status_code}"
            
            print(f"✅ Host room is accessible")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to access host room: {e}")


class TestVideoConsultationEndToEnd:
    """End-to-end test of video consultation flow with real API"""
    
    def test_complete_video_consultation_flow(self, client, patient_user, doctor_user, api_key):
        """Test complete flow: booking -> video room -> access"""
        # Setup
        patient_user.email_verified = True
        doctor_user.email_verified = True
        patient_user.save()
        doctor_user.save()
        
        # Step 1: Patient books appointment
        client.force_login(patient_user)
        tomorrow = date.today() + timedelta(days=1)
        
        book_url = reverse('dashboard:patient_create_appointment')
        response = client.post(book_url, {
            'doctor': doctor_user.doctor_profile.id,
            'slot_date': tomorrow.strftime('%Y-%m-%d'),
            'slot_start': '19:00',
            'duration': 30,
            'reason': 'E2E test',
            'appointment_type': 'online',
        })
        
        assert response.status_code == 302
        appointment = Appointment.objects.get(patient=patient_user, date=tomorrow)
        
        # Verify video room was created
        assert appointment.video_room_url, "Video room should be created"
        assert appointment.video_host_url, "Host URL should be created"
        
        print(f"\n✅ Step 1: Appointment booked with video room")
        print(f"   Room: {appointment.video_room_url}")
        
        # Step 2: Doctor confirms appointment
        client.logout()
        client.force_login(doctor_user)
        appointment.status = 'confirmed'
        appointment.save()
        
        print(f"✅ Step 2: Appointment confirmed")
        
        # Step 3: Patient accesses video room
        client.logout()
        client.force_login(patient_user)
        
        encounter_url = reverse('dashboard:active_encounter', kwargs={'appointment_id': appointment.pk})
        response = client.get(encounter_url)
        
        assert response.status_code == 200
        print(f"✅ Step 3: Patient can access video room")
        
        # Step 4: Doctor accesses video room
        client.logout()
        client.force_login(doctor_user)
        response = client.get(encounter_url)
        
        assert response.status_code == 200
        print(f"✅ Step 4: Doctor can access video room")
        
        print(f"\n🎉 Complete video consultation flow tested successfully!")
        print(f"\n📋 Test URLs (for manual verification):")
        print(f"   Patient: {appointment.video_room_url}")
        print(f"   Doctor:  {appointment.video_host_url}")




