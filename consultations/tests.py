import pytest
from datetime import date, time, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.utils import timezone
from rest_framework import status

from consultations.models import Consultation, Prescription, PrescriptionItem
from consultations.serializers import (
    ConsultationSerializer,
    ConsultationListSerializer,
    ConsultationUpdateSerializer,
    PrescriptionSerializer,
    PrescriptionItemSerializer,
    CreatePrescriptionSerializer,
)
from appointments.models import Appointment
from accounts.models import User, DoctorProfile


# ============================================
# CONSULTATION MODEL TESTS
# ============================================

@pytest.mark.django_db
class TestConsultationModel:
    """Test Consultation model"""
    
    def test_create_consultation(self, appointment):
        """Verify consultation can be created"""
        consultation = Consultation.objects.create(
            appointment=appointment,
            chief_complaint='Headache',
            diagnosis='Tension headache',
            treatment_plan='Rest and pain medication'
        )
        
        assert consultation.pk is not None
        assert consultation.chief_complaint == 'Headache'
    
    def test_consultation_string_representation(self, appointment):
        """Verify __str__ returns expected format"""
        consultation = Consultation.objects.create(appointment=appointment)
        
        assert appointment.appointment_number in str(consultation)
    
    def test_duration_minutes_calculation(self, appointment):
        """Verify duration is calculated correctly"""
        now = timezone.now()
        consultation = Consultation.objects.create(
            appointment=appointment,
            started_at=now,
            ended_at=now + timedelta(minutes=30)
        )
        
        assert consultation.duration_minutes == 30
    
    def test_duration_none_without_times(self, appointment):
        """Verify duration returns None without start/end times"""
        consultation = Consultation.objects.create(appointment=appointment)
        
        assert consultation.duration_minutes is None
    
    def test_duration_none_without_end_time(self, appointment):
        """Verify duration returns None without end time"""
        consultation = Consultation.objects.create(
            appointment=appointment,
            started_at=timezone.now()
        )
        
        assert consultation.duration_minutes is None
    
    def test_one_consultation_per_appointment(self, appointment):
        """Verify OneToOne relationship enforced"""
        Consultation.objects.create(appointment=appointment)
        
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Consultation.objects.create(appointment=appointment)


# ============================================
# PRESCRIPTION MODEL TESTS
# ============================================

@pytest.mark.django_db
class TestPrescriptionModel:
    """Test Prescription model"""
    
    def test_create_prescription(self, appointment):
        """Verify prescription can be created"""
        consultation = Consultation.objects.create(appointment=appointment)
        
        prescription = Prescription.objects.create(
            consultation=consultation,
            diagnosis='Hypertension',
            notes='Take with food'
        )
        
        assert prescription.pk is not None
        assert prescription.prescription_number is not None
    
    def test_prescription_number_auto_generated(self, appointment):
        """Verify prescription number is auto-generated"""
        consultation = Consultation.objects.create(appointment=appointment)
        
        prescription = Prescription.objects.create(consultation=consultation)
        
        assert prescription.prescription_number.startswith('RX-')
    
    def test_prescription_number_format(self, appointment):
        """Verify prescription number format: RX-YYYYMMDD-XXXX"""
        consultation = Consultation.objects.create(appointment=appointment)
        
        prescription = Prescription.objects.create(consultation=consultation)
        
        parts = prescription.prescription_number.split('-')
        assert len(parts) == 3
        assert parts[0] == 'RX'
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 4  # Random string
    
    def test_prescription_string_representation(self, appointment):
        """Verify __str__ returns expected format"""
        consultation = Consultation.objects.create(appointment=appointment)
        prescription = Prescription.objects.create(consultation=consultation)
        
        assert prescription.prescription_number in str(prescription)


# ============================================
# PRESCRIPTION ITEM MODEL TESTS
# ============================================

@pytest.mark.django_db
class TestPrescriptionItemModel:
    """Test PrescriptionItem model"""
    
    def test_create_prescription_item(self, appointment):
        """Verify prescription item can be created"""
        consultation = Consultation.objects.create(appointment=appointment)
        prescription = Prescription.objects.create(consultation=consultation)
        
        item = PrescriptionItem.objects.create(
            prescription=prescription,
            medicine_name='Paracetamol',
            dosage='500mg',
            frequency='twice_daily',
            duration='7_days',
            quantity='14 tablets',
            instructions='Take after meals'
        )
        
        assert item.pk is not None
        assert item.medicine_name == 'Paracetamol'
    
    def test_prescription_item_string_representation(self, appointment):
        """Verify __str__ returns medicine and dosage"""
        consultation = Consultation.objects.create(appointment=appointment)
        prescription = Prescription.objects.create(consultation=consultation)
        
        item = PrescriptionItem.objects.create(
            prescription=prescription,
            medicine_name='Amoxicillin',
            dosage='250mg',
            frequency='three_times_daily',
            duration='5_days'
        )
        
        assert 'Amoxicillin' in str(item)
        assert '250mg' in str(item)


# ============================================
# SERIALIZER TESTS (No DB needed for validation)
# ============================================

class TestCreatePrescriptionSerializer:
    """Test CreatePrescriptionSerializer validation"""
    
    def test_valid_prescription_data(self):
        """Verify valid prescription data passes validation"""
        data = {
            'diagnosis': 'Common cold',
            'notes': 'Rest and hydration',
            'valid_days': 30,
            'items': [
                {
                    'medicine_name': 'Vitamin C',
                    'dosage': '500mg',
                    'frequency': 'once_daily',
                    'duration': '7_days'
                }
            ]
        }
        
        serializer = CreatePrescriptionSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
    
    def test_empty_items_fails(self):
        """Verify empty items list fails validation"""
        data = {
            'diagnosis': 'Test',
            'items': []
        }
        
        serializer = CreatePrescriptionSerializer(data=data)
        assert not serializer.is_valid()
        assert 'items' in serializer.errors
    
    def test_missing_items_fails(self):
        """Verify missing items fails validation"""
        data = {
            'diagnosis': 'Test'
        }
        
        serializer = CreatePrescriptionSerializer(data=data)
        assert not serializer.is_valid()
        assert 'items' in serializer.errors
    
    def test_valid_days_validation(self):
        """Verify valid_days has min/max constraints"""
        data = {
            'items': [{'medicine_name': 'Test', 'dosage': '10mg', 'frequency': 'once_daily', 'duration': '7_days'}],
            'valid_days': 0  # Below minimum
        }
        
        serializer = CreatePrescriptionSerializer(data=data)
        assert not serializer.is_valid()
        assert 'valid_days' in serializer.errors
    
    def test_multiple_items_allowed(self):
        """Verify multiple prescription items are allowed"""
        data = {
            'items': [
                {'medicine_name': 'Med1', 'dosage': '10mg', 'frequency': 'once_daily', 'duration': '7_days'},
                {'medicine_name': 'Med2', 'dosage': '20mg', 'frequency': 'twice_daily', 'duration': '5_days'},
                {'medicine_name': 'Med3', 'dosage': '5mg', 'frequency': 'as_needed', 'duration': '3_days'},
            ]
        }
        
        serializer = CreatePrescriptionSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert len(serializer.validated_data['items']) == 3


class TestPrescriptionItemSerializer:
    """Test PrescriptionItemSerializer validation"""
    
    def test_valid_item_data(self):
        """Verify valid item data passes validation"""
        data = {
            'medicine_name': 'Ibuprofen',
            'dosage': '400mg',
            'frequency': 'three_times_daily',
            'duration': '5_days',
            'quantity': '15 tablets',
            'instructions': 'Take with food'
        }
        
        serializer = PrescriptionItemSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
    
    def test_required_fields(self):
        """Verify required fields are enforced"""
        data = {}
        
        serializer = PrescriptionItemSerializer(data=data)
        assert not serializer.is_valid()
        assert 'medicine_name' in serializer.errors
        assert 'dosage' in serializer.errors
        assert 'frequency' in serializer.errors
        assert 'duration' in serializer.errors


# ============================================
# API TESTS - CONSULTATION DETAIL
# ============================================

@pytest.mark.django_db
class TestConsultationDetailAPI:
    """Test consultation detail endpoint"""
    
    def test_patient_can_view_own_consultation(self, authenticated_patient, appointment):
        """Verify patient can view their consultation"""
        url = f'/api/consultations/{appointment.id}/'
        
        response = authenticated_patient.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'chief_complaint' in response.data
    
    def test_doctor_can_view_own_consultation(self, authenticated_doctor, appointment):
        """Verify doctor can view their consultation"""
        url = f'/api/consultations/{appointment.id}/'
        
        response = authenticated_doctor.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_consultation_auto_created(self, authenticated_patient, appointment):
        """Verify consultation is auto-created if doesn't exist"""
        # Ensure no consultation exists
        Consultation.objects.filter(appointment=appointment).delete()
        
        url = f'/api/consultations/{appointment.id}/'
        response = authenticated_patient.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert Consultation.objects.filter(appointment=appointment).exists()
    
    def test_unauthenticated_rejected(self, api_client, appointment):
        """Verify unauthenticated request is rejected"""
        url = f'/api/consultations/{appointment.id}/'
        
        response = api_client.get(url)
        
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


# ============================================
# API TESTS - CONSULTATION UPDATE
# ============================================

@pytest.mark.django_db
class TestConsultationUpdateAPI:
    """Test consultation update endpoint"""
    
    def test_doctor_can_update_consultation(self, authenticated_doctor, appointment):
        """Verify doctor can update consultation notes"""
        url = f'/api/consultations/{appointment.id}/update/'
        
        response = authenticated_doctor.patch(url, {
            'chief_complaint': 'Severe headache',
            'diagnosis': 'Migraine',
            'treatment_plan': 'Pain medication and rest'
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'consultation' in response.data
    
    def test_patient_cannot_update_consultation(self, authenticated_patient, appointment):
        """Verify patient cannot update consultation"""
        url = f'/api/consultations/{appointment.id}/update/'
        
        response = authenticated_patient.patch(url, {
            'diagnosis': 'Self-diagnosis'
        }, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_update_followup_fields(self, authenticated_doctor, appointment):
        """Verify followup fields can be updated"""
        url = f'/api/consultations/{appointment.id}/update/'
        
        followup_date = (date.today() + timedelta(days=14)).isoformat()
        
        response = authenticated_doctor.patch(url, {
            'followup_needed': True,
            'followup_date': followup_date,
            'followup_notes': 'Check blood pressure'
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK


# ============================================
# API TESTS - MY CONSULTATIONS
# ============================================

@pytest.mark.django_db
class TestMyConsultationsAPI:
    """Test my consultations list endpoint"""
    
    url = '/api/consultations/'
    
    def test_patient_sees_own_consultations(self, authenticated_patient, appointment):
        """Verify patient sees their consultations"""
        Consultation.objects.create(appointment=appointment)
        
        response = authenticated_patient.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_doctor_sees_own_consultations(self, authenticated_doctor, appointment):
        """Verify doctor sees their consultations"""
        Consultation.objects.create(appointment=appointment)
        
        response = authenticated_doctor.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_unauthenticated_rejected(self, api_client):
        """Verify unauthenticated request is rejected"""
        response = api_client.get(self.url)
        
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


# ============================================
# API TESTS - START CONSULTATION
# ============================================

@pytest.mark.django_db
class TestStartConsultationAPI:
    """Test start consultation endpoint"""
    
    def test_doctor_can_start_consultation(self, authenticated_doctor, appointment):
        """Verify doctor can start consultation"""
        url = f'/api/consultations/{appointment.id}/start/'
        
        response = authenticated_doctor.post(url, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'started_at' in response.data
        
        # Verify appointment status updated
        appointment.refresh_from_db()
        assert appointment.status == 'in_progress'
    
    def test_patient_cannot_start_consultation(self, authenticated_patient, appointment):
        """Verify patient cannot start consultation"""
        url = f'/api/consultations/{appointment.id}/start/'
        
        response = authenticated_patient.post(url, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_cannot_start_already_started(self, authenticated_doctor, appointment):
        """Verify already started consultation returns error"""
        # Create consultation with start time
        Consultation.objects.create(
            appointment=appointment,
            started_at=timezone.now()
        )
        
        url = f'/api/consultations/{appointment.id}/start/'
        response = authenticated_doctor.post(url, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already started' in response.data.get('error', '').lower()


# ============================================
# API TESTS - END CONSULTATION
# ============================================

@pytest.mark.django_db
class TestEndConsultationAPI:
    """Test end consultation endpoint"""
    
    def test_doctor_can_end_consultation(self, authenticated_doctor, appointment):
        """Verify doctor can end consultation"""
        # Start consultation first
        Consultation.objects.create(
            appointment=appointment,
            started_at=timezone.now()
        )
        
        url = f'/api/consultations/{appointment.id}/end/'
        
        with patch('consultations.views.EmailService') as mock_email:
            mock_email.send_consultation_completed = MagicMock()
            response = authenticated_doctor.post(url, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'ended_at' in response.data
        assert 'duration_minutes' in response.data
        
        # Verify appointment status updated
        appointment.refresh_from_db()
        assert appointment.status == 'completed'
    
    def test_patient_cannot_end_consultation(self, authenticated_patient, appointment):
        """Verify patient cannot end consultation"""
        url = f'/api/consultations/{appointment.id}/end/'
        
        response = authenticated_patient.post(url, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_cannot_end_already_ended(self, authenticated_doctor, appointment):
        """Verify already ended consultation returns error"""
        Consultation.objects.create(
            appointment=appointment,
            started_at=timezone.now() - timedelta(minutes=30),
            ended_at=timezone.now()
        )
        
        url = f'/api/consultations/{appointment.id}/end/'
        response = authenticated_doctor.post(url, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already ended' in response.data.get('error', '').lower()


# ============================================
# API TESTS - CREATE PRESCRIPTION
# ============================================

@pytest.mark.django_db
class TestCreatePrescriptionAPI:
    """Test prescription creation endpoint"""
    
    def test_doctor_can_create_prescription(self, authenticated_doctor, appointment):
        """Verify doctor can create prescription"""
        url = f'/api/consultations/{appointment.id}/prescription/'
        
        data = {
            'diagnosis': 'Common cold',
            'notes': 'Rest and hydration',
            'valid_days': 30,
            'items': [
                {
                    'medicine_name': 'Paracetamol',
                    'dosage': '500mg',
                    'frequency': 'three_times_daily',
                    'duration': '5_days',
                    'quantity': '15 tablets',
                    'instructions': 'Take after meals'
                },
                {
                    'medicine_name': 'Vitamin C',
                    'dosage': '1000mg',
                    'frequency': 'once_daily',
                    'duration': '7_days'
                }
            ]
        }
        
        with patch('consultations.views.EmailService') as mock_email:
            mock_email.send_prescription_ready = MagicMock()
            response = authenticated_doctor.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'prescription' in response.data
        assert response.data['prescription']['prescription_number'].startswith('RX-')
    
    def test_patient_cannot_create_prescription(self, authenticated_patient, appointment):
        """Verify patient cannot create prescription"""
        url = f'/api/consultations/{appointment.id}/prescription/'
        
        data = {
            'items': [
                {'medicine_name': 'Test', 'dosage': '10mg', 'frequency': 'once_daily', 'duration': '7_days'}
            ]
        }
        
        response = authenticated_patient.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_empty_items_rejected(self, authenticated_doctor, appointment):
        """Verify empty prescription items are rejected"""
        url = f'/api/consultations/{appointment.id}/prescription/'
        
        data = {
            'diagnosis': 'Test',
            'items': []
        }
        
        response = authenticated_doctor.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================
# API TESTS - PRESCRIPTION LIST
# ============================================

@pytest.mark.django_db
class TestPrescriptionListAPI:
    """Test prescription list endpoint"""
    
    url = '/api/consultations/prescriptions/'
    
    def test_patient_sees_own_prescriptions(self, authenticated_patient, appointment):
        """Verify patient sees their prescriptions"""
        consultation = Consultation.objects.create(appointment=appointment)
        Prescription.objects.create(consultation=consultation)
        
        response = authenticated_patient.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_doctor_sees_own_prescriptions(self, authenticated_doctor, appointment):
        """Verify doctor sees prescriptions they created"""
        consultation = Consultation.objects.create(appointment=appointment)
        Prescription.objects.create(consultation=consultation)
        
        response = authenticated_doctor.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_unauthenticated_rejected(self, api_client):
        """Verify unauthenticated request is rejected"""
        response = api_client.get(self.url)
        
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


# ============================================
# API TESTS - PRESCRIPTION DETAIL
# ============================================

@pytest.mark.django_db
class TestPrescriptionDetailAPI:
    """Test prescription detail endpoint"""
    
    def test_patient_can_view_own_prescription(self, authenticated_patient, appointment):
        """Verify patient can view their prescription"""
        consultation = Consultation.objects.create(appointment=appointment)
        prescription = Prescription.objects.create(consultation=consultation)
        
        url = f'/api/consultations/prescriptions/{prescription.id}/'
        response = authenticated_patient.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'prescription_number' in response.data
        assert 'items' in response.data
    
    def test_doctor_can_view_prescription(self, authenticated_doctor, appointment):
        """Verify doctor can view prescription they created"""
        consultation = Consultation.objects.create(appointment=appointment)
        prescription = Prescription.objects.create(consultation=consultation)
        
        url = f'/api/consultations/prescriptions/{prescription.id}/'
        response = authenticated_doctor.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_cannot_view_others_prescription(self, authenticated_patient, specialization, doctor_profile):
        """Verify patient cannot view another's prescription"""
        # Create another patient
        other_patient = User.objects.create_user(
            email='other.patient@test.com',
            password='pass123',
            first_name='Other',
            last_name='Patient',
            user_type='patient'
        )
        
        # Create appointment for other patient
        other_appointment = Appointment.objects.create(
            patient=other_patient,
            doctor=doctor_profile,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='completed'
        )
        
        consultation = Consultation.objects.create(appointment=other_appointment)
        prescription = Prescription.objects.create(consultation=consultation)
        
        url = f'/api/consultations/prescriptions/{prescription.id}/'
        response = authenticated_patient.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND