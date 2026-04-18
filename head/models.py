from django.db import models

class createUser(models.Model):
    userName = models.CharField(max_length=20)
    userId = models.IntegerField(unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)  # Add email field
    userPassword = models.CharField(max_length=100)  # ✅ Allow any string password
    created_at = models.DateTimeField(auto_now_add=True)  # Add creation timestamp

class uploadQuestion(models.Model):
        question=models.CharField(max_length=500)
        marks=models.IntegerField(default=10)
        created_at = models.DateTimeField(auto_now_add=True)  # Add creation timestamp
        usage_count = models.IntegerField(default=0)  # Track how many times this question is used
