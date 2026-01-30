from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0003_alter_appointment_time_slot'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='video_host_url',
            field=models.URLField(blank=True),
        ),
    ]




