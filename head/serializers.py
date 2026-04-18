import re

from rest_framework import serializers
from .models import createUser, uploadQuestion

class CreateUserSerializer(serializers.ModelSerializer):
    def validate_userName(self, value):
        cleaned_value = value.strip()
        if not re.fullmatch(r"[A-Za-z ]+", cleaned_value):
            raise serializers.ValidationError("Student name must contain only alphabets.")
        return cleaned_value

    def validate_userId(self, value):
        if not re.fullmatch(r"\d+", str(value)):
            raise serializers.ValidationError("Student ID must contain only numbers.")
        return value

    class Meta:
        model = createUser
        fields = ['userName', 'userId', 'userPassword']

class UploadQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = uploadQuestion
        fields = ['question', 'marks']
