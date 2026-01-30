import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from doctors.models import Specialization

data = [
    ('General Practice', 'Primary care'),
    ('Cardiology', 'Heart specialist'),
    ('Dermatology', 'Skin specialist'),
    ('Pediatrics', 'Child specialist'),
    ('Psychiatry', 'Mental health'),
    ('Orthopedics', 'Bone specialist'),
    ('Gynecology', 'Women health'),
    ('Ophthalmology', 'Eye specialist'),
    ('ENT', 'Ear Nose Throat'),
    ('Neurology', 'Brain specialist'),
]

for name, desc in data:
    Specialization.objects.get_or_create(name=name, defaults={'description': desc})
    print(f"Created: {name}")

print("Done!")