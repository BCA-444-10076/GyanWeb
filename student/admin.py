from django.contrib import admin
from .models import UserAnswer, InterviewSession, InterviewResult, StudentMarks

admin.site.register(UserAnswer)
admin.site.register(InterviewSession)
admin.site.register(InterviewResult)
admin.site.register(StudentMarks)
