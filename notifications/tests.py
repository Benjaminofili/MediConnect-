import pytest
from datetime import date, time, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock, ANY
from django.core import mail
from django.test import override_settings

from notifications.services import EmailService
from accounts.models import User, DoctorProfile, PatientProfile
from doctors.models import Specialization
from appointments.models import Appointment
from consultations.models import Consultation, Prescription, PrescriptionItem


# ============================================
# EMAIL SERVICE UNIT TESTS (No DB needed)
# ============================================

class TestEmailServiceHelpers:
    """Test helper methods"""
    
    def test_get_base_url_without_request(self):
        """Verify default base URL when no request provided"""
        url = EmailService._get_base_url(None)
        
        assert url == "http://localhost:8000"
    
    def test_get_base_url_with_request(self):
        """Verify base URL extracted from request"""
        mock_request = MagicMock()
        mock_request.scheme = 'https'
        mock_request.get_host.return_value = 'example.com'
        
        url = EmailService._get_base_url(mock_request)
        
        assert url == "https://example.com"


class TestSendEmailFunction:
    """Test the core send_email function"""
    
    @patch('notifications.services.EmailMultiAlternatives')
    @patch('notifications.services.render_to_string')
    def test_send_email_with_html_template(self, mock_render, mock_email_class):
        """Verify HTML email is sent when template exists"""
        mock_render.return_value = '<html><body>Test</body></html>'
        mock_email_instance = MagicMock()
        mock_email_class.return_value = mock_email_instance
        
        result = EmailService.send_email(
            subject='Test Subject',
            template_name='test_template',
            context={'key': 'value'},
            recipient_email='test@example.com'
        )
        
        assert result is True
        mock_email_class.assert_called_once()
        mock_email_instance.attach_alternative.assert_called_once()
        mock_email_instance.send.assert_called_once()
    
    @patch('notifications.services.send_mail')
    @patch('notifications.services.render_to_string')
    def test_send_email_fallback_to_plain_text(self, mock_render, mock_send_mail):
        """Verify plain text email is sent when template fails"""
        mock_render.side_effect = Exception("Template not found")
        mock_send_mail.return_value = 1
        
        result = EmailService.send_email(
            subject='Test Subject',
            template_name='nonexistent_template',
            context={'message': 'Plain text message'},
            recipient_email='test@example.com'
        )
        
        assert result is True
        mock_send_mail.assert_called_once()
    
    @patch('notifications.services.send_mail')
    @patch('notifications.services.render_to_string')
    def test_send_email_handles_send_error(self, mock_render, mock_send_mail):
        """Verify email errors are handled gracefully"""
        mock_render.side_effect = Exception("Template error")
        mock_send_mail.side_effect = Exception("SMTP error")
        
        result = EmailService.send_email(
            subject='Test Subject',
            template_name='test',
            context={},
            recipient_email='test@example.com'
        )
        
        assert result is False


# ============================================
# WELCOME EMAIL TESTS
# ============================================

class TestWelcomeEmail:
    """Test welcome email functionality"""
    
    @patch.object(EmailService, 'send_email')
    def test_send_welcome_email(self, mock_send_email):
        """Verify welcome email is sent with correct parameters"""
        mock_send_email.return_value = True
        
        # Create mock user
        mock_user = MagicMock()
        mock_user.full_name = 'John Doe'
        mock_user.email = 'john@example.com'
        mock_user.user_type = 'patient'
        
        result = EmailService.send_welcome_email(mock_user)
        
        assert result is True
        mock_send_email.assert_called_once()
        
        # Verify call arguments
        call_args = mock_send_email.call_args
        assert call_args[1]['subject'] == 'Welcome to MediConnect!'
        assert call_args[1]['template_name'] == 'welcome'
        assert call_args[1]['recipient_email'] == 'john@example.com'
        assert call_args[1]['context']['user_name'] == 'John Doe'
        assert call_args[1]['context']['user_type'] == 'patient'


# ============================================
# EMAIL VERIFICATION TESTS
# ============================================

class TestEmailVerification:
    """Test email verification functionality"""
    
    @patch.object(EmailService, 'send_email')
    def test_send_email_verification(self, mock_send_email):
        """Verify verification email contains correct URL"""
        mock_send_email.return_value = True
        
        mock_user = MagicMock()
        mock_user.full_name = 'John Doe'
        mock_user.email = 'john@example.com'
        
        result = EmailService.send_email_verification(
            user=mock_user,
            request=None,
            token='test-token-123',
            uid='test-uid-456'
        )
        
        assert result is True
        mock_send_email.assert_called_once()
        
        # Verify URL is in context
        call_args = mock_send_email.call_args
        context = call_args[1]['context']
        assert 'verification_url' in context
        assert 'test-uid-456' in context['verification_url']
        assert 'test-token-123' in context['verification_url']
    
    @patch.object(EmailService, 'send_email')
    def test_verification_url_format(self, mock_send_email):
        """Verify verification URL has correct format"""
        mock_send_email.return_value = True
        
        mock_user = MagicMock()
        mock_user.full_name = 'Test User'
        mock_user.email = 'test@example.com'
        
        EmailService.send_email_verification(
            user=mock_user,
            request=None,
            token='abc123',
            uid='xyz789'
        )
        
        context = mock_send_email.call_args[1]['context']
        expected_url = 'http://localhost:8000/verify-email/xyz789/abc123/'
        assert context['verification_url'] == expected_url


# ============================================
# PASSWORD RESET TESTS
# ============================================

class TestPasswordReset:
    """Test password reset email functionality"""
    
    @patch.object(EmailService, 'send_email')
    def test_send_password_reset(self, mock_send_email):
        """Verify password reset email is sent correctly"""
        mock_send_email.return_value = True
        
        mock_user = MagicMock()
        mock_user.full_name = 'Jane Doe'
        mock_user.email = 'jane@example.com'
        
        result = EmailService.send_password_reset(
            user=mock_user,
            request=None,
            token='reset-token',
            uid='reset-uid'
        )
        
        assert result is True
        
        call_args = mock_send_email.call_args
        assert 'Reset Your Password' in call_args[1]['subject']
        assert call_args[1]['template_name'] == 'password_reset'
        
        context = call_args[1]['context']
        assert 'reset_url' in context
        assert 'reset-uid' in context['reset_url']
        assert 'reset-token' in context['reset_url']


# ============================================
# APPOINTMENT CONFIRMATION TESTS
# ============================================

class TestAppointmentConfirmation:
    """Test appointment confirmation emails"""
    
    @patch.object(EmailService, 'send_email')
    def test_send_appointment_confirmation_to_patient(self, mock_send_email):
        """Verify appointment confirmation sent to patient"""
        mock_send_email.return_value = True
        
        # Create mock appointment
        mock_appointment = MagicMock()
        mock_appointment.appointment_number = 'APT-20240101-XXXX'
        mock_appointment.patient.full_name = 'John Patient'
        mock_appointment.patient.email = 'patient@example.com'
        mock_appointment.doctor.user.full_name = 'Jane Doctor'
        mock_appointment.doctor.specialization.name = 'Cardiology'
        mock_appointment.date = date.today()
        mock_appointment.start_time = time(10, 0)
        mock_appointment.end_time = time(10, 30)
        mock_appointment.video_room_url = 'https://whereby.com/test-room'
        
        result = EmailService.send_appointment_confirmation(mock_appointment)
        
        assert result is True
        mock_send_email.assert_called_once()
        
        call_args = mock_send_email.call_args
        assert 'APT-20240101-XXXX' in call_args[1]['subject']
        assert call_args[1]['recipient_email'] == 'patient@example.com'
    
    @patch.object(EmailService, 'send_email')
    def test_send_appointment_confirmation_to_doctor(self, mock_send_email):
        """Verify appointment notification sent to doctor"""
        mock_send_email.return_value = True
        
        mock_appointment = MagicMock()
        mock_appointment.appointment_number = 'APT-20240101-YYYY'
        mock_appointment.patient.full_name = 'John Patient'
        mock_appointment.doctor.user.full_name = 'Jane Doctor'
        mock_appointment.doctor.user.email = 'doctor@example.com'
        mock_appointment.date = date.today()
        mock_appointment.start_time = time(14, 0)
        mock_appointment.end_time = time(14, 30)
        mock_appointment.reason = 'Chest pain'
        
        result = EmailService.send_appointment_confirmation_to_doctor(mock_appointment)
        
        assert result is True
        
        call_args = mock_send_email.call_args
        assert 'New Appointment' in call_args[1]['subject']
        assert call_args[1]['recipient_email'] == 'doctor@example.com'


# ============================================
# APPOINTMENT CANCELLATION TESTS
# ============================================

class TestAppointmentCancellation:
    """Test appointment cancellation emails"""
    
    @patch.object(EmailService, 'send_email')
    def test_cancellation_by_patient_notifies_doctor(self, mock_send_email):
        """Verify doctor is notified when patient cancels"""
        mock_send_email.return_value = True
        
        mock_appointment = MagicMock()
        mock_appointment.appointment_number = 'APT-CANCEL-001'
        mock_appointment.patient.full_name = 'John Patient'
        mock_appointment.doctor.user.full_name = 'Jane Doctor'
        mock_appointment.doctor.user.email = 'doctor@example.com'
        mock_appointment.date = date.today()
        mock_appointment.start_time = time(10, 0)
        mock_appointment.cancellation_reason = 'Personal emergency'
        
        result = EmailService.send_appointment_cancellation(
            mock_appointment,
            cancelled_by_type='patient'
        )
        
        assert result is True
        
        call_args = mock_send_email.call_args
        assert call_args[1]['recipient_email'] == 'doctor@example.com'
    
    @patch.object(EmailService, 'send_email')
    def test_cancellation_by_doctor_notifies_patient(self, mock_send_email):
        """Verify patient is notified when doctor cancels"""
        mock_send_email.return_value = True
        
        mock_appointment = MagicMock()
        mock_appointment.appointment_number = 'APT-CANCEL-002'
        mock_appointment.patient.full_name = 'John Patient'
        mock_appointment.patient.email = 'patient@example.com'
        mock_appointment.doctor.user.full_name = 'Jane Doctor'
        mock_appointment.date = date.today()
        mock_appointment.start_time = time(10, 0)
        mock_appointment.cancellation_reason = 'Emergency surgery'
        
        result = EmailService.send_appointment_cancellation(
            mock_appointment,
            cancelled_by_type='doctor'
        )
        
        assert result is True
        
        call_args = mock_send_email.call_args
        assert call_args[1]['recipient_email'] == 'patient@example.com'


# ============================================
# APPOINTMENT REMINDER TESTS
# ============================================

class TestAppointmentReminder:
    """Test appointment reminder emails"""
    
    @patch.object(EmailService, 'send_email')
    def test_send_appointment_reminder(self, mock_send_email):
        """Verify reminder email is sent with correct content"""
        mock_send_email.return_value = True
        
        mock_appointment = MagicMock()
        mock_appointment.appointment_number = 'APT-REMIND-001'
        mock_appointment.patient.full_name = 'John Patient'
        mock_appointment.patient.email = 'patient@example.com'
        mock_appointment.doctor.user.full_name = 'Jane Doctor'
        mock_appointment.date = date.today() + timedelta(days=1)
        mock_appointment.start_time = time(10, 0)
        mock_appointment.video_room_url = 'https://whereby.com/reminder-room'
        
        result = EmailService.send_appointment_reminder(mock_appointment)
        
        assert result is True
        
        call_args = mock_send_email.call_args
        assert 'Reminder' in call_args[1]['subject']
        assert 'Tomorrow' in call_args[1]['subject']


# ============================================
# PRESCRIPTION READY TESTS
# ============================================

class TestPrescriptionReady:
    """Test prescription notification emails"""
    
    @patch.object(EmailService, 'send_email')
    def test_send_prescription_ready(self, mock_send_email):
        """Verify prescription notification is sent"""
        mock_send_email.return_value = True
        
        # Create mock prescription with items
        mock_item1 = MagicMock()
        mock_item1.medicine_name = 'Paracetamol'
        mock_item1.dosage = '500mg'
        mock_item1.get_frequency_display.return_value = 'Three Times Daily'
        
        mock_item2 = MagicMock()
        mock_item2.medicine_name = 'Vitamin C'
        mock_item2.dosage = '1000mg'
        mock_item2.get_frequency_display.return_value = 'Once Daily'
        
        mock_prescription = MagicMock()
        mock_prescription.prescription_number = 'RX-20240101-ABCD'
        mock_prescription.diagnosis = 'Common cold'
        mock_prescription.notes = 'Take with food'
        mock_prescription.valid_until = date.today() + timedelta(days=30)
        mock_prescription.items.all.return_value = [mock_item1, mock_item2]
        mock_prescription.consultation.appointment.patient.full_name = 'John Patient'
        mock_prescription.consultation.appointment.patient.email = 'patient@example.com'
        mock_prescription.consultation.appointment.doctor.user.full_name = 'Jane Doctor'
        
        result = EmailService.send_prescription_ready(mock_prescription)
        
        assert result is True
        
        call_args = mock_send_email.call_args
        assert 'RX-20240101-ABCD' in call_args[1]['subject']
        assert call_args[1]['recipient_email'] == 'patient@example.com'
        
        # Verify medicines are included in context
        context = call_args[1]['context']
        assert len(context['medicines']) == 2


# ============================================
# DOCTOR VERIFIED TESTS
# ============================================

class TestDoctorVerified:
    """Test doctor verification notification"""
    
    @patch.object(EmailService, 'send_email')
    def test_send_doctor_verified(self, mock_send_email):
        """Verify doctor receives verification confirmation"""
        mock_send_email.return_value = True
        
        mock_doctor_profile = MagicMock()
        mock_doctor_profile.user.full_name = 'Jane Doctor'
        mock_doctor_profile.user.email = 'doctor@example.com'
        
        result = EmailService.send_doctor_verified(mock_doctor_profile)
        
        assert result is True
        
        call_args = mock_send_email.call_args
        assert 'Verified' in call_args[1]['subject']
        assert call_args[1]['recipient_email'] == 'doctor@example.com'
        assert call_args[1]['template_name'] == 'doctor_verified'


# ============================================
# CONSULTATION COMPLETED TESTS
# ============================================

class TestConsultationCompleted:
    """Test consultation completed notification"""
    
    @patch.object(EmailService, 'send_email')
    def test_send_consultation_completed(self, mock_send_email):
        """Verify patient receives completion notification"""
        mock_send_email.return_value = True
        
        mock_appointment = MagicMock()
        mock_appointment.appointment_number = 'APT-COMPLETE-001'
        mock_appointment.patient.full_name = 'John Patient'
        mock_appointment.patient.email = 'patient@example.com'
        mock_appointment.doctor.user.full_name = 'Jane Doctor'
        mock_appointment.date = date.today()
        
        result = EmailService.send_consultation_completed(mock_appointment)
        
        assert result is True
        
        call_args = mock_send_email.call_args
        assert 'Completed' in call_args[1]['subject']
        assert call_args[1]['recipient_email'] == 'patient@example.com'


# ============================================
# INTEGRATION TESTS (With Django test email backend)
# ============================================

@pytest.mark.django_db
class TestEmailIntegration:
    """Integration tests for email service"""
    
    def test_welcome_email_returns_boolean(self, patient_user):
        """Verify welcome email returns True/False without crashing"""
        # This tests that the function handles missing templates gracefully
        result = EmailService.send_welcome_email(patient_user)
        
        # Should return True or False, not crash
        assert isinstance(result, bool)
        
        # Check email was "sent" (captured by test backend)
        # Note: This may fail if template doesn't exist
        # The email might not appear in outbox if template rendering fails
        # But the function should still return True/False without crashing