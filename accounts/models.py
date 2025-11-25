from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    pass


class UserProfile(models.Model):
    usern = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='user_profile')
    bio = models.TextField(null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return self.username
    
class UserProfile(models.Model):
    usern = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='user_profile')
    bio = models.TextField(null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)    

