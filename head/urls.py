from django.urls import path
from . import views
from .views import get_all_questions

urlpatterns = [
    path('create-user/', views.CreateUserView.as_view(), name='create_user'),
    path('upload-question/', views.UploadQuestionView.as_view(), name='upload_question'),
    path("getAllQuestions/", get_all_questions),
    path('create-user-page/', views.create_user_page, name='create_user_page'),
    path('upload-question-page/', views.upload_question_page, name='upload_question_page'),
    path('view-answers-page/', views.view_answers_page, name='view_answers_page'),
    path('view-interview-page/', views.view_interview_page, name='view_interview_page'),
    path('view-users-page/', views.view_users_page, name='view_users_page'),
    path('view-questions-page/', views.view_questions_page, name='view_questions_page'),
    path('interview-results/', views.interview_results, name='interview_results'),
    path('results/', views.results, name='results'),
    # Import/Export endpoints
    path('export-results/', views.export_results, name='export_results'),
    path('export-users/', views.export_users, name='export_users'),
    path('export-questions/', views.export_questions, name='export_questions'),
    path('import-questions/', views.import_questions, name='import_questions'),
    # User management API endpoints
    path('api/user/<str:user_id>/details/', views.get_user_details, name='get_user_details'),
    path('api/user/<str:user_id>/update/', views.update_user, name='update_user'),
    path('api/user/<str:user_id>/delete/', views.delete_user, name='delete_user'),
    # API endpoints for question CRUD
    path('api/question/<int:question_id>/update/', views.update_question, name='update_question'),
    path('api/question/<int:question_id>/delete/', views.delete_question, name='delete_question'),
]
