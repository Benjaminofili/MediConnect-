# tests/integration/test_whereby_real.py
"""
REAL Whereby API Tests - Run manually to verify video integration
These tests make actual API calls and require WHEREBY_API_KEY

Run with: pytest tests/integration/test_whereby_real.py -v -s
"""

import pytest
import os
from django.conf import settings
from datetime import date, timedelta


# Skip all tests if no API key
pytestmark = pytest.mark.skipif(
    not os.getenv('WHEREBY_API_KEY') and not getattr(settings, 'WHEREBY_API_KEY', None),
    reason="WHEREBY_API_KEY not configured - skipping real API tests"
)


@pytest.mark.django_db
class TestWherebyRealAPI:
    """Test actual Whereby API integration"""
    
    def test_whereby_api_key_exists(self):
        """Verify API key is configured"""
        api_key = getattr(settings, 'WHEREBY_API_KEY', None) or os.getenv('WHEREBY_API_KEY')
        assert api_key, "WHEREBY_API_KEY must be set"
        assert len(api_key) > 10, "API key seems too short"
        print(f"✅ API Key found: {api_key[:10]}...")
    
    def test_create_whereby_room_directly(self):
        """Test creating a Whereby room via direct API call"""
        import requests
        from datetime import datetime, timedelta
        
        api_key = getattr(settings, 'WHEREBY_API_KEY', None) or os.getenv('WHEREBY_API_KEY')
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        # Room expires in 1 day
        end_date = (datetime.now() + timedelta(days=1)).isoformat()
        
        data = {
            "endDate": end_date,
            "fields": ["hostRoomUrl"],
        }
        
        response = requests.post(
            "https://api.whereby.dev/v1/meetings",
            json=data,
            headers=headers,
            timeout=30,
        )
        
        print(f"\n📡 API Response Status: {response.status_code}")
        print(f"📡 API Response: {response.json()}")
        
        assert response.status_code == 201, f"API call failed: {response.text}"
        
        room_data = response.json()
        assert "roomUrl" in room_data, "No roomUrl in response"
        assert "hostRoomUrl" in room_data, "No hostRoomUrl in response"
        
        print(f"✅ Room URL: {room_data['roomUrl']}")
        print(f"✅ Host URL: {room_data['hostRoomUrl']}")
    
    def test_appointment_generates_video_room(self, patient_user, doctor_profile):
        """Test that appointment model generates real video room"""
        from appointments.models import Appointment
        
        tomorrow = date.today() + timedelta(days=1)
        
        # Create appointment without video room
        appointment = Appointment.objects.create(
            patient=patient_user,
            doctor=doctor_profile,
            date=tomorrow,
            start_time="10:00",
            end_time="10:30",
            status='confirmed',
            reason='Test consultation'
        )
        
        # Generate video room
        appointment.generate_video_room()
        appointment.save()
        
        print(f"\n🎥 Video Room URL: {appointment.video_room_url}")
        print(f"🎥 Host URL: {appointment.video_host_url}")
        print(f"🎥 Room ID: {appointment.video_room_id}")
        
        assert appointment.video_room_url, "No video_room_url generated"
        assert appointment.video_host_url, "No video_host_url generated"
        assert appointment.video_room_id, "No video_room_id generated"
        assert "whereby.com" in appointment.video_room_url
    
    def test_video_room_url_is_accessible(self, patient_user, doctor_profile):
        """Test that generated video room URL is actually accessible"""
        import requests
        from appointments.models import Appointment
        
        tomorrow = date.today() + timedelta(days=1)
        
        appointment = Appointment.objects.create(
            patient=patient_user,
            doctor=doctor_profile,
            date=tomorrow,
            start_time="11:00",
            end_time="11:30",
            status='confirmed',
        )
        
        appointment.generate_video_room()
        appointment.save()
        
        # Check if room URL is accessible (should return 200 or redirect)
        response = requests.get(appointment.video_room_url, timeout=10, allow_redirects=True)
        
        print(f"\n🌐 Room URL Status: {response.status_code}")
        print(f"🌐 Final URL: {response.url}")
        
        # Whereby returns 200 for valid room pages
        assert response.status_code == 200, f"Room URL not accessible: {response.status_code}"


@pytest.mark.django_db
class TestVideoConsultationRealFlow:
    """Test complete video consultation with real Whereby"""
    
    def test_complete_video_consultation_setup(self, client, patient_user, doctor_user):
        """Test full video consultation setup"""
        from appointments.models import Appointment
        from django.urls import reverse
        
        # Create appointment
        tomorrow = date.today() + timedelta(days=1)
        
        appointment = Appointment.objects.create(
            patient=patient_user,
            doctor=doctor_user.doctor_profile,
            date=tomorrow,
            start_time="14:00",
            end_time="14:30",
            status='confirmed',
        )
        
        # Generate video room
        appointment.generate_video_room()
        appointment.save()
        
        print(f"\n📋 Appointment: {appointment.appointment_number}")
        print(f"🎥 Patient URL: {appointment.video_room_url}")
        print(f"🎥 Doctor URL: {appointment.video_host_url}")
        
        # Test patient can access encounter page
        client.force_login(patient_user)
        url = reverse('dashboard:active_encounter', kwargs={'appointment_id': appointment.pk})
        response = client.get(url)
        
        assert response.status_code == 200
        assert appointment.video_room_url in str(response.content) or \
               'whereby' in str(response.content).lower()
        
        print("✅ Patient can access encounter page")
        
        # Test doctor can access encounter page
        client.logout()
        client.force_login(doctor_user)
        response = client.get(url)
        
        assert response.status_code == 200
        print("✅ Doctor can access encounter page")
        
        # Return URLs for manual testing
        print("\n" + "="*50)
        print("🧪 MANUAL TEST - Open these URLs in browser:")
        print("="*50)
        print(f"Patient URL: {appointment.video_room_url}")
        print(f"Doctor URL:  {appointment.video_host_url}")
        print("="*50)