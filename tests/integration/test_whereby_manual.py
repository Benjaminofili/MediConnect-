# tests/integration/test_whereby_manual.py
"""
REAL Whereby API Tests
Run with: pytest tests/integration/test_whereby_manual.py -v -s
"""

import pytest
import os
from django.conf import settings
from datetime import date, time, timedelta


# Skip if no API key
pytestmark = pytest.mark.skipif(
    not os.getenv('WHEREBY_API_KEY') and not getattr(settings, 'WHEREBY_API_KEY', None),
    reason="WHEREBY_API_KEY not configured"
)


@pytest.mark.django_db
def test_whereby_api_key_exists():
    """Verify API key is configured"""
    api_key = getattr(settings, 'WHEREBY_API_KEY', None) or os.getenv('WHEREBY_API_KEY')
    assert api_key, "WHEREBY_API_KEY must be set"
    print(f"✅ API Key found: {api_key[:10]}...")


@pytest.mark.django_db
def test_create_whereby_room_directly():
    """Test creating a Whereby room via direct API call"""
    import requests
    from datetime import datetime, timedelta
    
    api_key = getattr(settings, 'WHEREBY_API_KEY', None) or os.getenv('WHEREBY_API_KEY')
    if not api_key:
        pytest.skip("No API key")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
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
    
    assert response.status_code == 201, f"API call failed: {response.text}"
    
    room_data = response.json()
    print(f"✅ Room URL: {room_data.get('roomUrl')}")
    print(f"✅ Host URL: {room_data.get('hostRoomUrl')}")


@pytest.mark.django_db
def test_appointment_video_room(patient_user, doctor_profile):
    """Test that appointment model generates real video room"""
    from appointments.models import Appointment
    
    api_key = getattr(settings, 'WHEREBY_API_KEY', None) or os.getenv('WHEREBY_API_KEY')
    if not api_key:
        pytest.skip("No API key")
    
    tomorrow = date.today() + timedelta(days=1)
    
    appointment = Appointment.objects.create(
        patient=patient_user,
        doctor=doctor_profile,
        date=tomorrow,
        start_time=time(10, 0),
        end_time=time(10, 30),
        status='confirmed',
        reason='Test consultation'
    )
    
    # Generate video room - this will use REAL API
    appointment.generate_video_room()
    appointment.save()
    
    print(f"\n🎥 Video Room URL: {appointment.video_room_url}")
    print(f"🎥 Host URL: {appointment.video_host_url}")
    
    assert appointment.video_room_url, "No video_room_url generated"
    assert "whereby.com" in appointment.video_room_url