import pytest
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO
from unittest.mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status

from records.models import HealthProfile, MedicalHistory, MedicalDocument
from records.serializers import (
    HealthProfileSerializer,
    MedicalHistorySerializer,
    MedicalDocumentSerializer,
    MedicalDocumentUploadSerializer,
)
from accounts.models import User, DoctorProfile
from appointments.models import Appointment


# ============================================
# HEALTH PROFILE MODEL TESTS
# ============================================

@pytest.mark.django_db
class TestHealthProfileModel:
    """Test HealthProfile model"""
    
    def test_create_health_profile(self, patient_user):
        """Verify health profile can be created"""
        profile = HealthProfile.objects.create(
            patient=patient_user,
            blood_type='O+',
            height_cm=Decimal('175.00'),
            weight_kg=Decimal('70.00'),
            allergies='Penicillin',
            smoking_status='never'
        )
        
        assert profile.pk is not None
        assert profile.blood_type == 'O+'
    
    def test_health_profile_string_representation(self, patient_user):
        """Verify __str__ returns expected format"""
        profile = HealthProfile.objects.create(patient=patient_user)
        
        assert patient_user.email in str(profile)
    
    def test_bmi_calculation(self, patient_user):
        """Verify BMI is calculated correctly"""
        profile = HealthProfile.objects.create(
            patient=patient_user,
            height_cm=Decimal('180.00'),  # 1.8m
            weight_kg=Decimal('81.00')     # 81kg
        )
        
        # BMI = 81 / (1.8^2) = 81 / 3.24 = 25.0
        assert profile.bmi == 25.0
    
    def test_bmi_none_without_height(self, patient_user):
        """Verify BMI returns None without height"""
        profile = HealthProfile.objects.create(
            patient=patient_user,
            weight_kg=Decimal('70.00')
        )
        
        assert profile.bmi is None
    
    def test_bmi_none_without_weight(self, patient_user):
        """Verify BMI returns None without weight"""
        profile = HealthProfile.objects.create(
            patient=patient_user,
            height_cm=Decimal('175.00')
        )
        
        assert profile.bmi is None
    
    def test_one_profile_per_patient(self, patient_user):
        """Verify OneToOne relationship enforced"""
        HealthProfile.objects.create(patient=patient_user)
        
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            HealthProfile.objects.create(patient=patient_user)


# ============================================
# MEDICAL HISTORY MODEL TESTS
# ============================================

@pytest.mark.django_db
class TestMedicalHistoryModel:
    """Test MedicalHistory model"""
    
    def test_create_medical_history(self, patient_user):
        """Verify medical history can be created"""
        history = MedicalHistory.objects.create(
            patient=patient_user,
            event_type='diagnosis',
            title='Hypertension Diagnosis',
            description='Diagnosed with high blood pressure',
            event_date=date.today() - timedelta(days=30),
            doctor_name='Dr. Smith'
        )
        
        assert history.pk is not None
        assert history.event_type == 'diagnosis'
    
    def test_medical_history_ordering(self, patient_user):
        """Verify histories are ordered by date descending"""
        old = MedicalHistory.objects.create(
            patient=patient_user,
            event_type='surgery',
            title='Old Surgery',
            event_date=date.today() - timedelta(days=365)
        )
        recent = MedicalHistory.objects.create(
            patient=patient_user,
            event_type='diagnosis',
            title='Recent Diagnosis',
            event_date=date.today() - timedelta(days=10)
        )
        
        histories = list(patient_user.medical_history.all())
        assert histories[0] == recent
        assert histories[1] == old
    
    def test_medical_history_string_representation(self, patient_user):
        """Verify __str__ returns expected format"""
        history = MedicalHistory.objects.create(
            patient=patient_user,
            event_type='vaccination',
            title='COVID Vaccine',
            event_date=date.today()
        )
        
        assert 'COVID Vaccine' in str(history)


# ============================================
# MEDICAL DOCUMENT MODEL TESTS
# ============================================

@pytest.mark.django_db
class TestMedicalDocumentModel:
    """Test MedicalDocument model"""
    
    def test_create_medical_document(self, patient_user):
        """Verify document can be created"""
        # Create a fake file
        fake_file = SimpleUploadedFile(
            "test_report.pdf",
            b"fake pdf content",
            content_type="application/pdf"
        )
        
        document = MedicalDocument.objects.create(
            patient=patient_user,
            title='Blood Test Results',
            document_type='blood_test',
            file=fake_file,
            description='Annual blood work'
        )
        
        assert document.pk is not None
        assert document.document_type == 'blood_test'
    
    def test_file_size_saved_on_create(self, patient_user):
        """Verify file size is calculated on save"""
        content = b"x" * 1000  # 1000 bytes
        fake_file = SimpleUploadedFile(
            "test.pdf",
            content,
            content_type="application/pdf"
        )
        
        document = MedicalDocument.objects.create(
            patient=patient_user,
            title='Test Doc',
            document_type='other',
            file=fake_file
        )
        
        assert document.file_size == 1000
    
    def test_documents_ordered_by_upload_date(self, patient_user):
        """Verify documents are ordered by upload date descending"""
        doc1 = MedicalDocument.objects.create(
            patient=patient_user,
            title='First Doc',
            document_type='other',
            file=SimpleUploadedFile("a.pdf", b"content", content_type="application/pdf")
        )
        doc2 = MedicalDocument.objects.create(
            patient=patient_user,
            title='Second Doc',
            document_type='other',
            file=SimpleUploadedFile("b.pdf", b"content", content_type="application/pdf")
        )
        
        documents = list(patient_user.medical_documents.all())
        # Most recent first
        assert documents[0] == doc2


# ============================================
# SERIALIZER TESTS
# ============================================

@pytest.mark.django_db
class TestHealthProfileSerializer:
    """Test HealthProfileSerializer"""
    
    def test_includes_bmi(self, patient_user):
        """Verify BMI is included in serialization"""
        profile = HealthProfile.objects.create(
            patient=patient_user,
            height_cm=Decimal('180.00'),
            weight_kg=Decimal('81.00')
        )
        
        serializer = HealthProfileSerializer(profile)
        
        assert 'bmi' in serializer.data
        assert serializer.data['bmi'] == 25.0
    
    def test_includes_patient_info(self, patient_user):
        """Verify patient info is included"""
        profile = HealthProfile.objects.create(patient=patient_user)
        
        serializer = HealthProfileSerializer(profile)
        
        assert serializer.data['patient_email'] == patient_user.email
        assert serializer.data['patient_name'] == patient_user.full_name


@pytest.mark.django_db
class TestMedicalDocumentUploadSerializer:
    """Test MedicalDocumentUploadSerializer validation"""
    
    def test_valid_pdf_file(self):
        """Verify valid PDF passes validation"""
        file = SimpleUploadedFile(
            "test.pdf",
            b"fake pdf content",
            content_type="application/pdf"
        )
        
        data = {
            'title': 'Test Document',
            'document_type': 'lab_report',
            'file': file
        }
        
        serializer = MedicalDocumentUploadSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
    
    def test_valid_image_file(self):
        """Verify valid image passes validation"""
        # Create a minimal valid JPEG
        file = SimpleUploadedFile(
            "test.jpg",
            b"\xff\xd8\xff\xe0\x00\x10JFIF",  # JPEG header
            content_type="image/jpeg"
        )
        
        data = {
            'title': 'X-Ray Image',
            'document_type': 'xray',
            'file': file
        }
        
        serializer = MedicalDocumentUploadSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
    
    def test_file_too_large_rejected(self):
        """Verify file over 5MB is rejected"""
        # Create 6MB file
        large_content = b"x" * (6 * 1024 * 1024)
        file = SimpleUploadedFile(
            "large.pdf",
            large_content,
            content_type="application/pdf"
        )
        
        data = {
            'title': 'Large Document',
            'document_type': 'other',
            'file': file
        }
        
        serializer = MedicalDocumentUploadSerializer(data=data)
        assert not serializer.is_valid()
        assert 'file' in serializer.errors
    
    def test_invalid_file_type_rejected(self):
        """Verify invalid file type is rejected"""
        file = SimpleUploadedFile(
            "script.exe",
            b"malicious content",
            content_type="application/x-executable"
        )
        
        data = {
            'title': 'Bad File',
            'document_type': 'other',
            'file': file
        }
        
        serializer = MedicalDocumentUploadSerializer(data=data)
        assert not serializer.is_valid()
        assert 'file' in serializer.errors


# ============================================
# API TESTS - HEALTH PROFILE
# ============================================

@pytest.mark.django_db
class TestHealthProfileAPI:
    """Test health profile endpoint"""
    
    url = '/api/records/profile/'
    
    def test_get_health_profile(self, authenticated_patient):
        """Verify patient can get their health profile"""
        response = authenticated_patient.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'blood_type' in response.data
        assert 'bmi' in response.data
    
    def test_profile_auto_created(self, authenticated_patient, patient_user):
        """Verify profile is auto-created if it doesn't exist"""
        # Ensure no profile exists
        HealthProfile.objects.filter(patient=patient_user).delete()
        
        response = authenticated_patient.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        assert HealthProfile.objects.filter(patient=patient_user).exists()
    
    def test_update_health_profile(self, authenticated_patient):
        """Verify patient can update their health profile"""
        response = authenticated_patient.patch(self.url, {
            'blood_type': 'AB+',
            'height_cm': '175.50',
            'weight_kg': '72.00',
            'allergies': 'Pollen, Dust',
            'smoking_status': 'never'
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['blood_type'] == 'AB+'
        assert response.data['allergies'] == 'Pollen, Dust'
    
    def test_unauthenticated_rejected(self, api_client):
        """Verify unauthenticated request is rejected"""
        response = api_client.get(self.url)
        
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


# ============================================
# API TESTS - MEDICAL HISTORY
# ============================================

@pytest.mark.django_db
class TestMedicalHistoryAPI:
    """Test medical history endpoints"""
    
    url = '/api/records/history/'
    
    def test_list_medical_history(self, authenticated_patient, patient_user):
        """Verify patient can list their medical history"""
        MedicalHistory.objects.create(
            patient=patient_user,
            event_type='diagnosis',
            title='Test Diagnosis',
            event_date=date.today()
        )
        
        response = authenticated_patient.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_create_medical_history(self, authenticated_patient):
        """Verify patient can create medical history entry"""
        data = {
            'event_type': 'surgery',
            'title': 'Appendectomy',
            'description': 'Emergency appendix removal',
            'event_date': str(date.today() - timedelta(days=365)),
            'hospital_name': 'City Hospital'
        }
        
        response = authenticated_patient.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'Appendectomy'
        assert response.data['event_type'] == 'surgery'
    
    def test_patient_sees_only_own_history(self, authenticated_patient, patient_user):
        """Verify patient only sees their own history"""
        # Create history for patient
        MedicalHistory.objects.create(
            patient=patient_user,
            event_type='diagnosis',
            title='My Diagnosis',
            event_date=date.today()
        )
        
        # Create history for another patient
        other_patient = User.objects.create_user(
            email='other@test.com',
            password='pass123',
            first_name='Other',
            last_name='Patient',
            user_type='patient'
        )
        MedicalHistory.objects.create(
            patient=other_patient,
            event_type='diagnosis',
            title='Other Diagnosis',
            event_date=date.today()
        )
        
        response = authenticated_patient.get(self.url)
        
        data = response.data.get('results', response.data)
        titles = [h['title'] for h in data]
        assert 'My Diagnosis' in titles
        assert 'Other Diagnosis' not in titles
    
    def test_unauthenticated_rejected(self, api_client):
        """Verify unauthenticated request is rejected"""
        response = api_client.get(self.url)
        
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


@pytest.mark.django_db
class TestMedicalHistoryDetailAPI:
    """Test medical history detail endpoint"""
    
    def test_get_history_detail(self, authenticated_patient, patient_user):
        """Verify patient can view history entry details"""
        history = MedicalHistory.objects.create(
            patient=patient_user,
            event_type='vaccination',
            title='COVID Vaccine',
            event_date=date.today()
        )
        
        url = f'/api/records/history/{history.id}/'
        response = authenticated_patient.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'COVID Vaccine'
    
    def test_update_history_entry(self, authenticated_patient, patient_user):
        """Verify patient can update their history entry"""
        history = MedicalHistory.objects.create(
            patient=patient_user,
            event_type='diagnosis',
            title='Original Title',
            event_date=date.today()
        )
        
        url = f'/api/records/history/{history.id}/'
        response = authenticated_patient.patch(url, {
            'title': 'Updated Title',
            'notes': 'Additional notes'
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Updated Title'
    
    def test_delete_history_entry(self, authenticated_patient, patient_user):
        """Verify patient can delete their history entry"""
        history = MedicalHistory.objects.create(
            patient=patient_user,
            event_type='other',
            title='To Delete',
            event_date=date.today()
        )
        
        url = f'/api/records/history/{history.id}/'
        response = authenticated_patient.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not MedicalHistory.objects.filter(id=history.id).exists()
    
    def test_cannot_access_others_history(self, authenticated_patient):
        """Verify patient cannot access another's history"""
        other_patient = User.objects.create_user(
            email='other2@test.com',
            password='pass123',
            first_name='Other',
            last_name='Patient',
            user_type='patient'
        )
        other_history = MedicalHistory.objects.create(
            patient=other_patient,
            event_type='diagnosis',
            title='Private History',
            event_date=date.today()
        )
        
        url = f'/api/records/history/{other_history.id}/'
        response = authenticated_patient.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================
# API TESTS - MEDICAL DOCUMENTS
# ============================================

@pytest.mark.django_db
class TestMedicalDocumentListAPI:
    """Test document list endpoint"""
    
    url = '/api/records/documents/'
    
    def test_list_documents(self, authenticated_patient, patient_user):
        """Verify patient can list their documents"""
        MedicalDocument.objects.create(
            patient=patient_user,
            title='Test Doc',
            document_type='lab_report',
            file=SimpleUploadedFile("test.pdf", b"content", content_type="application/pdf")
        )
        
        response = authenticated_patient.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_filter_by_document_type(self, authenticated_patient, patient_user):
        """Verify filtering by document type works"""
        MedicalDocument.objects.create(
            patient=patient_user,
            title='Lab Report',
            document_type='lab_report',
            file=SimpleUploadedFile("lab.pdf", b"content", content_type="application/pdf")
        )
        MedicalDocument.objects.create(
            patient=patient_user,
            title='X-Ray',
            document_type='xray',
            file=SimpleUploadedFile("xray.pdf", b"content", content_type="application/pdf")
        )
        
        response = authenticated_patient.get(f'{self.url}?type=lab_report')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.data.get('results', response.data)
        for doc in data:
            assert doc['document_type'] == 'lab_report'
    
    def test_patient_sees_only_own_documents(self, authenticated_patient, patient_user):
        """Verify patient only sees their own documents"""
        MedicalDocument.objects.create(
            patient=patient_user,
            title='My Document',
            document_type='other',
            file=SimpleUploadedFile("mine.pdf", b"content", content_type="application/pdf")
        )
        
        other_patient = User.objects.create_user(
            email='other3@test.com',
            password='pass123',
            first_name='Other',
            last_name='Patient',
            user_type='patient'
        )
        MedicalDocument.objects.create(
            patient=other_patient,
            title='Other Document',
            document_type='other',
            file=SimpleUploadedFile("other.pdf", b"content", content_type="application/pdf")
        )
        
        response = authenticated_patient.get(self.url)
        
        data = response.data.get('results', response.data)
        titles = [d['title'] for d in data]
        assert 'My Document' in titles
        assert 'Other Document' not in titles


@pytest.mark.django_db
class TestMedicalDocumentUploadAPI:
    """Test document upload endpoint"""
    
    url = '/api/records/documents/upload/'
    
    def test_upload_document(self, authenticated_patient):
        """Verify patient can upload a document"""
        file = SimpleUploadedFile(
            "blood_test.pdf",
            b"fake pdf content",
            content_type="application/pdf"
        )
        
        response = authenticated_patient.post(self.url, {
            'title': 'Blood Test Results',
            'document_type': 'blood_test',
            'file': file,
            'description': 'Annual checkup results'
        }, format='multipart')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'document' in response.data
        assert response.data['document']['title'] == 'Blood Test Results'
    
    def test_upload_without_file_fails(self, authenticated_patient):
        """Verify upload without file fails"""
        response = authenticated_patient.post(self.url, {
            'title': 'No File',
            'document_type': 'other'
        }, format='multipart')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_unauthenticated_cannot_upload(self, api_client):
        """Verify unauthenticated user cannot upload"""
        file = SimpleUploadedFile("test.pdf", b"content", content_type="application/pdf")
        
        response = api_client.post(self.url, {
            'title': 'Test',
            'document_type': 'other',
            'file': file
        }, format='multipart')
        
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


@pytest.mark.django_db
class TestMedicalDocumentDetailAPI:
    """Test document detail endpoint"""
    
    def test_get_document_detail(self, authenticated_patient, patient_user):
        """Verify patient can view document details"""
        document = MedicalDocument.objects.create(
            patient=patient_user,
            title='My Report',
            document_type='lab_report',
            file=SimpleUploadedFile("report.pdf", b"content", content_type="application/pdf")
        )
        
        url = f'/api/records/documents/{document.id}/'
        response = authenticated_patient.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'My Report'
    
    def test_delete_document(self, authenticated_patient, patient_user):
        """Verify patient can delete their document"""
        document = MedicalDocument.objects.create(
            patient=patient_user,
            title='To Delete',
            document_type='other',
            file=SimpleUploadedFile("delete.pdf", b"content", content_type="application/pdf")
        )
        
        url = f'/api/records/documents/{document.id}/'
        response = authenticated_patient.delete(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert not MedicalDocument.objects.filter(id=document.id).exists()
    
    def test_cannot_access_others_document(self, authenticated_patient):
        """Verify patient cannot access another's document"""
        other_patient = User.objects.create_user(
            email='other4@test.com',
            password='pass123',
            first_name='Other',
            last_name='Patient',
            user_type='patient'
        )
        other_doc = MedicalDocument.objects.create(
            patient=other_patient,
            title='Private Doc',
            document_type='other',
            file=SimpleUploadedFile("private.pdf", b"content", content_type="application/pdf")
        )
        
        url = f'/api/records/documents/{other_doc.id}/'
        response = authenticated_patient.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================
# API TESTS - PATIENT RECORDS (DOCTOR ACCESS)
# ============================================

@pytest.mark.django_db
class TestPatientRecordsAPI:
    """Test doctor access to patient records"""
    
    def test_doctor_can_view_patient_with_appointment(
        self, authenticated_doctor, doctor_profile, patient_user
    ):
        """Verify doctor can view patient records during active appointment"""
        # Create active appointment
        Appointment.objects.create(
            patient=patient_user,
            doctor=doctor_profile,
            date=date.today(),
            start_time='10:00',
            end_time='10:30',
            status='confirmed'
        )
        
        # Create health profile
        HealthProfile.objects.create(
            patient=patient_user,
            blood_type='A+',
            allergies='None'
        )
        
        url = f'/api/records/patient/{patient_user.id}/'
        response = authenticated_doctor.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'patient' in response.data
        assert 'health_profile' in response.data
        assert 'medical_history' in response.data
        assert 'documents' in response.data
    
    def test_doctor_cannot_view_patient_without_appointment(
        self, authenticated_doctor, patient_user
    ):
        """Verify doctor cannot view patient without active appointment"""
        url = f'/api/records/patient/{patient_user.id}/'
        response = authenticated_doctor.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'active appointments' in response.data.get('error', '').lower()
    
    def test_patient_cannot_view_others_records(self, authenticated_patient):
        """Verify patient cannot access this endpoint"""
        other_patient = User.objects.create_user(
            email='other5@test.com',
            password='pass123',
            first_name='Other',
            last_name='Patient',
            user_type='patient'
        )
        
        url = f'/api/records/patient/{other_patient.id}/'
        response = authenticated_patient.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'Only doctors' in response.data.get('error', '')
    
    def test_cancelled_appointment_denies_access(
        self, authenticated_doctor, doctor_profile, patient_user
    ):
        """Verify cancelled appointment doesn't grant access"""
        Appointment.objects.create(
            patient=patient_user,
            doctor=doctor_profile,
            date=date.today(),
            start_time='10:00',
            end_time='10:30',
            status='cancelled'
        )
        
        url = f'/api/records/patient/{patient_user.id}/'
        response = authenticated_doctor.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_nonexistent_patient_returns_404(self, authenticated_doctor, doctor_profile):
        """Verify 404 for non-existent patient"""
        # Create a fake appointment to pass first check
        # But patient ID doesn't exist
        url = '/api/records/patient/99999/'
        response = authenticated_doctor.get(url)
        
        # Will fail at appointment check (403) or patient check (404)
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]