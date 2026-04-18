from django.shortcuts import render
from head.models import createUser, uploadQuestion
from student.models import InterviewResult, StudentMarks
from django.db.models import Count, Avg

def home(request):
    """Home page view with platform statistics and information"""
    # Get platform statistics
    total_students = createUser.objects.count()
    total_questions = uploadQuestion.objects.count()
    completed_exams = StudentMarks.objects.count()
    completed_interviews = InterviewResult.objects.count()
    
    # Calculate average performance
    average_score = StudentMarks.objects.aggregate(average_score=Avg('marks'))['average_score'] or 0
    
    # Get recent activity counts
    recent_students = createUser.objects.all().order_by('-id')[:5]
    top_performers = StudentMarks.objects.select_related('user').order_by('-marks')[:5]
    
    context = {
        'total_students': total_students,
        'total_questions': total_questions,
        'completed_exams': completed_exams,
        'completed_interviews': completed_interviews,
        'average_score': round(average_score, 1),
        'recent_students': recent_students,
        'top_performers': top_performers,
    }
    
    return render(request, 'home.html', context)
