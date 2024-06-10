from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)

class CommandLog(models.Model):
    username = models.CharField(max_length=20)
    command = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)