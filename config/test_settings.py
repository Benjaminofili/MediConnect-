# config/test_settings.py

from .settings import *

# =============================================
# TEST-SPECIFIC SETTINGS
# =============================================

# FIX: Override STORAGES for Django 4.2+ (not STATICFILES_STORAGE)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Remove WhiteNoise middleware
MIDDLEWARE = [m for m in MIDDLEWARE if 'whitenoise' not in m.lower()]

# Faster password hashing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

DEBUG = False

print("✅ Test settings loaded - WhiteNoise disabled")