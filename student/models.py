from django.db import models
from head.models import createUser, uploadQuestion

# Stores each student's answers

class UserAnswer(models.Model):
    user = models.ForeignKey(createUser, on_delete=models.CASCADE)
    question = models.ForeignKey(uploadQuestion, on_delete=models.CASCADE)
    answer_text = models.TextField()
    marks = models.IntegerField(default=0)

# Stores AI interview Q&A
class InterviewSession(models.Model):
    user = models.ForeignKey(createUser, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

# Final result summary of AI interview
class InterviewResult(models.Model):
    user = models.OneToOneField(createUser, on_delete=models.CASCADE)
    result_summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

# ✅ New model to store total marks given by head (if not already present)
class StudentMarks(models.Model):
    user = models.OneToOneField(createUser, on_delete=models.CASCADE)
    marks = models.IntegerField()
    grade = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(default='2026-01-01 00:00:00')
