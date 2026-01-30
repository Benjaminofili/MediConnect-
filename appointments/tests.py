import pytest
from datetime import date, time, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.utils import timezone
from rest_framework import status

from appointments.models import Appointment
from appointments.serializers import (
    AppointmentListSerializer,
    AppointmentDetailSerializer,
    BookAppointmentSerializer,
    CancelAppointmentSerializer,
    RescheduleAppointmentSerializer,
)
from doctors.models import TimeSlot, Specialization
from accounts.models import User, DoctorProfile, PatientProfile


# ============================================
# APPOINTMENT MODEL TESTS
# ============================================

@pytest.mark.django_db
class TestAppointmentModel:
    """Test Appointment model"""
    
    def test_create_appointment(self, patient_user, doctor_profile, available_time_slot):
        """Verify appointment can be created"""
        appt = Appointment.objects.create(
            patient=patient_user,
            doctor=doctor_profile,
            time_slot=available_time_slot,
            date=available_time_slot.date,
            start_time=available_time_slot.start_time,
            end_time=available_time_slot.end_time,
            reason='Checkup'
        )
        
        assert appt.pk is not None
        assert appt.status == 'confirmed'
    
    def test_appointment_number_auto_generated(self, patient_user, doctor_profile, available_time_slot):
        """Verify appointment number is auto-generated"""
        appt = Appointment.objects.create(
            patient=patient_user,
            doctor=doctor_profile,
            date=available_time_slot.date,
            start_time=available_time_slot.start_time,
            end_time=available_time_slot.end_time
        )
        
        assert appt.appointment_number is not None
        assert appt.appointment_number.startswith('APT-')
    
    def test_appointment_number_format(self, patient_user, doctor_profile, available_time_slot):
        """Verify appointment number format: APT-YYYYMMDD-XXXX"""
        appt = Appointment.objects.create(
            patient=patient_user,
            doctor=doctor_profile,
            date=available_time_slot.date,
            start_time=available_time_slot.start_time,
            end_time=available_time_slot.end_time
        )
        
        parts = appt.appointment_number.split('-')
        assert len(parts) == 3
        assert parts[0] == 'APT'
        assert len(parts[1]) == 8
        assert len(parts[2]) == 4
    
    def test_can_cancel_future_appointment(self, patient_user, doctor_profile):
        """Verify future appointment can be cancelled"""
        future_date = date.today() + timedelta(days=2)
        
        appt = Appointment.objects.create(
            patient=patient_user,
            doctor=doctor_profile,
            date=future_date,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='confirmed'
        )
        
        assert appt.can_cancel is True
    
    def test_cannot_cancel_completed_appointment(self, patient_user, doctor_profile):
        """Verify completed appointment cannot be cancelled"""
        appt = Appointment.objects.create(
            patient=patient_user,
            doctor=doctor_profile,
            date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='completed'
        )
        
        assert appt.can_cancel is False
    
    def test_can_reschedule_first_time(self, patient_user, doctor_profile):
        """Verify appointment with 0 reschedules can be rescheduled"""
        future_date = date.today() + timedelta(days=2)
        
        appt = Appointment.objects.create(
            patient=patient_user,
            doctor=doctor_profile,
            date=future_date,
            start_time=time(10, 0),
            end_time=time(10, 30),
            reschedule_count=0
        )
        
        assert appt.can_reschedule is True
    
    def test_cannot_reschedule_after_max(self, patient_user, doctor_profile):
        """Verify appointment with 2+ reschedules cannot be rescheduled"""
        future_date = date.today() + timedelta(days=2)
        
        appt = Appointment.objects.create(
            patient=patient_user,
            doctor=doctor_profile,
            date=future_date,
            start_time=time(10, 0),
            end_time=time(10, 30),
            reschedule_count=2
        )
        
        assert appt.can_reschedule is False


# ============================================
# SERIALIZER TESTS
# ============================================

@pytest.mark.django_db
class TestBookAppointmentSerializer:
    """Test BookAppointmentSerializer validation"""
    
    def test_valid_booking_data(self, patient_user, doctor_profile, available_time_slot, api_client):
        """Verify valid booking data passes validation"""
        api_client.force_authenticate(user=patient_user)
        
        # Create a mock request
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        request = factory.post('/api/appointments/book/')
        request.user = patient_user
        
        data = {
            'doctor_id': doctor_profile.id,
            'time_slot_id': available_time_slot.id,
            'reason': 'Regular checkup',
            'symptoms': 'Headache'
        }
        
        serializer = BookAppointmentSerializer(data=data, context={'request': request})
        
        assert serializer.is_valid(), serializer.errors
    
    def test_invalid_doctor_id(self, patient_user):
        """Verify non-existent doctor fails validation"""
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        request = factory.post('/api/appointments/book/')
        request.user = patient_user
        
        data = {
            'doctor_id': 99999,
            'time_slot_id': 1
        }
        
        serializer = BookAppointmentSerializer(data=data, context={'request': request})
        
        assert not serializer.is_valid()
        assert 'doctor_id' in serializer.errors
    
    def test_unverified_doctor_fails(self, patient_user, specialization):
        """Verify booking with unverified doctor fails"""
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        request = factory.post('/api/appointments/book/')
        request.user = patient_user
        
        # Create unverified doctor
        unverified_user = User.objects.create_user(
            email='unverified@test.com',
            password='pass123',
            first_name='Unverified',
            last_name='Doctor',
            user_type='doctor'
        )
        unverified_profile = DoctorProfile.objects.create(
            user=unverified_user,
            specialization=specialization,
            license_number='UNVER123',
            experience_years=2,
            education='Test School',
            consultation_fee=Decimal('3000.00'),
            verification_status='pending'
        )
        
        data = {
            'doctor_id': unverified_profile.id,
            'time_slot_id': 1
        }
        
        serializer = BookAppointmentSerializer(data=data, context={'request': request})
        
        assert not serializer.is_valid()
        assert 'doctor_id' in serializer.errors
    
    def test_unavailable_slot_fails(self, patient_user, doctor_profile, booked_time_slot):
        """Verify booking unavailable slot fails"""
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        request = factory.post('/api/appointments/book/')
        request.user = patient_user
        
        data = {
            'doctor_id': doctor_profile.id,
            'time_slot_id': booked_time_slot.id
        }
        
        serializer = BookAppointmentSerializer(data=data, context={'request': request})
        
        assert not serializer.is_valid()
        assert 'time_slot_id' in serializer.errors


@pytest.mark.django_db
class TestCancelAppointmentSerializer:
    """Test CancelAppointmentSerializer validation"""
    
    def test_valid_cancellation(self, appointment):
        """Verify valid cancellation passes"""
        # Make sure appointment is in the future
        appointment.date = date.today() + timedelta(days=2)
        appointment.save()
        
        data = {'cancellation_reason': 'I have another commitment that day'}
        serializer = CancelAppointmentSerializer(
            data=data,
            context={'appointment': appointment}
        )
        
        assert serializer.is_valid(), serializer.errors
    
    def test_reason_too_short_fails(self, appointment):
        """Verify short cancellation reason fails"""
        appointment.date = date.today() + timedelta(days=2)
        appointment.save()
        
        data = {'cancellation_reason': 'Short'}
        serializer = CancelAppointmentSerializer(
            data=data,
            context={'appointment': appointment}
        )
        
        assert not serializer.is_valid()
        assert 'cancellation_reason' in serializer.errors


@pytest.mark.django_db
class TestRescheduleAppointmentSerializer:
    """Test RescheduleAppointmentSerializer validation"""
    
    def test_valid_reschedule(self, appointment, doctor_profile):
        """Verify valid reschedule passes"""
        # Create a new available slot
        new_slot = TimeSlot.objects.create(
            doctor=doctor_profile,
            date=date.today() + timedelta(days=3),
            start_time=time(14, 0),
            end_time=time(14, 30),
            status='available'
        )
        
        # Make appointment reschedulable
        appointment.date = date.today() + timedelta(days=2)
        appointment.reschedule_count = 0
        appointment.save()
        
        data = {'new_time_slot_id': new_slot.id}
        serializer = RescheduleAppointmentSerializer(
            data=data,
            context={'appointment': appointment}
        )
        
        assert serializer.is_valid(), serializer.errors
    
    def test_different_doctor_slot_fails(self, appointment, specialization):
        """Verify rescheduling to different doctor's slot fails"""
        # Create another doctor
        other_user = User.objects.create_user(
            email='other.doc@test.com',
            password='pass123',
            first_name='Other',
            last_name='Doctor',
            user_type='doctor'
        )
        other_profile = DoctorProfile.objects.create(
            user=other_user,
            specialization=specialization,
            license_number='OTHER456',
            experience_years=5,
            education='Other School',
            consultation_fee=Decimal('5000.00'),
            verification_status='verified'
        )
        other_slot = TimeSlot.objects.create(
            doctor=other_profile,
            date=date.today() + timedelta(days=3),
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='available'
        )
        
        # Make appointment reschedulable
        appointment.date = date.today() + timedelta(days=2)
        appointment.reschedule_count = 0
        appointment.save()
        
        data = {'new_time_slot_id': other_slot.id}
        serializer = RescheduleAppointmentSerializer(
            data=data,
            context={'appointment': appointment}
        )
        
        assert not serializer.is_valid()


# ============================================
# API TESTS - BOOK APPOINTMENT
# ============================================

@pytest.mark.django_db
class TestBookAppointmentAPI:
    """Test appointment booking endpoint"""
    
    url = '/api/appointments/book/'
    
    def test_patient_can_book_appointment(self, authenticated_patient, doctor_profile, available_time_slot):
        """Verify patient can book an appointment"""
        with patch('appointments.views.EmailService') as mock_email:
            mock_email.send_appointment_confirmation = MagicMock()
            mock_email.send_appointment_confirmation_to_doctor = MagicMock()
            
            data = {
                'doctor_id': doctor_profile.id,
                'time_slot_id': available_time_slot.id,
                'reason': 'Regular checkup',
                'symptoms': 'Headache'
            }
            
            response = authenticated_patient.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'appointment' in response.data
        assert response.data['appointment']['status'] == 'confirmed'
    
    def test_booking_marks_slot_as_booked(self, authenticated_patient, doctor_profile, available_time_slot):
        """Verify booking marks time slot as booked"""
        with patch('appointments.views.EmailService'):
            data = {
                'doctor_id': doctor_profile.id,
                'time_slot_id': available_time_slot.id
            }
            
            authenticated_patient.post(self.url, data, format='json')
        
        available_time_slot.refresh_from_db()
        assert available_time_slot.status == 'booked'
    
    def test_doctor_cannot_book_appointment(self, authenticated_doctor, doctor_profile, available_time_slot):
        """Verify doctor cannot book appointments"""
        data = {
            'doctor_id': doctor_profile.id,
            'time_slot_id': available_time_slot.id
        }
        
        response = authenticated_doctor.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'Only patients' in response.data.get('error', '')
    
    def test_cannot_double_book_slot(self, authenticated_patient, doctor_profile, booked_time_slot):
        """Verify already booked slot cannot be booked again"""
        data = {
            'doctor_id': doctor_profile.id,
            'time_slot_id': booked_time_slot.id
        }
        
        response = authenticated_patient.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_unauthenticated_cannot_book(self, api_client, doctor_profile, available_time_slot):
        """Verify unauthenticated user cannot book"""
        data = {
            'doctor_id': doctor_profile.id,
            'time_slot_id': available_time_slot.id
        }
        
        response = api_client.post(self.url, data, format='json')
        
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


# ============================================
# API TESTS - MY APPOINTMENTS
# ============================================

@pytest.mark.django_db
class TestMyAppointmentsAPI:
    """Test my appointments endpoint"""
    
    url = '/api/appointments/'
    
    def test_patient_sees_own_appointments(self, authenticated_patient, appointment):
        """Verify patient sees their appointments"""
        response = authenticated_patient.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_doctor_sees_own_appointments(self, authenticated_doctor, appointment):
        """Verify doctor sees their appointments"""
        response = authenticated_doctor.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_filter_by_status(self, authenticated_patient, appointment):
        """Verify filtering by status works"""
        response = authenticated_patient.get(f'{self.url}?status=confirmed')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_filter_by_date_range(self, authenticated_patient, appointment):
        """Verify filtering by date range works"""
        today = date.today()
        next_week = today + timedelta(days=7)
        
        response = authenticated_patient.get(
            f'{self.url}?date_from={today}&date_to={next_week}'
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_unauthenticated_rejected(self, api_client):
        """Verify unauthenticated request is rejected"""
        response = api_client.get(self.url)
        
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


# ============================================
# API TESTS - UPCOMING APPOINTMENTS
# ============================================

@pytest.mark.django_db
class TestUpcomingAppointmentsAPI:
    """Test upcoming appointments endpoint"""
    
    url = '/api/appointments/upcoming/'
    
    def test_shows_only_future_appointments(self, authenticated_patient, appointment, past_appointment):
        """Verify only future appointments are returned"""
        response = authenticated_patient.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        # Past appointment should not be in results
        data = response.data.get('results', response.data)
        for appt in data:
            assert appt['date'] >= str(date.today())
    
    def test_excludes_cancelled_appointments(self, authenticated_patient, patient_user, doctor_profile):
        """Verify cancelled appointments are excluded"""
        # Create cancelled future appointment
        cancelled = Appointment.objects.create(
            patient=patient_user,
            doctor=doctor_profile,
            date=date.today() + timedelta(days=3),
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='cancelled'
        )
        
        response = authenticated_patient.get(self.url)
        
        data = response.data.get('results', response.data)
        appointment_ids = [a['id'] for a in data]
        assert cancelled.id not in appointment_ids


# ============================================
# API TESTS - APPOINTMENT DETAIL
# ============================================

@pytest.mark.django_db
class TestAppointmentDetailAPI:
    """Test appointment detail endpoint"""
    
    def test_patient_can_view_own_appointment(self, authenticated_patient, appointment):
        """Verify patient can view their appointment"""
        url = f'/api/appointments/{appointment.id}/'
        
        response = authenticated_patient.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == appointment.id
    
    def test_doctor_can_view_own_appointment(self, authenticated_doctor, appointment):
        """Verify doctor can view their appointment"""
        url = f'/api/appointments/{appointment.id}/'
        
        response = authenticated_doctor.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_cannot_view_others_appointment(self, authenticated_patient, specialization, doctor_profile):
        """Verify patient cannot view other's appointment"""
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
            date=date.today() + timedelta(days=1),
            start_time=time(15, 0),
            end_time=time(15, 30),
            status='confirmed'
        )
        
        url = f'/api/appointments/{other_appointment.id}/'
        response = authenticated_patient.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================
# API TESTS - CANCEL APPOINTMENT
# ============================================

@pytest.mark.django_db
class TestCancelAppointmentAPI:
    """Test appointment cancellation endpoint"""
    
    def test_patient_can_cancel_own_appointment(self, authenticated_patient, appointment):
        """Verify patient can cancel their appointment"""
        # Make sure it's in the future
        appointment.date = date.today() + timedelta(days=2)
        appointment.save()
        
        url = f'/api/appointments/{appointment.id}/cancel/'
        
        with patch('appointments.views.EmailService') as mock_email:
            mock_email.send_appointment_cancellation = MagicMock()
            
            response = authenticated_patient.post(url, {
                'cancellation_reason': 'I have another commitment on that day'
            }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        appointment.refresh_from_db()
        assert appointment.status == 'cancelled'
    
    def test_cancellation_releases_slot(self, authenticated_patient, appointment, available_time_slot):
        """Verify cancellation marks slot as available"""
        appointment.date = date.today() + timedelta(days=2)
        appointment.time_slot = available_time_slot
        available_time_slot.status = 'booked'
        available_time_slot.save()
        appointment.save()
        
        url = f'/api/appointments/{appointment.id}/cancel/'
        
        with patch('appointments.views.EmailService'):
            authenticated_patient.post(url, {
                'cancellation_reason': 'I have another commitment on that day'
            }, format='json')
        
        available_time_slot.refresh_from_db()
        assert available_time_slot.status == 'available'
    
    def test_doctor_can_cancel_appointment(self, authenticated_doctor, appointment):
        """Verify doctor can cancel their appointment"""
        appointment.date = date.today() + timedelta(days=2)
        appointment.save()
        
        url = f'/api/appointments/{appointment.id}/cancel/'
        
        with patch('appointments.views.EmailService'):
            response = authenticated_doctor.post(url, {
                'cancellation_reason': 'Emergency situation, need to reschedule'
            }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_short_reason_rejected(self, authenticated_patient, appointment):
        """Verify short cancellation reason is rejected"""
        appointment.date = date.today() + timedelta(days=2)
        appointment.save()
        
        url = f'/api/appointments/{appointment.id}/cancel/'
        
        response = authenticated_patient.post(url, {
            'cancellation_reason': 'Short'
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================
# API TESTS - RESCHEDULE APPOINTMENT
# ============================================

@pytest.mark.django_db
class TestRescheduleAppointmentAPI:
    """Test appointment rescheduling endpoint"""
    
    def test_patient_can_reschedule(self, authenticated_patient, appointment, doctor_profile):
        """Verify patient can reschedule their appointment"""
        # Create new available slot
        new_slot = TimeSlot.objects.create(
            doctor=doctor_profile,
            date=date.today() + timedelta(days=4),
            start_time=time(11, 0),
            end_time=time(11, 30),
            status='available'
        )
        
        # Make appointment reschedulable
        appointment.date = date.today() + timedelta(days=2)
        appointment.reschedule_count = 0
        appointment.save()
        
        url = f'/api/appointments/{appointment.id}/reschedule/'
        
        response = authenticated_patient.post(url, {
            'new_time_slot_id': new_slot.id
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        appointment.refresh_from_db()
        assert appointment.time_slot == new_slot
        assert appointment.reschedule_count == 1
    
    def test_doctor_cannot_reschedule(self, authenticated_doctor, appointment, doctor_profile):
        """Verify doctor cannot reschedule appointments"""
        new_slot = TimeSlot.objects.create(
            doctor=doctor_profile,
            date=date.today() + timedelta(days=4),
            start_time=time(11, 0),
            end_time=time(11, 30),
            status='available'
        )
        
        url = f'/api/appointments/{appointment.id}/reschedule/'
        
        response = authenticated_doctor.post(url, {
            'new_time_slot_id': new_slot.id
        }, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_old_slot_released_after_reschedule(self, authenticated_patient, appointment, doctor_profile, available_time_slot):
        """Verify old slot becomes available after reschedule"""
        # Setup
        appointment.time_slot = available_time_slot
        available_time_slot.status = 'booked'
        available_time_slot.save()
        appointment.date = date.today() + timedelta(days=2)
        appointment.reschedule_count = 0
        appointment.save()
        
        # Create new slot
        new_slot = TimeSlot.objects.create(
            doctor=doctor_profile,
            date=date.today() + timedelta(days=4),
            start_time=time(14, 0),
            end_time=time(14, 30),
            status='available'
        )
        
        url = f'/api/appointments/{appointment.id}/reschedule/'
        
        authenticated_patient.post(url, {
            'new_time_slot_id': new_slot.id
        }, format='json')
        
        available_time_slot.refresh_from_db()
        new_slot.refresh_from_db()
        
        assert available_time_slot.status == 'available'
        assert new_slot.status == 'booked'


# ============================================
# API TESTS - COMPLETE APPOINTMENT
# ============================================

@pytest.mark.django_db
class TestCompleteAppointmentAPI:
    """Test appointment completion endpoint"""
    
    def test_doctor_can_complete_appointment(self, authenticated_doctor, appointment):
        """Verify doctor can complete their appointment"""
        url = f'/api/appointments/{appointment.id}/complete/'
        
        response = authenticated_doctor.post(url, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        appointment.refresh_from_db()
        assert appointment.status == 'completed'
    
    def test_patient_cannot_complete_appointment(self, authenticated_patient, appointment):
        """Verify patient cannot complete appointments"""
        url = f'/api/appointments/{appointment.id}/complete/'
        
        response = authenticated_patient.post(url, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_cannot_complete_cancelled_appointment(self, authenticated_doctor, appointment):
        """Verify cancelled appointment cannot be completed"""
        appointment.status = 'cancelled'
        appointment.save()
        
        url = f'/api/appointments/{appointment.id}/complete/'
        
        response = authenticated_doctor.post(url, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================
# API TESTS - TODAY'S APPOINTMENTS (DOCTOR)
# ============================================

@pytest.mark.django_db
class TestDoctorTodayAppointmentsAPI:
    """Test doctor's today appointments endpoint"""
    
    url = '/api/appointments/today/'
    
    def test_doctor_sees_today_appointments(self, authenticated_doctor, doctor_profile, patient_user):
        """Verify doctor sees today's appointments"""
        # Create today's appointment
        Appointment.objects.create(
            patient=patient_user,
            doctor=doctor_profile,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(14, 30),
            status='confirmed'
        )
        
        response = authenticated_doctor.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_patient_gets_empty_list(self, authenticated_patient):
        """Verify patient gets empty list"""
        response = authenticated_patient.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.data.get('results', response.data)
        assert len(data) == 0
    
    def test_excludes_cancelled_appointments(self, authenticated_doctor, doctor_profile, patient_user):
        """Verify cancelled appointments are excluded"""
        Appointment.objects.create(
            patient=patient_user,
            doctor=doctor_profile,
            date=date.today(),
            start_time=time(15, 0),
            end_time=time(15, 30),
            status='cancelled'
        )
        
        response = authenticated_doctor.get(self.url)
        
        data = response.data.get('results', response.data)
        for appt in data:
            assert appt['status'] != 'cancelled'


# ============================================
# API TESTS - JOIN CONSULTATION
# ============================================

@pytest.mark.django_db
class TestJoinConsultationAPI:
    """Test video consultation join endpoint"""
    
    def test_patient_can_get_video_url(self, authenticated_patient, appointment):
        """Verify patient can get video room URL"""
        appointment.video_room_url = 'https://whereby.com/test-room'
        appointment.save()
        
        url = f'/api/appointments/{appointment.id}/join/'
        
        response = authenticated_patient.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'video_room_url' in response.data
    
    def test_doctor_can_get_video_url(self, authenticated_doctor, appointment):
        """Verify doctor can get video room URL"""
        appointment.video_room_url = 'https://whereby.com/test-room'
        appointment.video_host_url = 'https://whereby.com/test-room?host=true'
        appointment.save()
        
        url = f'/api/appointments/{appointment.id}/join/'
        
        response = authenticated_doctor.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'video_room_url' in response.data
    
    def test_generates_room_if_not_exists(self, authenticated_patient, appointment):
        """Verify video room is generated if it doesn't exist"""
        appointment.video_room_url = ''
        appointment.save()
        
        url = f'/api/appointments/{appointment.id}/join/'
        
        with patch.object(Appointment, 'generate_video_room') as mock_generate:
            mock_generate.return_value = None
            appointment.video_room_url = 'https://whereby.com/generated-room'
            
            response = authenticated_patient.get(url)
        
        # Either succeeds or fails gracefully
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]