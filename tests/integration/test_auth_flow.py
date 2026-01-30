# tests/integration/test_auth_flow.py
"""
Integration tests for Authentication Flow:
- Patient Registration → Email Verification → Login
- Doctor Registration → Email Verification → Admin Verification → Login
- Password Reset Flow
"""

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from unittest.mock import patch, MagicMock

User = get_user_model()


@pytest.mark.django_db
class TestPatientAuthFlow:
    """Test complete patient authentication journey"""
    
    def test_patient_registration_success(self, client):
        """Patient can register with valid data"""
        url = reverse('dashboard:register_patient')
        
        data = {
            'email': 'newpatient@test.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '+2341234567890',
        }
        
        with patch('dashboard.views.EmailService') as mock_email:
            mock_email.send_email_verification = MagicMock()
            mock_email.send_welcome_email = MagicMock()
            
            response = client.post(url, data)
        
        # Should redirect to verification sent page
        assert response.status_code == 302
        assert 'verification-sent' in response.url
        
        # User should be created
        user = User.objects.get(email='newpatient@test.com')
        assert user.user_type == 'patient'
        assert user.email_verified == False
        assert hasattr(user, 'patient_profile')
    
    def test_patient_registration_password_mismatch(self, client):
        """Registration fails with mismatched passwords"""
        url = reverse('dashboard:register_patient')
        
        data = {
            'email': 'test@test.com',
            'password': 'SecurePass123!',
            'password_confirm': 'DifferentPass123!',
            'first_name': 'John',
            'last_name': 'Doe',
        }
        
        response = client.post(url, data)
        
        # Should stay on page with error
        assert response.status_code == 200
        assert not User.objects.filter(email='test@test.com').exists()
    
    def test_patient_registration_duplicate_email(self, client, patient_user):
        """Registration fails with existing email"""
        url = reverse('dashboard:register_patient')
        
        data = {
            'email': patient_user.email,  # Already exists
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Another',
            'last_name': 'User',
        }
        
        response = client.post(url, data)
        
        # Should stay on page with error
        assert response.status_code == 200
    
    def test_email_verification_success(self, client):
        """User can verify email with valid token"""
        # Create unverified user
        user = User.objects.create_user(
            email='unverified@test.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            user_type='patient',
            email_verified=False
        )
        
        # Generate token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        url = reverse('dashboard:verify_email', kwargs={'uidb64': uid, 'token': token})
        response = client.get(url)
        
        # Should redirect to login
        assert response.status_code == 302
        assert 'login' in response.url
        
        # User should be verified
        user.refresh_from_db()
        assert user.email_verified == True
    
    def test_email_verification_invalid_token(self, client):
        """Verification fails with invalid token"""
        user = User.objects.create_user(
            email='test@test.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            user_type='patient',
            email_verified=False
        )
        
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        url = reverse('dashboard:verify_email', kwargs={'uidb64': uid, 'token': 'invalid-token'})
        response = client.get(url)
        
        # Should redirect with error
        assert response.status_code == 302
        
        # User should still be unverified
        user.refresh_from_db()
        assert user.email_verified == False
    
    def test_patient_login_verified_user(self, client):
        """Verified patient can login"""
        user = User.objects.create_user(
            email='verified@test.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            user_type='patient',
            email_verified=True
        )
        
        url = reverse('dashboard:login')
        response = client.post(url, {
            'email': 'verified@test.com',
            'password': 'testpass123'
        })
        
        # Should redirect to patient dashboard
        assert response.status_code == 302
        assert 'patient/dashboard' in response.url
    
    def test_patient_login_unverified_user(self, client):
        """Unverified patient cannot login"""
        user = User.objects.create_user(
            email='unverified@test.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            user_type='patient',
            email_verified=False
        )
        
        url = reverse('dashboard:login')
        response = client.post(url, {
            'email': 'unverified@test.com',
            'password': 'testpass123'
        })
        
        # Should stay on login page
        assert response.status_code == 200
    
    def test_patient_login_wrong_password(self, client, patient_user):
        """Login fails with wrong password"""
        patient_user.email_verified = True
        patient_user.save()
        
        url = reverse('dashboard:login')
        response = client.post(url, {
            'email': patient_user.email,
            'password': 'wrongpassword'
        })
        
        # Should stay on login page
        assert response.status_code == 200
    
    def test_patient_logout(self, client, patient_user):
        """Patient can logout"""
        # Login first
        client.force_login(patient_user)
        
        url = reverse('dashboard:logout')
        response = client.get(url)
        
        # Should redirect to login
        assert response.status_code == 302
        assert 'login' in response.url


@pytest.mark.django_db
class TestDoctorAuthFlow:
    """Test complete doctor authentication journey"""
    
    def test_doctor_registration_success(self, client, specialization):
        """Doctor can register with valid data"""
        url = reverse('dashboard:register_doctor')
        
        data = {
            'email': 'newdoctor@test.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone': '+2349876543210',
            'license_number': 'DOC99999',
            'specialization': specialization.id,
            'experience_years': 5,
            'consultation_fee': '5000.00',
            'education': 'Medical School',
        }
        
        with patch('dashboard.views.EmailService') as mock_email:
            mock_email.send_email_verification = MagicMock()
            mock_email.send_welcome_email = MagicMock()
            
            response = client.post(url, data)
        
        # Should redirect to verification sent page
        assert response.status_code == 302
        
        # User should be created with pending verification
        user = User.objects.get(email='newdoctor@test.com')
        assert user.user_type == 'doctor'
        assert hasattr(user, 'doctor_profile')
        assert user.doctor_profile.verification_status == 'pending'
    
    def test_doctor_login_verified(self, client, doctor_user):
        """Verified doctor can login"""
        doctor_user.email_verified = True
        doctor_user.save()
        
        url = reverse('dashboard:login')
        response = client.post(url, {
            'email': doctor_user.email,
            'password': 'testpass123'
        })
        
        # Should redirect to doctor dashboard
        assert response.status_code == 302
        assert 'doctor/dashboard' in response.url
    
    def test_doctor_login_rejected_profile(self, client, doctor_user):
        """Doctor with rejected profile cannot login"""
        doctor_user.email_verified = True
        doctor_user.save()
        doctor_user.doctor_profile.verification_status = 'rejected'
        doctor_user.doctor_profile.save()
        
        url = reverse('dashboard:login')
        response = client.post(url, {
            'email': doctor_user.email,
            'password': 'testpass123'
        })
        
        # Should stay on login page with error
        assert response.status_code == 200


@pytest.mark.django_db
class TestPasswordResetFlow:
    """Test password reset journey"""
    
    def test_forgot_password_request(self, client, patient_user):
        """User can request password reset"""
        url = reverse('dashboard:forgot_password')
        
        with patch('dashboard.views.EmailService') as mock_email:
            mock_email.send_password_reset = MagicMock()
            
            response = client.post(url, {'email': patient_user.email})
        
        # Should redirect with success message
        assert response.status_code == 302
    
    def test_reset_password_success(self, client, patient_user):
        """User can reset password with valid token"""
        token = default_token_generator.make_token(patient_user)
        uid = urlsafe_base64_encode(force_bytes(patient_user.pk))
        
        url = reverse('dashboard:reset_password', kwargs={'uidb64': uid, 'token': token})
        
        response = client.post(url, {
            'password': 'NewSecurePass123!',
            'password_confirm': 'NewSecurePass123!'
        })
        
        # Should redirect to login
        assert response.status_code == 302
        assert 'login' in response.url
        
        # Password should be changed
        patient_user.refresh_from_db()
        assert patient_user.check_password('NewSecurePass123!')
    
    def test_reset_password_invalid_token(self, client, patient_user):
        """Password reset fails with invalid token"""
        uid = urlsafe_base64_encode(force_bytes(patient_user.pk))
        
        url = reverse('dashboard:reset_password', kwargs={'uidb64': uid, 'token': 'invalid'})
        response = client.get(url)
        
        # Should redirect to forgot password
        assert response.status_code == 302
        assert 'forgot-password' in response.url