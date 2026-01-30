# tests/integration/test_booking_flow.py
"""
Integration tests for Appointment Booking Flow:
- Patient browses doctors
- Patient books appointment
- Doctor confirms/cancels
- Appointment lifecycle
"""

import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import date, time, timedelta
from accounts.models import User, DoctorProfile, PatientProfile
from appointments.models import Appointment
from doctors.models import Specialization, TimeSlot


@pytest.mark.django_db
class TestPatientBookingFlow:
    """Test patient booking journey"""
    
    def test_patient_can_view_doctors_list(self, client, patient_user, doctor_user):
        """Patient can browse available doctors"""
        patient_user.email_verified = True
        patient_user.save()
        client.force_login(patient_user)
        
        url = reverse('dashboard:patient_doctors')
        response = client.get(url)
        
        assert response.status_code == 200
        assert doctor_user.doctor_profile in response.context['doctors'] or \
               any(d.id == doctor_user.doctor_profile.id for d in response.context['doctors'])
    
    def test_patient_can_view_doctor_detail(self, client, patient_user, doctor_user):
        """Patient can view doctor profile"""
        patient_user.email_verified = True
        patient_user.save()
        client.force_login(patient_user)
        
        url = reverse('dashboard:patient_doctor_detail', kwargs={'pk': doctor_user.doctor_profile.pk})
        response = client.get(url)
        
        assert response.status_code == 200
        assert response.context['doctor'].id == doctor_user.doctor_profile.id
    
    def test_patient_can_create_appointment(self, client, patient_user, doctor_user):
        """Patient can book appointment"""
        patient_user.email_verified = True
        patient_user.save()
        client.force_login(patient_user)
        
        tomorrow = date.today() + timedelta(days=1)
        
        url = reverse('dashboard:patient_create_appointment')
        data = {
            'doctor': doctor_user.doctor_profile.id,
            'slot_date': tomorrow.strftime('%Y-%m-%d'),
            'slot_start': '10:00',
            'duration': 30,
            'reason': 'Regular checkup',
            'symptoms': 'Headache',
            'appointment_type': 'online',
        }
        
        response = client.post(url, data)
        
        # Should redirect to appointments
        assert response.status_code == 302
        
        # Appointment should be created
        appointment = Appointment.objects.filter(
            patient=patient_user,
            doctor=doctor_user.doctor_profile
        ).first()
        
        assert appointment is not None
        assert appointment.status == 'pending'
        assert appointment.date == tomorrow
    
    def test_patient_cannot_book_conflicting_appointment(self, client, patient_user, doctor_user, appointment):
        """Patient cannot book when already has appointment at same time"""
        patient_user.email_verified = True
        patient_user.save()
        client.force_login(patient_user)
        
        url = reverse('dashboard:patient_create_appointment')
        data = {
            'doctor': doctor_user.doctor_profile.id,
            'slot_date': appointment.date.strftime('%Y-%m-%d'),
            'slot_start': appointment.start_time.strftime('%H:%M'),
            'duration': 30,
            'reason': 'Another appointment',
            'appointment_type': 'online',
        }
        
        response = client.post(url, data)
        
        # Should redirect with error
        assert response.status_code == 302
        
        # Should only have 1 appointment
        count = Appointment.objects.filter(
            patient=patient_user,
            date=appointment.date,
            start_time=appointment.start_time
        ).count()
        assert count == 1
    
    def test_patient_can_view_appointments(self, client, patient_user, appointment):
        """Patient can see their appointments"""
        patient_user.email_verified = True
        patient_user.save()
        client.force_login(patient_user)
        
        url = reverse('dashboard:patient_appointments')
        response = client.get(url)
        
        assert response.status_code == 200
        assert appointment in response.context['appointments']
    
    def test_patient_can_view_appointment_detail(self, client, patient_user, appointment):
        """Patient can view appointment details"""
        patient_user.email_verified = True
        patient_user.save()
        client.force_login(patient_user)
        
        url = reverse('dashboard:patient_appointment_detail', kwargs={'pk': appointment.pk})
        response = client.get(url)
        
        assert response.status_code == 200
        assert response.context['appointment'].id == appointment.id
    
    def test_patient_can_cancel_appointment(self, client, patient_user, appointment):
        """Patient can cancel appointment"""
        patient_user.email_verified = True
        patient_user.save()
        client.force_login(patient_user)
        
        # Move appointment to future so it can be cancelled
        appointment.date = date.today() + timedelta(days=2)
        appointment.save()
        
        url = reverse('dashboard:patient_cancel_appointment', kwargs={'pk': appointment.pk})
        response = client.post(url, {'cancellation_reason': 'Changed plans'})
        
        # Should redirect
        assert response.status_code == 302
        
        # Appointment should be cancelled
        appointment.refresh_from_db()
        assert appointment.status == 'cancelled'


@pytest.mark.django_db
class TestDoctorAppointmentManagement:
    """Test doctor appointment management"""
    
    def test_doctor_can_view_appointments(self, client, doctor_user, appointment):
        """Doctor can see their appointments"""
        doctor_user.email_verified = True
        doctor_user.save()
        client.force_login(doctor_user)
        
        url = reverse('dashboard:doctor_appointments')
        response = client.get(url)
        
        assert response.status_code == 200
        assert appointment in response.context['appointments']
    
    def test_doctor_can_view_appointment_detail(self, client, doctor_user, appointment):
        """Doctor can view appointment details"""
        doctor_user.email_verified = True
        doctor_user.save()
        client.force_login(doctor_user)
        
        url = reverse('dashboard:doctor_appointment_detail', kwargs={'pk': appointment.pk})
        response = client.get(url)
        
        assert response.status_code == 200
        assert response.context['appointment'].id == appointment.id
    
    def test_doctor_can_create_appointment_for_patient(self, client, doctor_user, patient_user):
        """Doctor can create appointment for existing patient"""
        doctor_user.email_verified = True
        doctor_user.save()
        client.force_login(doctor_user)
        
        tomorrow = date.today() + timedelta(days=1)
        
        url = reverse('dashboard:doctor_create_appointment')
        data = {
            'patient': patient_user.id,
            'date': tomorrow.strftime('%Y-%m-%d'),
            'start_time': '14:00',
            'duration': 30,
            'reason': 'Follow-up',
            'status': 'confirmed',
            'appointment_type': 'online',
        }
        
        response = client.post(url, data)
        
        # Should redirect
        assert response.status_code == 302
        
        # Appointment should be created
        appointment = Appointment.objects.filter(
            patient=patient_user,
            doctor=doctor_user.doctor_profile,
            date=tomorrow
        ).first()
        
        assert appointment is not None
        assert appointment.status == 'confirmed'
    
    def test_doctor_can_cancel_appointment(self, client, doctor_user, appointment):
        """Doctor can cancel appointment"""
        doctor_user.email_verified = True
        doctor_user.save()
        client.force_login(doctor_user)
        
        # Ensure appointment is in future
        appointment.date = date.today() + timedelta(days=2)
        appointment.save()
        
        url = reverse('dashboard:doctor_cancel_appointment', kwargs={'pk': appointment.pk})
        response = client.post(url, {'cancellation_reason': 'Emergency'})
        
        assert response.status_code == 302
        
        appointment.refresh_from_db()
        assert appointment.status == 'cancelled'
    
    def test_doctor_can_view_patients_list(self, client, doctor_user, appointment):
        """Doctor can see their patients"""
        doctor_user.email_verified = True
        doctor_user.save()
        client.force_login(doctor_user)
        
        url = reverse('dashboard:doctor_patients')
        response = client.get(url)
        
        assert response.status_code == 200
    
    def test_doctor_can_view_patient_detail(self, client, doctor_user, patient_user, appointment):
        """Doctor can view patient details"""
        doctor_user.email_verified = True
        doctor_user.save()
        client.force_login(doctor_user)
        
        url = reverse('dashboard:doctor_patient_detail', kwargs={'pk': patient_user.pk})
        response = client.get(url)
        
        assert response.status_code == 200
        assert response.context['patient'].id == patient_user.id


@pytest.mark.django_db
class TestAppointmentCalendar:
    """Test calendar functionality"""
    
    def test_patient_calendar_events(self, client, patient_user, appointment):
        """Patient can get calendar events as JSON"""
        patient_user.email_verified = True
        patient_user.save()
        client.force_login(patient_user)
        
        url = reverse('dashboard:patient_appointment_events')
        response = client.get(url)
        
        assert response.status_code == 200
        
        # Should be JSON response
        data = response.json()
        assert isinstance(data, list)
    
    def test_doctor_calendar_events(self, client, doctor_user, appointment):
        """Doctor can get calendar events as JSON"""
        doctor_user.email_verified = True
        doctor_user.save()
        client.force_login(doctor_user)
        
        url = reverse('dashboard:doctor_appointment_events')
        response = client.get(url)
        
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)