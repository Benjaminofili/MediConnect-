"""
Test script to verify email configuration.
Run this to test if emails are being sent correctly.

Usage:
    python test_email.py recipient@example.com
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings


def test_email(recipient_email):
    """Send a test email to verify configuration."""
    print("=" * 60)
    print("Email Configuration Test")
    print("=" * 60)
    print(f"Backend: {settings.EMAIL_BACKEND}")
    print(f"Host: {settings.EMAIL_HOST}")
    print(f"Port: {settings.EMAIL_PORT}")
    print(f"Use TLS: {settings.EMAIL_USE_TLS}")
    print(f"Use SSL: {settings.EMAIL_USE_SSL}")
    print(f"Host User: {settings.EMAIL_HOST_USER}")
    print(f"From Email: {settings.DEFAULT_FROM_EMAIL}")
    print("=" * 60)
    
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        print("\n❌ ERROR: Email credentials not configured!")
        print("Please set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in your .env file")
        return False
    
    try:
        print(f"\n📧 Sending test email to: {recipient_email}")
        
        result = send_mail(
            subject='MediConnect - Email Configuration Test',
            message='This is a test email from MediConnect. If you receive this, your email configuration is working correctly!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        
        if result == 1:
            print("✅ Email sent successfully!")
            print(f"Check the inbox for: {recipient_email}")
            return True
        else:
            print("❌ Email sending failed (no exception but result was 0)")
            return False
            
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        print("\nCommon issues:")
        print("- Gmail: Make sure you're using an App Password, not your regular password")
        print("- Check that 2-Factor Authentication is enabled on your Google account")
        print("- Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are correct")
        print("- Check your internet connection")
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_email.py recipient@example.com")
        sys.exit(1)
    
    recipient = sys.argv[1]
    success = test_email(recipient)
    sys.exit(0 if success else 1)
