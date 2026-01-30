from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from accounts.models import DoctorProfile
from doctors.models import Specialization, TimeSlot
from appointments.models import Appointment
from consultations.models import Consultation, Prescription

User = get_user_model()


class Command(BaseCommand):
    help = 'Show platform statistics'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('MEDICONNECT STATISTICS')
        self.stdout.write('=' * 50 + '\n')
        
        # Users
        total_users = User.objects.count()
        patients = User.objects.filter(user_type='patient').count()
        doctors = User.objects.filter(user_type='doctor').count()
        verified_doctors = DoctorProfile.objects.filter(verification_status='verified').count()
        
        self.stdout.write(self.style.HTTP_INFO('USERS:'))
        self.stdout.write(f'  Total Users: {total_users}')
        self.stdout.write(f'  Patients: {patients}')
        self.stdout.write(f'  Doctors: {doctors}')
        self.stdout.write(f'  Verified Doctors: {verified_doctors}')
        
        # Specializations
        specializations = Specialization.objects.count()
        self.stdout.write(f'\n  Specializations: {specializations}')
        
        # Appointments
        total_appointments = Appointment.objects.count()
        pending = Appointment.objects.filter(status='pending').count()
        confirmed = Appointment.objects.filter(status='confirmed').count()
        completed = Appointment.objects.filter(status='completed').count()
        cancelled = Appointment.objects.filter(status='cancelled').count()
        
        self.stdout.write(self.style.HTTP_INFO('\nAPPOINTMENTS:'))
        self.stdout.write(f'  Total: {total_appointments}')
        self.stdout.write(f'  Pending: {pending}')
        self.stdout.write(f'  Confirmed: {confirmed}')
        self.stdout.write(f'  Completed: {completed}')
        self.stdout.write(f'  Cancelled: {cancelled}')
        
        # Time Slots
        total_slots = TimeSlot.objects.count()
        available_slots = TimeSlot.objects.filter(status='available').count()
        booked_slots = TimeSlot.objects.filter(status='booked').count()
        
        self.stdout.write(self.style.HTTP_INFO('\nTIME SLOTS:'))
        self.stdout.write(f'  Total: {total_slots}')
        self.stdout.write(f'  Available: {available_slots}')
        self.stdout.write(f'  Booked: {booked_slots}')
        
        # Consultations & Prescriptions
        consultations = Consultation.objects.count()
        prescriptions = Prescription.objects.count()
        
        self.stdout.write(self.style.HTTP_INFO('\nCONSULTATIONS:'))
        self.stdout.write(f'  Total Consultations: {consultations}')
        self.stdout.write(f'  Total Prescriptions: {prescriptions}')
        
        # Today's Stats
        today = timezone.now().date()
        today_appointments = Appointment.objects.filter(date=today).count()
        
        self.stdout.write(self.style.HTTP_INFO('\nTODAY:'))
        self.stdout.write(f'  Appointments: {today_appointments}')
        
        self.stdout.write('\n' + '=' * 50 + '\n')