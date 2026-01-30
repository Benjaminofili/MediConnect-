# notifications/services.py

from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class EmailService:
    """Service for sending emails."""
    
    @staticmethod
    def _get_base_url(request=None):
        """Get the base URL for the site."""
        if request:
            return f"{request.scheme}://{request.get_host()}"
        return "http://localhost:8000"
    
    @staticmethod
    def send_email(subject, template_name, context, recipient_email):
        """Send an email using HTML template."""
        try:
            html_content = render_to_string(f'emails/{template_name}.html', context)
            text_content = strip_tags(html_content)
        except Exception as e:
            print(f"DEBUG: Template error: {e}")
            text_content = context.get('message', '')
            html_content = None
        
        try:
            if html_content:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[recipient_email]
                )
                email.attach_alternative(html_content, "text/html")
                email.send()
            else:
                send_mail(
                    subject=subject,
                    message=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient_email],
                    fail_silently=False
                )
            return True
        except Exception as e:
            print(f"Email error: {str(e)}")
            return False
    
    @staticmethod
    def send_email_verification(user, request=None, token=None, uid=None):
        """Send email verification link to user."""
        
        # ✅ Build URL manually to avoid encoding issues
        base_url = EmailService._get_base_url(request)
        verification_url = f"{base_url}/verify-email/{uid}/{token}/"
        
        print(f"DEBUG: Generated verification URL: {verification_url}")
        
        subject = "Verify Your Email - MediConnect"
        context = {
            'user_name': user.full_name,
            'verification_url': verification_url,
        }
        
        return EmailService.send_email(
            subject=subject,
            template_name='email_verification',
            context=context,
            recipient_email=user.email
        )
    
    @staticmethod
    def send_password_reset(user, request=None, token=None, uid=None):
        """Send password reset link to user."""
        
        # ✅ Build URL manually to avoid encoding issues
        base_url = EmailService._get_base_url(request)
        reset_url = f"{base_url}/reset-password/{uid}/{token}/"
        
        print(f"DEBUG: Generated reset URL: {reset_url}")
        
        subject = "Reset Your Password - MediConnect"
        context = {
            'user_name': user.full_name,
            'reset_url': reset_url,
        }
        
        return EmailService.send_email(
            subject=subject,
            template_name='password_reset',
            context=context,
            recipient_email=user.email
        )
    
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email to new user."""
        subject = "Welcome to MediConnect!"
        context = {
            'user_name': user.full_name,
            'user_email': user.email,
            'user_type': user.user_type,
        }
        
        return EmailService.send_email(
            subject=subject,
            template_name='welcome',
            context=context,
            recipient_email=user.email
        )
    
    # ... rest of your existing methods ...

    @staticmethod
    def send_appointment_confirmation(appointment):
        """Send appointment confirmation to patient."""
        subject = f"Appointment Confirmed - {appointment.appointment_number}"
        context = {
            'patient_name': appointment.patient.full_name,
            'doctor_name': f"Dr. {appointment.doctor.user.full_name}",
            'specialization': appointment.doctor.specialization.name if appointment.doctor.specialization else 'General',
            'date': appointment.date.strftime('%B %d, %Y'),
            'time': appointment.start_time.strftime('%I:%M %p'),
            'appointment_number': appointment.appointment_number,
            'video_room_url': appointment.video_room_url,
            'message': f"""
Hello {appointment.patient.full_name},

Your appointment has been confirmed!

Appointment Details:
- Appointment Number: {appointment.appointment_number}
- Doctor: Dr. {appointment.doctor.user.full_name}
- Specialization: {appointment.doctor.specialization.name if appointment.doctor.specialization else 'General'}
- Date: {appointment.date.strftime('%B %d, %Y')}
- Time: {appointment.start_time.strftime('%I:%M %p')} - {appointment.end_time.strftime('%I:%M %p')}

Video Consultation Link:
{appointment.video_room_url}

Please join the video call 5 minutes before your scheduled time.

To cancel or reschedule, please do so at least 2 hours before your appointment.

Thank you for choosing MediConnect!

Best regards,
The MediConnect Team
            """
        }
        
        return EmailService.send_email(
            subject=subject,
            template_name='appointment_confirmation',
            context=context,
            recipient_email=appointment.patient.email
        )
    
    @staticmethod
    def send_appointment_confirmation_to_doctor(appointment):
        """Send appointment notification to doctor."""
        subject = f"New Appointment - {appointment.appointment_number}"
        context = {
            'doctor_name': f"Dr. {appointment.doctor.user.full_name}",
            'patient_name': appointment.patient.full_name,
            'date': appointment.date.strftime('%B %d, %Y'),
            'time': appointment.start_time.strftime('%I:%M %p'),
            'appointment_number': appointment.appointment_number,
            'reason': appointment.reason or 'Not specified',
            'message': f"""
Hello Dr. {appointment.doctor.user.full_name},

You have a new appointment!

Appointment Details:
- Appointment Number: {appointment.appointment_number}
- Patient: {appointment.patient.full_name}
- Date: {appointment.date.strftime('%B %d, %Y')}
- Time: {appointment.start_time.strftime('%I:%M %p')} - {appointment.end_time.strftime('%I:%M %p')}
- Reason: {appointment.reason or 'Not specified'}

Best regards,
The MediConnect Team
            """
        }
        
        return EmailService.send_email(
            subject=subject,
            template_name='appointment_doctor_notification',
            context=context,
            recipient_email=appointment.doctor.user.email
        )
    
    @staticmethod
    def send_appointment_cancellation(appointment, cancelled_by_type):
        """Send cancellation notification."""
        subject = f"Appointment Cancelled - {appointment.appointment_number}"
        
        if cancelled_by_type == 'patient':
            # Notify doctor
            recipient = appointment.doctor.user
            other_party = appointment.patient.full_name
        else:
            # Notify patient
            recipient = appointment.patient
            other_party = f"Dr. {appointment.doctor.user.full_name}"
        
        context = {
            'recipient_name': recipient.full_name,
            'other_party': other_party,
            'date': appointment.date.strftime('%B %d, %Y'),
            'time': appointment.start_time.strftime('%I:%M %p'),
            'appointment_number': appointment.appointment_number,
            'cancellation_reason': appointment.cancellation_reason,
            'message': f"""
Hello {recipient.full_name},

An appointment has been cancelled.

Appointment Details:
- Appointment Number: {appointment.appointment_number}
- Date: {appointment.date.strftime('%B %d, %Y')}
- Time: {appointment.start_time.strftime('%I:%M %p')}
- Cancelled by: {other_party}
- Reason: {appointment.cancellation_reason or 'Not specified'}

If you need to book a new appointment, please visit our platform.

Best regards,
The MediConnect Team
            """
        }
        
        return EmailService.send_email(
            subject=subject,
            template_name='appointment_cancellation',
            context=context,
            recipient_email=recipient.email
        )
    
    @staticmethod
    def send_appointment_reminder(appointment):
        """Send appointment reminder to patient."""
        subject = f"Reminder: Appointment Tomorrow - {appointment.appointment_number}"
        context = {
            'patient_name': appointment.patient.full_name,
            'doctor_name': f"Dr. {appointment.doctor.user.full_name}",
            'date': appointment.date.strftime('%B %d, %Y'),
            'time': appointment.start_time.strftime('%I:%M %p'),
            'appointment_number': appointment.appointment_number,
            'video_room_url': appointment.video_room_url,
            'message': f"""
Hello {appointment.patient.full_name},

This is a reminder for your upcoming appointment tomorrow.

Appointment Details:
- Appointment Number: {appointment.appointment_number}
- Doctor: Dr. {appointment.doctor.user.full_name}
- Date: {appointment.date.strftime('%B %d, %Y')}
- Time: {appointment.start_time.strftime('%I:%M %p')}

Video Consultation Link:
{appointment.video_room_url}

Please join the video call 5 minutes before your scheduled time.

Best regards,
The MediConnect Team
            """
        }
        
        return EmailService.send_email(
            subject=subject,
            template_name='appointment_reminder',
            context=context,
            recipient_email=appointment.patient.email
        )
    
    @staticmethod
    def send_prescription_ready(prescription):
        """Send notification when prescription is ready."""
        appointment = prescription.consultation.appointment
        subject = f"Prescription Ready - {prescription.prescription_number}"
        
        # Get medicine list
        medicines = []
        for item in prescription.items.all():
            medicines.append(f"- {item.medicine_name} ({item.dosage}) - {item.get_frequency_display()}")
        
        medicine_list = '\n'.join(medicines)
        
        context = {
            'patient_name': appointment.patient.full_name,
            'doctor_name': f"Dr. {appointment.doctor.user.full_name}",
            'prescription_number': prescription.prescription_number,
            'diagnosis': prescription.diagnosis,
            'medicines': medicines,
            'valid_until': prescription.valid_until.strftime('%B %d, %Y') if prescription.valid_until else 'N/A',
            'message': f"""
Hello {appointment.patient.full_name},

Your prescription is ready!

Prescription Number: {prescription.prescription_number}
Doctor: Dr. {appointment.doctor.user.full_name}
Diagnosis: {prescription.diagnosis or 'See prescription details'}

Medicines:
{medicine_list}

Valid Until: {prescription.valid_until.strftime('%B %d, %Y') if prescription.valid_until else 'N/A'}

{prescription.notes if prescription.notes else ''}

Please log in to view and download your full prescription.

Best regards,
The MediConnect Team
            """
        }
        
        return EmailService.send_email(
            subject=subject,
            template_name='prescription_ready',
            context=context,
            recipient_email=appointment.patient.email
        )
    
    @staticmethod
    def send_doctor_verified(doctor_profile):
        """Send notification when doctor is verified."""
        subject = "Your Account Has Been Verified - MediConnect"
        context = {
            'doctor_name': f"Dr. {doctor_profile.user.full_name}",
            'message': f"""
Hello Dr. {doctor_profile.user.full_name},

Congratulations! Your account has been verified.

You can now:
- Set your availability schedule
- Accept patient appointments
- Conduct video consultations
- Issue prescriptions

Please log in to complete your profile and start accepting patients.

Welcome to MediConnect!

Best regards,
The MediConnect Team
            """
        }
        
        return EmailService.send_email(
            subject=subject,
            template_name='doctor_verified',
            context=context,
            recipient_email=doctor_profile.user.email
        )
    
    @staticmethod
    def send_consultation_completed(appointment):
        """Send notification when consultation is completed."""
        subject = f"Consultation Completed - {appointment.appointment_number}"
        context = {
            'patient_name': appointment.patient.full_name,
            'doctor_name': f"Dr. {appointment.doctor.user.full_name}",
            'date': appointment.date.strftime('%B %d, %Y'),
            'appointment_number': appointment.appointment_number,
            'message': f"""
Hello {appointment.patient.full_name},

Your consultation with Dr. {appointment.doctor.user.full_name} has been completed.

Appointment Number: {appointment.appointment_number}
Date: {appointment.date.strftime('%B %d, %Y')}

You can now:
- View your consultation notes
- Download any prescriptions
- Book a follow-up appointment if needed

Thank you for choosing MediConnect!

Best regards,
The MediConnect Team
            """
        }
        
        return EmailService.send_email(
            subject=subject,
            template_name='consultation_completed',
            context=context,
            recipient_email=appointment.patient.email
        )