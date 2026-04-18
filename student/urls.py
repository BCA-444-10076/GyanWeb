from django.urls import path
from . import views

urlpatterns = [
    
    path("userLogin/", views.UserLogin.as_view(), name='user_login'),
    path("submitAnswer/", views.SubmitAnswer.as_view(), name='submit_answer'),
    path("viewQuestions/", views.ViewQuestion.as_view(), name='view_questions'),
    path('login/', views.login_page),
    path('logout/', views.logout_view, name='student_logout'),
    path('startExam/', views.start_exam_page),
    path('test/', views.test_page),
    path('thankyou/', views.thankyou_page),
    path('saveInterview/', views.SaveInterviewQA.as_view(), name='save_interview'),
    path('saveInterviewResult/', views.SaveInterviewResult.as_view(), name='save_interview_result'),
    path('interview/', views.interview_page, name='interview_page'),

    # ✅ New endpoints for Head Panel
    path('getStudentAnswers/', views.get_student_answers, name='get_student_answers'),
    path('saveStudentMarks/', views.save_student_marks, name='save_student_marks'),
    path('getInterviewTranscript/', views.get_interview_transcript, name='get_interview_transcript'),

    path("result/", views.student_result_page, name='student_result_page'),
    path("getStudentResult/", views.get_student_result)
]
