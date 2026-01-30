from django.db import models

class Service(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(help_text="Short description for the card")
    # Using 'icon_image' for the small icon and 'cover_image' for the card background
    icon_image = models.FileField(upload_to='services/icons/', help_text="Upload SVG or PNG icon")
    cover_image = models.ImageField(upload_to='services/covers/', help_text="The background image for the card")
    order = models.IntegerField(default=0, help_text="Order to display on homepage")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

class Testimonial(models.Model):
    patient_name = models.CharField(max_length=100)
    designation = models.CharField(max_length=100, blank=True, help_text="e.g. 'Satisfied Patient' or 'Teacher'")
    photo = models.ImageField(upload_to='testimonials/', blank=True)
    text = models.TextField()
    rating = models.IntegerField(default=5, help_text="Star rating (1-5)")

    def __str__(self):
        return self.patient_name

class FAQ(models.Model):
    question = models.CharField(max_length=200)
    answer = models.TextField()
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.question