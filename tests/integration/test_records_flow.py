# tests/integration/test_records_flow.py
"""
Integration tests for Medical Records Flow:
- Patient creates health profile
- Patient adds medical history
- Patient uploads documents
- Doctor views patient records
"""

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from records.models import HealthProfile, MedicalHistory, MedicalDocument
from datetime import date

User = get_user_model()

@pytest.mark.django_db
class TestHealthProfileFlow:
    """Test health profile management"""
    
    def test_patient_can_view_health_profile(self, client, patient_user):
        """Patient can view health profile page"""
        patient_user.email_verified = True
        patient_user.save()
        client.force_login(patient_user)
        
        url = reverse('dashboard:patient_health_profile')
        response = client.get(url)
        
        assert response.status_code == 200
    
    def test_patient_can_update_health_profile(self, client, patient_user):
        """Patient can update health profile"""
        patient_user.email_verified = True
        patient_user.save()
        client.force_login(patient_user)
        
        url = reverse('dashboard:patient_health_profile')
        data = {
            'blood_type': 'A+',
            'height_cm': '175.5',
            'weight_kg': '70.0',
            'allergies': 'Penicillin',
            'chronic_conditions': 'None',
            'current_medications': 'Vitamin D',
            'smoking_status': 'never',
            'alcohol_consumption': 'occasional',
            'emergency_contact_name': 'Jane Doe',
            'emergency_contact_phone': '+1234567890',
            'emergency_contact_relationship': 'Spouse',
        }
        
        response = client.post(url, data)
        
        # Should redirect or show success
        assert response.status_code in [200, 302]
        
        # Profile should be updated
        profile = HealthProfile.objects.get(patient=patient_user)
        assert profile.blood_type == 'A+'
        assert profile.allergies == 'Penicillin'


@pytest.mark.django_db
class TestMedicalHistoryFlow:
    """Test medical history management"""
    
    def test_patient_can_view_medical_history(self, client, patient_user):
        """Patient can view medical history page"""
        patient_user.email_verified = True
        patient_user.save()
        client.force_login(patient_user)
        
        url = reverse('dashboard:patient_medical_history')
        response = client.get(url)
        
        assert response.status_code == 200
    
    def test_patient_can_add_medical_history(self, client, patient_user):
        """Patient can add medical history entry"""
        patient_user.email_verified = True
        patient_user.save()
        client.force_login(patient_user)
        
        url = reverse('dashboard:patient_medical_history')
        data = {
            'event_type': 'vaccination',
            'title': 'COVID-19 Vaccination',
            'description': 'Pfizer booster shot',
            'event_date': '2024-01-15',
            'doctor_name': 'Dr. Smith',
            'hospital_name': 'City Hospital',
            'notes': 'No side effects',
        }
        
        response = client.post(url, data)
        
        # Should redirect
        assert response.status_code == 302
        
        # Entry should be created
        entry = MedicalHistory.objects.filter(
            patient=patient_user,
            title='COVID-19 Vaccination'
        ).first()
        
        assert entry is not None
        assert entry.event_type == 'vaccination'
    
    def test_patient_can_delete_medical_history(self, client, patient_user):
        """Patient can delete medical history entry"""
        patient_user.email_verified = True
        patient_user.save()
        client.force_login(patient_user)
        
        # Create entry first
        entry = MedicalHistory.objects.create(
            patient=patient_user,
            event_type='diagnosis',
            title='Test Entry',
            event_date=date.today()
        )
        
        url = reverse('dashboard:patient_medical_history_delete', kwargs={'pk': entry.pk})
        response = client.post(url)
        
        # Should redirect
        assert response.status_code == 302
        
        # Entry should be deleted
        assert not MedicalHistory.objects.filter(pk=entry.pk).exists()


@pytest.mark.django_db
class TestMedicalDocumentsFlow:
    """Test medical documents management"""
    
    def test_patient_can_view_documents_page(self, client, patient_user):
        """Patient can view documents page"""
        patient_user.email_verified = True
        patient_user.save()
        client.force_login(patient_user)
        
        url = reverse('dashboard:patient_medical_documents')
        response = client.get(url)
        
        assert response.status_code == 200
    
    def test_patient_can_upload_document(self, client, patient_user):
        """Patient can upload medical document"""
        patient_user.email_verified = True
        patient_user.save()
        client.force_login(patient_user)
        
        # Create a fake file
        file_content = b'This is a test document content.'
        test_file = SimpleUploadedFile(
            name='test_report.pdf',
            content=file_content,
            content_type='application/pdf'
        )
        
        url = reverse('dashboard:patient_medical_documents')
        data = {
            'title': 'Blood Test Report',
            'document_type': 'lab_report',
            'file': test_file,
            'description': 'Annual blood work',
            'document_date': '2024-01-20',
        }
        
        response = client.post(url, data)
        
        # Should redirect
        assert response.status_code == 302
        
        # Document should be created
        doc = MedicalDocument.objects.filter(
            patient=patient_user,
            title='Blood Test Report'
        ).first()
        
        assert doc is not None
        assert doc.document_type == 'lab_report'
    
    def test_patient_can_delete_document(self, client, patient_user):
        """Patient can delete document"""
        patient_user.email_verified = True
        patient_user.save()
        client.force_login(patient_user)
        
        # Create document first
        file_content = b'Test content'
        test_file = SimpleUploadedFile('test.pdf', file_content, 'application/pdf')
        
        doc = MedicalDocument.objects.create(
            patient=patient_user,
            title='Test Doc',
            document_type='other',
            file=test_file
        )
        
        url = reverse('dashboard:patient_document_delete', kwargs={'pk': doc.pk})
        response = client.post(url)
        
        # Should redirect
        assert response.status_code == 302
        
        # Document should be deleted
        assert not MedicalDocument.objects.filter(pk=doc.pk).exists()


@pytest.mark.django_db
class TestDoctorViewsPatientRecords:
    """Test doctor viewing patient records"""
    
    def test_doctor_can_view_patient_records(self, client, doctor_user, patient_user, appointment):
        """Doctor can view patient medical records"""
        doctor_user.email_verified = True
        doctor_user.save()
        client.force_login(doctor_user)
        
        # Create health profile for patient
        HealthProfile.objects.create(
            patient=patient_user,
            blood_type='O+',
            allergies='None'
        )
        
        url = reverse('dashboard:doctor_patient_records', kwargs={'pk': patient_user.pk})
        response = client.get(url)
        
        assert response.status_code == 200
        assert response.context['patient'].id == patient_user.id
    
    def test_doctor_cannot_view_unrelated_patient_records(self, client, doctor_user):
        """Doctor cannot view records of patient they haven't treated"""
        doctor_user.email_verified = True
        doctor_user.save()
        client.force_login(doctor_user)
        
        # Create unrelated patient
        from accounts.models import PatientProfile
        unrelated_patient = User.objects.create_user(
            email='unrelated@test.com',
            password='testpass123',
            first_name='Unrelated',
            last_name='Patient',
            user_type='patient'
        )
        PatientProfile.objects.create(user=unrelated_patient)
        
        url = reverse('dashboard:doctor_patient_records', kwargs={'pk': unrelated_patient.pk})
        response = client.get(url)
        
        # Should redirect with error
        assert response.status_code == 302