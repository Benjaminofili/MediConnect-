# tests/integration/test_consultation_flow.py
"""
Integration tests for Video Consultation Flow:
- Join video call
- Complete consultation
- Create prescription
"""

import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import date, time, timedelta
from unittest.mock import patch, MagicMock
from appointments.models import Appointment
from consultations.models import Consultation, Prescription, PrescriptionItem


@pytest.mark.django_db
class TestVideoConsultationFlow:
    """Test video consultation journey"""
    
    def test_patient_can_access_encounter(self, client, patient_user, appointment):
        """Patient can access active encounter"""
        patient_user.email_verified = True
        patient_user.save()
        client.force_login(patient_user)
        
        # Set appointment as confirmed and today
        appointment.status = 'confirmed'
        appointment.date = date.today()
        appointment.start_time = (timezone.now() - timedelta(minutes=5)).time()
        appointment.end_time = (timezone.now() + timedelta(minutes=25)).time()
        appointment.video_room_url = 'https://whereby.com/test-room'
        appointment.save()
        
        url = reverse('dashboard:active_encounter', kwargs={'appointment_id': appointment.pk})
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'appointment' in response.context
    
    def test_doctor_can_access_encounter(self, client, doctor_user, appointment):
        """Doctor can access active encounter"""
        doctor_user.email_verified = True
        doctor_user.save()
        client.force_login(doctor_user)
        
        # Set appointment as confirmed
        appointment.status = 'confirmed'
        appointment.date = date.today()
        appointment.start_time = (timezone.now() - timedelta(minutes=5)).time()
        appointment.end_time = (timezone.now() + timedelta(minutes=25)).time()
        appointment.video_room_url = 'https://whereby.com/test-room'
        appointment.video_host_url = 'https://whereby.com/test-room?host'
        appointment.save()
        
        url = reverse('dashboard:active_encounter', kwargs={'appointment_id': appointment.pk})
        response = client.get(url)
        
        assert response.status_code == 200
    
    def test_doctor_can_end_encounter(self, client, doctor_user, appointment):
        """Doctor can complete consultation"""
        doctor_user.email_verified = True
        doctor_user.save()
        client.force_login(doctor_user)
        
        appointment.status = 'in_progress'
        appointment.save()
        
        url = reverse('dashboard:end_encounter', kwargs={'appointment_id': appointment.pk})
        response = client.post(url)
        
        # Should redirect
        assert response.status_code == 302


@pytest.mark.django_db
class TestPrescriptionFlow:
    """Test prescription creation"""
    
    def test_doctor_can_view_prescriptions_list(self, client, doctor_user):
        """Doctor can view prescriptions list"""
        doctor_user.email_verified = True
        doctor_user.save()
        client.force_login(doctor_user)
        
        url = reverse('dashboard:doctor_prescriptions')
        response = client.get(url)
        
        assert response.status_code == 200
    
    def test_doctor_can_create_prescription(self, client, doctor_user, patient_user, past_appointment):
        """Doctor can create prescription for patient"""
        doctor_user.email_verified = True
        doctor_user.save()
        client.force_login(doctor_user)
        
        url = reverse('dashboard:doctor_prescription_create', kwargs={'patient_id': patient_user.pk})
        
        # GET request - view form
        response = client.get(url)
        assert response.status_code == 200
        
        # POST request - create prescription
        data = {
            'diagnosis': 'Common cold',
            'medicines': 'Paracetamol 500mg - 3 times daily\nVitamin C - once daily',
            'instructions': 'Rest and drink plenty of fluids',
        }
        
        response = client.post(url, data)
        
        # Should redirect to prescription detail
        assert response.status_code == 302
        
        # Prescription should be created
        prescription = Prescription.objects.filter(
            consultation__appointment__patient=patient_user,
            consultation__appointment__doctor=doctor_user.doctor_profile
        ).first()
        
        assert prescription is not None
        assert prescription.diagnosis == 'Common cold'
    
    def test_doctor_can_view_prescription_detail(self, client, doctor_user, patient_user, past_appointment):
        """Doctor can view prescription details"""
        doctor_user.email_verified = True
        doctor_user.save()
        client.force_login(doctor_user)
        
        # Create consultation and prescription
        consultation = Consultation.objects.create(
            appointment=past_appointment,
            diagnosis='Test diagnosis'
        )
        prescription = Prescription.objects.create(
            consultation=consultation,
            diagnosis='Test prescription'
        )
        
        url = reverse('dashboard:doctor_prescription_detail', kwargs={'pk': prescription.pk})
        response = client.get(url)
        
        assert response.status_code == 200
    
    def test_patient_can_view_prescriptions(self, client, patient_user, past_appointment):
        """Patient can view their prescriptions"""
        patient_user.email_verified = True
        patient_user.save()
        client.force_login(patient_user)
        
        # Create consultation and prescription
        consultation = Consultation.objects.create(
            appointment=past_appointment,
            diagnosis='Test diagnosis'
        )
        prescription = Prescription.objects.create(
            consultation=consultation,
            diagnosis='Test'
        )
        
        url = reverse('dashboard:patient_prescriptions')
        response = client.get(url)
        
        assert response.status_code == 200
    
    def test_patient_can_view_prescription_detail(self, client, patient_user, past_appointment):
        """Patient can view prescription details"""
        patient_user.email_verified = True
        patient_user.save()
        client.force_login(patient_user)
        
        consultation = Consultation.objects.create(
            appointment=past_appointment,
            diagnosis='Test'
        )
        prescription = Prescription.objects.create(
            consultation=consultation,
            diagnosis='Test'
        )
        
        url = reverse('dashboard:patient_prescription_detail', kwargs={'pk': prescription.pk})
        response = client.get(url)
        
        assert response.status_code == 200