from django.contrib import admin
from .models import AppSettings

@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    list_display = ['id', 'vendor', 'device_id', 'last_updated', 'created_at']
    list_filter = ['vendor', 'last_updated', 'created_at']
    search_fields = ['device_id', 'vendor__business_name', 'vendor__user__username']
    readonly_fields = ['id', 'created_at', 'last_updated']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('vendor', 'vendor__user')
