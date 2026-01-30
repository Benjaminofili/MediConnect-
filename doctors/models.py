from django.db import models


class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Availability(models.Model):
    DAYS_OF_WEEK = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'),
        (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]

    doctor = models.ForeignKey('accounts.DoctorProfile', on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['doctor', 'day_of_week', 'start_time']
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.doctor} - {self.get_day_of_week_display()}"


class TimeSlot(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('blocked', 'Blocked'),
    ]

    doctor = models.ForeignKey('accounts.DoctorProfile', on_delete=models.CASCADE, related_name='time_slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')

    class Meta:
        unique_together = ['doctor', 'date', 'start_time']
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.doctor} - {self.date} {self.start_time}"