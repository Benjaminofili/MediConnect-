import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from unittest.mock import patch, MagicMock

from accounts.models import PatientProfile, DoctorProfile
from doctors.models import Specialization
from decimal import Decimal

User = get_user_model()


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def verified_doctor_user(db, specialization):
    """Create a verified doctor user for testing"""
    user = User.objects.create_user(
        email='verified.doctor@test.com',
        password='testpass123',
        first_name='Verified',
        last_name='Doctor',
        user_type='doctor',
        email_verified=True
    )
    DoctorProfile.objects.create(
        user=user,
        specialization=specialization,
        license_number='VERDOC123',
        experience_years=5,
        education='Test Medical School',
        consultation_fee=Decimal('5000.00'),
        verification_status='verified'
    )
    return user


@pytest.fixture
def verified_patient_user(db):
    """Create a verified patient user for testing"""
    user = User.objects.create_user(
        email='verified.patient@test.com',
        password='testpass123',
        first_name='Verified',
        last_name='Patient',
        user_type='patient',
        email_verified=True
    )
    PatientProfile.objects.create(user=user)
    return user


@pytest.fixture
def unverified_patient_user(db):
    """Create an unverified patient user for testing"""
    user = User.objects.create_user(
        email='unverified.patient@test.com',
        password='testpass123',
        first_name='Unverified',
        last_name='Patient',
        user_type='patient',
        email_verified=False
    )
    PatientProfile.objects.create(user=user)
    return user


# ============================================
# AUTH PAGE TESTS
# ============================================

@pytest.mark.django_db
class TestAuthPages:
    """Test authentication pages"""
    
    def test_login_page_loads(self, client):
        """Verify login page loads"""
        response = client.get(reverse('dashboard:login'))
        
        assert response.status_code == 200
    
    def test_register_choice_page_loads(self, client):
        """Verify register choice page loads"""
        response = client.get(reverse('dashboard:register_choice'))
        
        assert response.status_code == 200
    
    def test_register_patient_page_loads(self, client):
        """Verify patient registration page loads"""
        response = client.get(reverse('dashboard:register_patient'))
        
        assert response.status_code == 200
    
    def test_register_doctor_page_loads(self, client, specialization):
        """Verify doctor registration page loads"""
        response = client.get(reverse('dashboard:register_doctor'))
        
        assert response.status_code == 200
    
    def test_forgot_password_page_loads(self, client):
        """Verify forgot password page loads"""
        response = client.get(reverse('dashboard:forgot_password'))
        
        assert response.status_code == 200
    
    def test_verification_sent_page_loads(self, client):
        """Verify verification sent page loads"""
        response = client.get(reverse('dashboard:verification_sent'))
        
        assert response.status_code == 200


# ============================================
# LOGIN TESTS
# ============================================

@pytest.mark.django_db
class TestLogin:
    """Test login functionality"""
    
    def test_successful_patient_login(self, client, verified_patient_user):
        """Verify patient can login and redirect to dashboard"""
        response = client.post(reverse('dashboard:login'), {
            'email': 'verified.patient@test.com',
            'password': 'testpass123'
        })
        
        assert response.status_code == 302
        assert '/patient/dashboard/' in response.url
    
    def test_successful_doctor_login(self, client, verified_doctor_user):
        """Verify doctor can login and redirect to dashboard"""
        response = client.post(reverse('dashboard:login'), {
            'email': 'verified.doctor@test.com',
            'password': 'testpass123'
        })
        
        assert response.status_code == 302
        assert '/doctor/dashboard/' in response.url
    
    def test_unverified_email_cannot_login(self, client, unverified_patient_user):
        """Verify unverified email user cannot login"""
        response = client.post(reverse('dashboard:login'), {
            'email': 'unverified.patient@test.com',
            'password': 'testpass123'
        })
        
        # Should stay on login page with error
        assert response.status_code == 200
    
    def test_wrong_password_rejected(self, client, verified_patient_user):
        """Verify wrong password is rejected"""
        response = client.post(reverse('dashboard:login'), {
            'email': 'verified.patient@test.com',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 200  # Stay on login page
    
    def test_nonexistent_user_rejected(self, client):
        """Verify non-existent user is rejected"""
        response = client.post(reverse('dashboard:login'), {
            'email': 'nobody@test.com',
            'password': 'anypassword'
        })
        
        assert response.status_code == 200  # Stay on login page


# ============================================
# LOGOUT TESTS
# ============================================

@pytest.mark.django_db
class TestLogout:
    """Test logout functionality"""
    
    def test_logout_redirects_to_login(self, client, verified_patient_user):
        """Verify logout redirects to login page"""
        # Login first
        client.login(email='verified.patient@test.com', password='testpass123')
        
        response = client.get(reverse('dashboard:logout'))
        
        assert response.status_code == 302
        assert '/login/' in response.url


# ============================================
# REGISTRATION TESTS
# ============================================

@pytest.mark.django_db
class TestPatientRegistration:
    """Test patient registration"""
    
    def test_successful_registration(self, client):
        """Verify patient registration works"""
        with patch('dashboard.views.EmailService') as mock_email:
            mock_email.send_email_verification = MagicMock()
            mock_email.send_welcome_email = MagicMock()
            
            response = client.post(reverse('dashboard:register_patient'), {
                'email': 'newpatient@test.com',
                'password': 'SecurePass123!',
                'password_confirm': 'SecurePass123!',
                'first_name': 'New',
                'last_name': 'Patient',
                'phone': '+2341234567890'
            })
        
        assert response.status_code == 302
        assert '/verification-sent/' in response.url
        assert User.objects.filter(email='newpatient@test.com').exists()
    
    def test_password_mismatch_rejected(self, client):
        """Verify password mismatch is rejected"""
        response = client.post(reverse('dashboard:register_patient'), {
            'email': 'test@test.com',
            'password': 'Password123!',
            'password_confirm': 'DifferentPassword!',
            'first_name': 'Test',
            'last_name': 'User'
        })
        
        assert response.status_code == 200  # Stay on page with error
    
    def test_duplicate_email_rejected(self, client, verified_patient_user):
        """Verify duplicate email is rejected"""
        response = client.post(reverse('dashboard:register_patient'), {
            'email': 'verified.patient@test.com',  # Already exists
            'password': 'Password123!',
            'password_confirm': 'Password123!',
            'first_name': 'Test',
            'last_name': 'User'
        })
        
        assert response.status_code == 200  # Stay on page with error


# ============================================
# DOCTOR DASHBOARD ACCESS TESTS
# ============================================

@pytest.mark.django_db
class TestDoctorDashboardAccess:
    """Test doctor dashboard access control"""
    
    def test_doctor_can_access_dashboard(self, client, verified_doctor_user):
        """Verify doctor can access doctor dashboard"""
        client.login(email='verified.doctor@test.com', password='testpass123')
        
        response = client.get(reverse('dashboard:doctor_dashboard'))
        
        assert response.status_code == 200
    
    def test_patient_cannot_access_doctor_dashboard(self, client, verified_patient_user):
        """Verify patient cannot access doctor dashboard"""
        client.login(email='verified.patient@test.com', password='testpass123')
        
        response = client.get(reverse('dashboard:doctor_dashboard'))
        
        # Should redirect to patient dashboard or return 403
        assert response.status_code in [302, 403]
    
    def test_unauthenticated_redirects_to_login(self, client):
        """Verify unauthenticated user is redirected to login"""
        response = client.get(reverse('dashboard:doctor_dashboard'))
        
        assert response.status_code == 302
        assert '/login/' in response.url
    
    def test_doctor_can_access_appointments(self, client, verified_doctor_user):
        """Verify doctor can access appointments page"""
        client.login(email='verified.doctor@test.com', password='testpass123')
        
        response = client.get(reverse('dashboard:doctor_appointments'))
        
        assert response.status_code == 200
    
    def test_doctor_can_access_patients(self, client, verified_doctor_user):
        """Verify doctor can access patients page"""
        client.login(email='verified.doctor@test.com', password='testpass123')
        
        response = client.get(reverse('dashboard:doctor_patients'))
        
        assert response.status_code == 200
    
    def test_doctor_can_access_prescriptions(self, client, verified_doctor_user):
        """Verify doctor can access prescriptions page"""
        client.login(email='verified.doctor@test.com', password='testpass123')
        
        response = client.get(reverse('dashboard:doctor_prescriptions'))
        
        assert response.status_code == 200
    
    def test_doctor_can_access_profile(self, client, verified_doctor_user):
        """Verify doctor can access profile page"""
        client.login(email='verified.doctor@test.com', password='testpass123')
        
        response = client.get(reverse('dashboard:doctor_profile'))
        
        assert response.status_code == 200


# ============================================
# PATIENT DASHBOARD ACCESS TESTS
# ============================================

@pytest.mark.django_db
class TestPatientDashboardAccess:
    """Test patient dashboard access control"""
    
    def test_patient_can_access_dashboard(self, client, verified_patient_user):
        """Verify patient can access patient dashboard"""
        client.login(email='verified.patient@test.com', password='testpass123')
        
        response = client.get(reverse('dashboard:patient_dashboard'))
        
        assert response.status_code == 200
    
    def test_doctor_cannot_access_patient_dashboard(self, client, verified_doctor_user):
        """Verify doctor cannot access patient dashboard"""
        client.login(email='verified.doctor@test.com', password='testpass123')
        
        response = client.get(reverse('dashboard:patient_dashboard'))
        
        # Should redirect to doctor dashboard or return 403
        assert response.status_code in [302, 403]
    
    def test_unauthenticated_redirects_to_login(self, client):
        """Verify unauthenticated user is redirected to login"""
        response = client.get(reverse('dashboard:patient_dashboard'))
        
        assert response.status_code == 302
        assert '/login/' in response.url
    
    def test_patient_can_access_appointments(self, client, verified_patient_user):
        """Verify patient can access appointments page"""
        client.login(email='verified.patient@test.com', password='testpass123')
        
        response = client.get(reverse('dashboard:patient_appointments'))
        
        assert response.status_code == 200
    
    def test_patient_can_access_doctors(self, client, verified_patient_user):
        """Verify patient can access doctors page"""
        client.login(email='verified.patient@test.com', password='testpass123')
        
        response = client.get(reverse('dashboard:patient_doctors'))
        
        assert response.status_code == 200
    
    def test_patient_can_access_prescriptions(self, client, verified_patient_user):
        """Verify patient can access prescriptions page"""
        client.login(email='verified.patient@test.com', password='testpass123')
        
        response = client.get(reverse('dashboard:patient_prescriptions'))
        
        assert response.status_code == 200
    
    def test_patient_can_access_profile(self, client, verified_patient_user):
        """Verify patient can access profile page"""
        client.login(email='verified.patient@test.com', password='testpass123')
        
        response = client.get(reverse('dashboard:patient_profile'))
        
        assert response.status_code == 200


# ============================================
# PASSWORD CHANGE TESTS
# ============================================

@pytest.mark.django_db
class TestPasswordChange:
    """Test password change functionality"""
    
    def test_doctor_can_change_password(self, client, verified_doctor_user):
        """Verify doctor can change password"""
        client.login(email='verified.doctor@test.com', password='testpass123')
        
        response = client.post(reverse('dashboard:doctor_change_password'), {
            'current_password': 'testpass123',
            'new_password': 'NewSecurePass456!',
            'confirm_password': 'NewSecurePass456!'
        })
        
        assert response.status_code == 302  # Redirect on success
    
    def test_patient_can_change_password(self, client, verified_patient_user):
        """Verify patient can change password"""
        client.login(email='verified.patient@test.com', password='testpass123')
        
        response = client.post(reverse('dashboard:patient_change_password'), {
            'current_password': 'testpass123',
            'new_password': 'NewSecurePass456!',
            'confirm_password': 'NewSecurePass456!'
        })
        
        assert response.status_code == 302  # Redirect on success
    
    def test_wrong_current_password_rejected(self, client, verified_patient_user):
        """Verify wrong current password is rejected"""
        client.login(email='verified.patient@test.com', password='testpass123')
        
        response = client.post(reverse('dashboard:patient_change_password'), {
            'current_password': 'wrongpassword',
            'new_password': 'NewSecurePass456!',
            'confirm_password': 'NewSecurePass456!'
        })
        
        assert response.status_code == 200  # Stay on page with error


# ============================================
# SHARED VIEW TESTS
# ============================================

@pytest.mark.django_db
class TestSharedViews:
    """Test shared views accessible by both doctor and patient"""
    
    def test_chat_requires_login(self, client):
        """Verify chat page requires authentication"""
        response = client.get(reverse('dashboard:chat'))
        
        assert response.status_code == 302
        assert '/login/' in response.url
    
    def test_video_call_requires_login(self, client):
        """Verify video call page requires authentication"""
        response = client.get(reverse('dashboard:video_call'))
        
        assert response.status_code == 302
        assert '/login/' in response.url
    
    def test_voice_call_requires_login(self, client):
        """Verify voice call page requires authentication"""
        response = client.get(reverse('dashboard:voice_call'))
        
        assert response.status_code == 302
        assert '/login/' in response.url
    
    def test_doctor_can_access_chat(self, client, verified_doctor_user):
        """Verify doctor can access chat"""
        client.login(email='verified.doctor@test.com', password='testpass123')
        
        response = client.get(reverse('dashboard:chat'))
        
        assert response.status_code == 200
    
    def test_patient_can_access_chat(self, client, verified_patient_user):
        """Verify patient can access chat"""
        client.login(email='verified.patient@test.com', password='testpass123')
        
        response = client.get(reverse('dashboard:chat'))
        
        assert response.status_code == 200


# ============================================
# FORGOT PASSWORD TESTS
# ============================================

@pytest.mark.django_db
class TestForgotPassword:
    """Test forgot password functionality"""
    
    def test_forgot_password_form_works(self, client, verified_patient_user):
        """Verify forgot password form sends email"""
        with patch('dashboard.views.EmailService') as mock_email:
            mock_email.send_password_reset = MagicMock()
            
            response = client.post(reverse('dashboard:forgot_password'), {
                'email': 'verified.patient@test.com'
            })
        
        assert response.status_code == 302  # Redirect on success
    
    def test_forgot_password_nonexistent_email(self, client):
        """Verify forgot password doesn't reveal if email exists"""
        response = client.post(reverse('dashboard:forgot_password'), {
            'email': 'nobody@test.com'
        })
        
        # Should still redirect (don't reveal if email exists)
        assert response.status_code == 302


# ============================================
# AUTHENTICATED USER REDIRECT TESTS
# ============================================

@pytest.mark.django_db
class TestAuthenticatedUserRedirect:
    """Test that authenticated users are redirected from auth pages"""
    
    def test_logged_in_patient_redirected_from_login(self, client, verified_patient_user):
        """Verify logged in patient is redirected from login page"""
        client.login(email='verified.patient@test.com', password='testpass123')
        
        response = client.get(reverse('dashboard:login'))
        
        # Should redirect to dashboard
        assert response.status_code == 302
    
    def test_logged_in_doctor_redirected_from_login(self, client, verified_doctor_user):
        """Verify logged in doctor is redirected from login page"""
        client.login(email='verified.doctor@test.com', password='testpass123')
        
        response = client.get(reverse('dashboard:login'))
        
        # Should redirect to dashboard
        assert response.status_code == 302
    
    def test_logged_in_user_redirected_from_register(self, client, verified_patient_user):
        """Verify logged in user is redirected from register page"""
        client.login(email='verified.patient@test.com', password='testpass123')
        
        response = client.get(reverse('dashboard:register_patient'))
        
        # Should redirect to dashboard
        assert response.status_code == 302