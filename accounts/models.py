from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    email = models.EmailField(unique=True)
    bio = models.TextField(max_length=500, blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True)
    
    def __str__(self):
        return self.username


class Experiment(models.Model):
    """Represent experiments (both system and custom)."""
    exp_key = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    url = models.URLField()  # Base URL without port, e.g., http://10.7.43.10
    port = models.IntegerField(default=4040)  # Port number
    is_custom = models.BooleanField(default=False)  # True for user-created experiments
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_experiments')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['id']  # Show in order of creation
    
    def __str__(self):
        return self.name
    
    @property
    def full_url(self):
        """Return complete URL with port."""
        return self.url


class SessionBooking(models.Model):
    """Track user bookings for experiment sessions."""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name='bookings')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['start_time']
        unique_together = ['experiment', 'start_time']  # Prevent double-booking same slot
    
    def __str__(self):
        return f"{self.user.username} - {self.experiment.name} ({self.start_time})"
    
    def is_active(self):
        now = timezone.now()
        return self.start_time <= now < self.end_time and self.status == 'active'
    
    def minutes_remaining(self):
        """Return minutes remaining for active booking."""
        if self.is_active():
            delta = self.end_time - timezone.now()
            return max(0, int(delta.total_seconds() / 60))
        return 0

    @property
    def duration(self):
        """Return total duration of booking in minutes."""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)