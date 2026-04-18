from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import createUser, uploadQuestion
from .serializers import CreateUserSerializer, UploadQuestionSerializer
from rest_framework.decorators import api_view
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from student.models import InterviewResult, StudentMarks
from head.models import createUser as HeadUser
from django.db.models import Count, Q, Avg
from django.http import JsonResponse, HttpResponse
import json
import csv
import re
from datetime import datetime

def create_user_page(request):
    return render(request, 'head/create_user.html')

def upload_question_page(request):
    return render(request, 'head/upload_question.html')

def view_answers_page(request):
    return render(request, 'head/view_answers.html')

def view_interview_page(request):
    return render(request, 'head/view_interview.html')

# For creating a user
class CreateUserView(APIView):
    def post(self, request):
        serializer = CreateUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# For uploading one or many questions
class UploadQuestionView(APIView):
    def post(self, request):
        # Allow single or multiple questions using `many=True` when needed
        is_many = isinstance(request.data, list)
        serializer = UploadQuestionSerializer(data=request.data, many=is_many)
        
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Question(s) uploaded successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_all_questions(request):
    questions = uploadQuestion.objects.all().values('id')  # only sending IDs
    return Response(list(questions))

# New view functions for side panel
def view_users_page(request):
    users = HeadUser.objects.all().order_by('-userId')
    total_users = users.count()
    return render(request, 'head/view_users.html', {
        'users': users,
        'total_users': total_users
    })

def view_questions_page(request):
    questions = uploadQuestion.objects.all().order_by('-id')
    total_questions = questions.count()
    return render(request, 'head/view_questions.html', {
        'questions': questions,
        'total_questions': total_questions
    })

def interview_results(request):
    from student.models import InterviewSession

    def format_duration(total_seconds):
        total_seconds = max(int(total_seconds or 0), 0)
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    results = InterviewResult.objects.select_related('user').order_by('-id')
    
    results_with_duration = []
    for result in results:
        sessions = list(
            InterviewSession.objects.filter(user=result.user)
            .order_by('timestamp')
            .values('question', 'answer', 'timestamp')
        )

        summary_duration_match = None
        if result.result_summary:
            summary_duration_match = re.search(r'\b(\d{2}:\d{2}(?::\d{2})?)\b', result.result_summary)

        if summary_duration_match:
            matched_duration = summary_duration_match.group(1)
            result.duration = matched_duration if matched_duration.count(':') == 2 else f"00:{matched_duration}"
        elif sessions:
            first_session_time = sessions[0]['timestamp']
            last_session_time = sessions[-1]['timestamp']
            result.duration = format_duration((last_session_time - first_session_time).total_seconds())
        else:
            result.duration = "00:00:00"

        if result.result_summary:
            result.display_summary = result.result_summary
        elif sessions:
            answered_sessions = [
                session for session in sessions
                if session['answer'] and session['answer'] != '[Question skipped]'
            ]
            skipped_count = sum(1 for session in sessions if session['answer'] == '[Question skipped]')
            result.display_summary = f"Answered {len(answered_sessions)}/{len(sessions)}, skipped {skipped_count}."
        else:
            result.display_summary = "No interview session data available."

        student_marks = StudentMarks.objects.filter(user=result.user).first()
        result.marks = student_marks.marks if student_marks else 'N/A'
        results_with_duration.append(result)
    
    # Calculate statistics
    excellent_count = results.filter(result_summary='Excellent').count()
    good_count = results.filter(result_summary='Good').count()
    fair_count = results.filter(result_summary='Fair').count()
    
    return render(request, 'head/interview_results.html', {
        'results': results_with_duration,
        'excellent_count': excellent_count,
        'good_count': good_count,
        'fair_count': fair_count
    })

def calculate_grade(marks, total_possible=100):
    """Calculate grade based on percentage"""
    if total_possible <= 0:
        return 'D'
    
    percentage = (marks / total_possible) * 100
    if percentage >= 90:
        return 'A+'
    elif percentage >= 85:
        return 'A'
    elif percentage >= 80:
        return 'B+'
    elif percentage >= 75:
        return 'B'
    elif percentage >= 70:
        return 'C+'
    elif percentage >= 60:
        return 'C'
    else:
        return 'D'

def results(request):
    # Generate comprehensive results data
    total_users = HeadUser.objects.count()
    total_questions = uploadQuestion.objects.count()
    completed_interviews = InterviewResult.objects.count()
    
    # Calculate performance percentages based on student grades
    student_marks = StudentMarks.objects.select_related('user').all()
    
    # Calculate grades first
    for student_mark in student_marks:
        if not student_mark.grade:
            # Calculate total possible marks for this student
            from student.models import UserAnswer
            user_answers = UserAnswer.objects.filter(user=student_mark.user).select_related('question')
            total_possible_marks = sum(answer.question.marks for answer in user_answers if answer.question)
            
            student_mark.grade = calculate_grade(student_mark.marks, total_possible_marks)
            student_mark.save()
    
    # Count performance based on grades
    excellent_count = StudentMarks.objects.filter(grade__in=['A+', 'A']).count()
    good_count = StudentMarks.objects.filter(grade__in=['B+', 'B']).count()
    fair_count = StudentMarks.objects.filter(grade__in=['C+', 'C', 'D']).count()
    total_results = excellent_count + good_count + fair_count
    
    # Calculate percentages
    excellent_percentage = (excellent_count / total_results * 100) if total_results > 0 else 0
    good_percentage = (good_count / total_results * 100) if total_results > 0 else 0
    fair_percentage = (fair_count / total_results * 100) if total_results > 0 else 0
    
    # Get top performers (now with grades)
    top_students = StudentMarks.objects.select_related('user').order_by('-marks')[:10]
    
    # Calculate average score
    average_score = StudentMarks.objects.aggregate(average_marks=Avg('marks'))['average_marks'] or 0
    
    return render(request, 'head/results.html', {
        'total_users': total_users,
        'total_questions': total_questions,
        'completed_interviews': completed_interviews,
        'excellent_count': excellent_count,
        'good_count': good_count,
        'fair_count': fair_count,
        'excellent_percentage': round(excellent_percentage, 1),
        'good_percentage': round(good_percentage, 1),
        'fair_percentage': round(fair_percentage, 1),
        'top_students': top_students,
        'average_score': round(average_score, 1)
    })

# API endpoints for question CRUD operations

@api_view(['PUT'])
def update_question(request, question_id):
    try:
        question = uploadQuestion.objects.get(id=question_id)
        serializer = UploadQuestionSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Question updated successfully'})
        return Response(serializer.errors, status=400)
    except uploadQuestion.DoesNotExist:
        return Response({'error': 'Question not found'}, status=404)

@api_view(['DELETE'])
def delete_question(request, question_id):
    try:
        question = uploadQuestion.objects.get(id=question_id)
        question.delete()
        return Response({'message': 'Question deleted successfully'})
    except uploadQuestion.DoesNotExist:
        return Response({'error': 'Question not found'}, status=404)

# Export results to CSV
@api_view(['GET'])
def export_results(request):
    try:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="results_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow(['Student Name', 'User ID', 'Marks', 'Grade', 'Interview Result', 'Date'])
        
        # Get student marks data
        student_marks = StudentMarks.objects.select_related('user').all()
        
        for mark in student_marks:
            # Calculate grade if not present
            if not mark.grade:
                # Calculate total possible marks for this student
                user_answers = UserAnswer.objects.filter(user=mark.user).select_related('question')
                total_possible_marks = sum(answer.question.marks for answer in user_answers if answer.question)
                
                mark.grade = calculate_grade(mark.marks, total_possible_marks)
                mark.save()
            
            # Get interview result if exists
            interview_result = InterviewResult.objects.filter(user=mark.user).first()
            result_summary = interview_result.result_summary if interview_result else 'N/A'
            
            writer.writerow([
                mark.user.userName,
                mark.user.userId,
                mark.marks,
                mark.grade or 'N/A',
                result_summary,
                mark.created_at.strftime('%Y-%m-%d') if mark.created_at else 'N/A'
            ])
        
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# Export users to CSV
@api_view(['GET'])
def export_users(request):
    try:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow(['User ID', 'User Name', 'Created Date'])
        
        # Get all users
        users = HeadUser.objects.all().order_by('-userId')
        
        for user in users:
            writer.writerow([
                user.userId,
                user.userName,
                user.created_at.strftime('%Y-%m-%d') if user.created_at else 'N/A'
            ])
        
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# Export questions to CSV
@api_view(['GET'])
def export_questions(request):
    try:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="questions_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow(['Question ID', 'Question Text', 'Marks', 'Created Date', 'Usage Count'])
        
        # Get all questions
        questions = uploadQuestion.objects.all().order_by('-id')
        
        for question in questions:
            writer.writerow([
                question.id,
                question.question,
                question.marks,
                question.created_at.strftime('%Y-%m-%d') if question.created_at else 'N/A',
                question.usage_count
            ])
        
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# Import questions from CSV
@api_view(['POST'])
def import_questions(request):
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No file provided'}, status=400)
        
        csv_file = request.FILES['file']
        
        if not csv_file.name.endswith('.csv'):
            return JsonResponse({'success': False, 'error': 'File must be a CSV'}, status=400)
        
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)
        
        imported_count = 0
        errors = []
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
            try:
                question_text = row.get('Question Text')
                marks = row.get('Marks')
                
                if not question_text:
                    errors.append(f'Row {row_num}: Missing Question Text')
                    continue
                
                marks_value = int(marks) if marks else 10
                
                # Create new question
                question = uploadQuestion.objects.create(
                    question=question_text,
                    marks=marks_value
                )
                
                imported_count += 1
                
            except ValueError as e:
                errors.append(f'Row {row_num}: Invalid marks value - {str(e)}')
            except Exception as e:
                errors.append(f'Row {row_num}: {str(e)}')
        
        response_data = {
            'success': True,
            'imported_count': imported_count,
            'errors': errors
        }
        
        if errors:
            response_data['message'] = f'Imported {imported_count} questions with {len(errors)} errors'
        else:
            response_data['message'] = f'Successfully imported {imported_count} questions'
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# User management API endpoints
@api_view(['GET'])
def get_user_details(request, user_id):
    try:
        user = HeadUser.objects.get(userId=user_id)
        user_data = {
            'userId': user.userId,
            'userName': user.userName,
            'password': user.userPassword
        }
        return JsonResponse({'success': True, 'user': user_data})
    except HeadUser.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@api_view(['PUT'])
def update_user(request, user_id):
    try:
        user = HeadUser.objects.get(userId=user_id)
        data = request.data
        
        # Update fields if provided
        if 'userName' in data:
            user.userName = data['userName']
        if 'userPassword' in data:
            user.userPassword = data['userPassword']
        
        user.save()
        
        return JsonResponse({'success': True, 'message': 'User updated successfully'})
    except HeadUser.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@api_view(['DELETE'])
def delete_user(request, user_id):
    try:
        user = HeadUser.objects.get(userId=user_id)
        user.delete()
        return JsonResponse({'success': True, 'message': 'User deleted successfully'})
    except HeadUser.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
