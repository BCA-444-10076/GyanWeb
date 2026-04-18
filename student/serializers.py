from rest_framework import serializers
from head.models import uploadQuestion

class StudentLoginSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    password = serializers.CharField()

# For submitting answers
class AnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    answer_text = serializers.CharField()
class QuestionViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = uploadQuestion
        fields = ['id', 'question'] 
