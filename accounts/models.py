from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    full_name = models.CharField(max_length=150, null=True, blank=True)

    def __str__(self):
        return self.username
    
class UserProfile(models.Model):
    usern = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='user_profile')
    bio = models.TextField(null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)    