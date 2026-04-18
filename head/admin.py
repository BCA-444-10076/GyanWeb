from django.contrib import admin
from .models import createUser, uploadQuestion

@admin.register(createUser)
class CreateUserAdmin(admin.ModelAdmin):
    list_display = ('userName', 'userId', 'email', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('userName', 'userId', 'email')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Student Information', {
            'fields': ('userName', 'userId', 'email', 'userPassword')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

admin.site.register(uploadQuestion)
