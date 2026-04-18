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
    results = InterviewResult.objects.select_related('user').order_by('-id')
    
    # Calculate statistics
    excellent_count = results.filter(result_summary='Excellent').count()
    good_count = results.filter(result_summary='Good').count()
    fair_count = results.filter(result_summary='Fair').count()
    
    return render(request, 'head/interview_results.html', {
        'results': results,
        'excellent_count': excellent_count,
        'good_count': good_count,
        'fair_count': fair_count
    })

def results(request):
    # Generate comprehensive results data
    total_users = HeadUser.objects.count()
    total_questions = uploadQuestion.objects.count()
    completed_interviews = InterviewResult.objects.count()
    
    # Calculate performance percentages
    excellent_count = InterviewResult.objects.filter(result_summary='Excellent').count()
    good_count = InterviewResult.objects.filter(result_summary='Good').count()
    fair_count = InterviewResult.objects.filter(result_summary='Fair').count()
    total_results = excellent_count + good_count + fair_count
    
    # Calculate percentages
    excellent_percentage = (excellent_count / total_results * 100) if total_results > 0 else 0
    good_percentage = (good_count / total_results * 100) if total_results > 0 else 0
    fair_percentage = (fair_count / total_results * 100) if total_results > 0 else 0
    
    # Get top performers
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

# Generate detailed HTML report
@api_view(['GET'])
def generate_detailed_report(request):
    try:
        # Get all data for the report
        total_users = HeadUser.objects.count()
        total_questions = uploadQuestion.objects.count()
        completed_interviews = InterviewResult.objects.count()
        
        excellent_count = InterviewResult.objects.filter(result_summary='Excellent').count()
        good_count = InterviewResult.objects.filter(result_summary='Good').count()
        fair_count = InterviewResult.objects.filter(result_summary='Fair').count()
        total_results = excellent_count + good_count + fair_count
        
        excellent_percentage = (excellent_count / total_results * 100) if total_results > 0 else 0
        good_percentage = (good_count / total_results * 100) if total_results > 0 else 0
        fair_percentage = (fair_count / total_results * 100) if total_results > 0 else 0
        
        top_students = StudentMarks.objects.select_related('user').order_by('-marks')[:10]
        average_score = StudentMarks.objects.aggregate(average_marks=Avg('marks'))['average_marks'] or 0
        
        # Generate HTML report
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Detailed Results Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat-box {{ text-align: center; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .excellent {{ color: #28a745; }}
                .good {{ color: #17a2b8; }}
                .fair {{ color: #ffc107; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>System Results Report</h1>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="stats">
                <div class="stat-box">
                    <h3>{total_users}</h3>
                    <p>Total Students</p>
                </div>
                <div class="stat-box">
                    <h3>{total_questions}</h3>
                    <p>Total Questions</p>
                </div>
                <div class="stat-box">
                    <h3>{completed_interviews}</h3>
                    <p>Completed Interviews</p>
                </div>
                <div class="stat-box">
                    <h3>{average_score:.1f}</h3>
                    <p>Average Score</p>
                </div>
            </div>
            
            <h2>Performance Distribution</h2>
            <div class="stats">
                <div class="stat-box">
                    <h3 class="excellent">{excellent_percentage:.1f}%</h3>
                    <p>Excellent ({excellent_count} students)</p>
                </div>
                <div class="stat-box">
                    <h3 class="good">{good_percentage:.1f}%</h3>
                    <p>Good ({good_count} students)</p>
                </div>
                <div class="stat-box">
                    <h3 class="fair">{fair_percentage:.1f}%</h3>
                    <p>Fair ({fair_count} students)</p>
                </div>
            </div>
            
            <h2>Top Performers</h2>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Student Name</th>
                        <th>User ID</th>
                        <th>Marks</th>
                        <th>Grade</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for i, student in enumerate(top_students, 1):
            html_content += f"""
                    <tr>
                        <td>{i}</td>
                        <td>{student.user.userName}</td>
                        <td>{student.user.userId}</td>
                        <td>{student.marks}</td>
                        <td>{student.grade or 'N/A'}</td>
                    </tr>
            """
        
        html_content += """
                </tbody>
            </table>
        </body>
        </html>
        """
        
        response = HttpResponse(html_content, content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="detailed_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html"'
        
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# Import results from CSV
@api_view(['POST'])
def import_results(request):
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
                user_id = row.get('User ID')
                marks = row.get('Marks')
                grade = row.get('Grade')
                
                if not user_id or not marks:
                    errors.append(f'Row {row_num}: Missing User ID or Marks')
                    continue
                
                # Find user
                try:
                    user = HeadUser.objects.get(userId=user_id)
                except HeadUser.DoesNotExist:
                    errors.append(f'Row {row_num}: User with ID {user_id} not found')
                    continue
                
                # Create or update student marks
                student_mark, created = StudentMarks.objects.update_or_create(
                    user=user,
                    defaults={
                        'marks': float(marks),
                        'grade': grade if grade and grade != 'N/A' else None
                    }
                )
                
                imported_count += 1
                
            except ValueError as e:
                errors.append(f'Row {row_num}: Invalid data format - {str(e)}')
            except Exception as e:
                errors.append(f'Row {row_num}: {str(e)}')
        
        response_data = {
            'success': True,
            'imported_count': imported_count,
            'errors': errors
        }
        
        if errors:
            response_data['message'] = f'Imported {imported_count} records with {len(errors)} errors'
        else:
            response_data['message'] = f'Successfully imported {imported_count} records'
        
        return JsonResponse(response_data)
        
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
                'N/A'  # No creation date field available in createUser model
            ])
        
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)