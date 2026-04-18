from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('head/', include('head.urls')),        # ✅ all head-related URLs will start with /head/
    path('student/', include('student.urls')),
      # ✅ all student-related URLs will start with /student/
]
