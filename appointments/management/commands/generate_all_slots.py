from django.core.management.base import BaseCommand
from doctors.services import generate_all_doctor_slots


class Command(BaseCommand):
    help = 'Generate time slots for all verified doctors'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days ahead to generate slots (default: 30)'
        )

    def handle(self, *args, **options):
        days = options['days']
        
        self.stdout.write(f'Generating slots for next {days} days...\n')
        
        total = generate_all_doctor_slots(days_ahead=days)
        
        self.stdout.write(
            self.style.SUCCESS(f'\nTotal slots generated: {total}')
        )