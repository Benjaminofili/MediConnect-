from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from doctors.models import TimeSlot


class Command(BaseCommand):
    help = 'Delete old time slots that have passed'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Delete slots older than this many days (default: 7)'
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now().date() - timedelta(days=days)
        
        # Only delete available slots (not booked ones)
        old_slots = TimeSlot.objects.filter(
            date__lt=cutoff_date,
            status='available'
        )
        
        count = old_slots.count()
        old_slots.delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Deleted {count} old available slots')
        )