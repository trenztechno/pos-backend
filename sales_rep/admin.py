from django.contrib import admin
from auth_app.models import SalesRep

@admin.register(SalesRep)
class SalesRepAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'name', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'name', 'phone']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Sales Rep Information', {
            'fields': ('user', 'name', 'phone')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def username(self, obj):
        return obj.user.username
    username.short_description = 'Username'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')
