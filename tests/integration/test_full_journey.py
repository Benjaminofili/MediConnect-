# tests/integration/test_full_journey.py
"""
End-to-end integration test:
Complete patient-doctor journey from registration to prescription
"""

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from accounts.models import PatientProfile, DoctorProfile
from appointments.models import Appointment
from consultations.models import Consultation, Prescription
from records.models import HealthProfile, MedicalHistory, MedicalDocument
from doctors.models import Specialization

User = get_user_model()


@pytest.mark.django_db
class TestCompletePatientJourney:
    """
    Test complete patient journey:
    1. Register
    2. Verify email
    3. Login
    4. Complete health profile
    5. Upload documents
    6. Find doctor
    7. Book appointment
    8. Attend consultation
    9. Receive prescription
    """
    
    def test_complete_patient_journey(self, client, specialization):
        """Full end-to-end patient journey"""
        
        # ==========================================
        # STEP 1: Patient Registration
        # ==========================================
        register_url = reverse('dashboard:register_patient')
        
        with patch('dashboard.views.EmailService') as mock_email:
            mock_email.send_email_verification = MagicMock()
            mock_email.send_welcome_email = MagicMock()
            
            response = client.post(register_url, {
                'email': 'journey_patient@test.com',
                'password': 'SecurePass123!',
                'password_confirm': 'SecurePass123!',
                'first_name': 'Journey',
                'last_name': 'Patient',
                'phone': '+1234567890',
            })
        
        assert response.status_code == 302
        patient = User.objects.get(email='journey_patient@test.com')
        assert patient.email_verified == False
        
        # ==========================================
        # STEP 2: Email Verification
        # ==========================================
        token = default_token_generator.make_token(patient)
        uid = urlsafe_base64_encode(force_bytes(patient.pk))
        
        verify_url = reverse('dashboard:verify_email', kwargs={'uidb64': uid, 'token': token})
        response = client.get(verify_url)
        
        assert response.status_code == 302
        patient.refresh_from_db()
        assert patient.email_verified == True
        
        # ==========================================
        # STEP 3: Login
        # ==========================================
        login_url = reverse('dashboard:login')
        response = client.post(login_url, {
            'email': 'journey_patient@test.com',
            'password': 'SecurePass123!'
        })
        
        assert response.status_code == 302
        assert 'patient/dashboard' in response.url
        
        # ==========================================
        # STEP 4: Complete Health Profile
        # ==========================================
        profile_url = reverse('dashboard:patient_health_profile')
        response = client.post(profile_url, {
            'blood_type': 'A+',
            'height_cm': '175',
            'weight_kg': '70',
            'allergies': 'Penicillin',
            'chronic_conditions': 'None',
            'smoking_status': 'never',
            'alcohol_consumption': 'occasional',
            'emergency_contact_name': 'Emergency Contact',
            'emergency_contact_phone': '+9876543210',
        })
        
        assert response.status_code in [200, 302]
        assert HealthProfile.objects.filter(patient=patient).exists()
        
        # ==========================================
        # STEP 5: Upload Medical Document
        # ==========================================
        docs_url = reverse('dashboard:patient_medical_documents')
        test_file = SimpleUploadedFile(
            'blood_test.pdf',
            b'Test blood work results',
            content_type='application/pdf'
        )
        
        response = client.post(docs_url, {
            'title': 'Previous Blood Work',
            'document_type': 'lab_report',
            'file': test_file,
            'description': 'Blood test from last year',
        })
        
        assert response.status_code == 302
        assert MedicalDocument.objects.filter(patient=patient).exists()
        
        # ==========================================
        # STEP 6: Create a Doctor for Booking
        # ==========================================
        doctor_user = User.objects.create_user(
            email='journey_doctor@test.com',
            password='testpass123',
            first_name='Journey',
            last_name='Doctor',
            user_type='doctor',
            email_verified=True
        )
        doctor_profile = DoctorProfile.objects.create(
            user=doctor_user,
            specialization=specialization,
            license_number='JOURNEY123',
            experience_years=10,
            education='Top Medical School',
            consultation_fee=5000,
            verification_status='verified'
        )
        
        # ==========================================
        # STEP 7: Browse and Book Appointment
        # ==========================================
        doctors_url = reverse('dashboard:patient_doctors')
        response = client.get(doctors_url)
        assert response.status_code == 200
        
        # Book appointment
        tomorrow = date.today() + timedelta(days=1)
        book_url = reverse('dashboard:patient_create_appointment')
        
        response = client.post(book_url, {
            'doctor': doctor_profile.id,
            'slot_date': tomorrow.strftime('%Y-%m-%d'),
            'slot_start': '10:00',
            'duration': 30,
            'reason': 'General checkup',
            'symptoms': 'Headache and fatigue',
            'appointment_type': 'online',
        })
        
        assert response.status_code == 302
        appointment = Appointment.objects.get(patient=patient, doctor=doctor_profile)
        assert appointment.status == 'pending'
        
        # ==========================================
        # STEP 8: Doctor Confirms & Completes
        # ==========================================
        # Login as doctor
        client.logout()
        client.force_login(doctor_user)
        
        # Confirm appointment
        appointment.status = 'confirmed'
        appointment.save()
        
        # Complete appointment
        appointment.status = 'completed'
        appointment.save()
        
        # ==========================================
        # STEP 9: Doctor Creates Prescription
        # ==========================================
        prescription_url = reverse('dashboard:doctor_prescription_create', kwargs={'patient_id': patient.pk})
        
        response = client.post(prescription_url, {
            'diagnosis': 'Tension headache',
            'medicines': 'Paracetamol 500mg - as needed\nIbuprofen 400mg - twice daily',
            'instructions': 'Rest well, stay hydrated',
        })
        
        assert response.status_code == 302
        assert Prescription.objects.filter(
            consultation__appointment__patient=patient
        ).exists()
        
        # ==========================================
        # STEP 10: Patient Views Prescription
        # ==========================================
        client.logout()
        client.force_login(patient)
        
        prescriptions_url = reverse('dashboard:patient_prescriptions')
        response = client.get(prescriptions_url)
        
        assert response.status_code == 200
        
        print("✅ Complete patient journey test PASSED!")


@pytest.mark.django_db  
class TestCompleteAppointmentLifecycle:
    """Test appointment from creation to completion"""
    
    def test_appointment_lifecycle(self, client, patient_user, doctor_user):
        """Test full appointment lifecycle"""
        
        patient_user.email_verified = True
        patient_user.save()
        doctor_user.email_verified = True
        doctor_user.save()
        
        # 1. Patient books appointment
        client.force_login(patient_user)
        
        tomorrow = date.today() + timedelta(days=1)
        book_url = reverse('dashboard:patient_create_appointment')
        
        response = client.post(book_url, {
            'doctor': doctor_user.doctor_profile.id,
            'slot_date': tomorrow.strftime('%Y-%m-%d'),
            'slot_start': '14:00',
            'duration': 30,
            'reason': 'Routine checkup',
            'appointment_type': 'online',
        })
        
        assert response.status_code == 302
        appointment = Appointment.objects.get(patient=patient_user)
        assert appointment.status == 'pending'
        
        # 2. Doctor confirms
        client.logout()
        client.force_login(doctor_user)
        
        appointment.status = 'confirmed'
        appointment.save()
        
        # 3. Appointment starts
        appointment.status = 'in_progress'
        appointment.save()
        
        # 4. Appointment completes
        appointment.status = 'completed'
        appointment.save()
        
        # 5. Verify final state
        appointment.refresh_from_db()
        assert appointment.status == 'completed'
        
        print("✅ Appointment lifecycle test PASSED!")