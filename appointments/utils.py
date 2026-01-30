import time
import requests
from django.conf import settings

def create_daily_room(appointment_id):
    """Create a Daily.co room for the consultation"""
    url = "https://api.daily.co/v1/rooms"
    headers = {
        "Authorization": f"Bearer {settings.DAILY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    room_name = f"mediconnect-{appointment_id}"
    
    data = {
        "name": room_name,
        "properties": {
            "enable_screenshare": True,
            "enable_chat": True,
            "start_video_off": False,
            "start_audio_off": False,
            "owner_only_broadcast": False,
            # --- FIX: Changed from 'cloud' to 'none' for free plan ---
            "enable_recording": "none", 
            "max_participants": 2,
            "exp": int(time.time()) + 7200 
        }
    }
    
    # Debugging
    print(f"Creating Daily Room: {room_name}")
    response = requests.post(url, json=data, headers=headers)
    print(f"Daily API Status: {response.status_code}")
    
    # If room already exists, fetch it
    if response.status_code == 400 and "already exists" in response.text:
        print("Room exists, fetching details...")
        get_resp = requests.get(f"{url}/{room_name}", headers=headers)
        return get_resp.json()
    
    # If other error, print it
    if response.status_code != 200:
        print(f"Daily API Error: {response.text}")
        
    return response.json()

def get_daily_token(room_name, user_name, is_owner=False):
    """Generate meeting token with specific permissions"""
    url = "https://api.daily.co/v1/meeting-tokens"
    headers = {
        "Authorization": f"Bearer {settings.DAILY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "properties": {
            "room_name": room_name,
            "user_name": user_name,
            "is_owner": is_owner,
            # --- FIX: Changed from 'cloud' to 'none' ---
            "enable_recording": "none" 
        }
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()