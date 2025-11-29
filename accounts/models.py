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
    """Represent the 5 experiments."""
    EXP_CHOICES = [
        ('exp1', 'Exp#1 OAI Core'),
        ('exp2', 'Exp#2 OAI+gNB'),
        ('exp3', 'Exp#3 OAI+gNB+UE'),
        ('exp4', 'Exp#4 Open5GS'),
        ('exp5', 'Exp#5 Free5GC'),
    ]
    exp_key = models.CharField(max_length=10, unique=True, choices=EXP_CHOICES)
    name = models.CharField(max_length=100)
    description = models.TextField()
    url = models.URLField()  # e.g., http://10.7.43.10:4040
    
    def __str__(self):
        return self.name


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