from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from appointments.models import Appointment
from notifications.services import EmailService


class Command(BaseCommand):
    help = 'Send appointment reminders for tomorrow'

    def handle(self, *args, **options):
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        appointments = Appointment.objects.filter(
            date=tomorrow,
            status__in=['confirmed', 'pending']
        ).select_related('patient', 'doctor__user')
        
        count = 0
        for appointment in appointments:
            success = EmailService.send_appointment_reminder(appointment)
            if success:
                count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Reminder sent: {appointment.appointment_number}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Failed to send: {appointment.appointment_number}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nTotal reminders sent: {count}')
        )