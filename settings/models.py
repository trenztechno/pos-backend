from django.db import models
import uuid

class AppSettings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey('auth_app.Vendor', on_delete=models.CASCADE, related_name='app_settings', null=True, blank=True)
    device_id = models.CharField(max_length=255)
    settings_data = models.JSONField()  # Store config blob from mobile
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-last_updated']
        unique_together = [['vendor', 'device_id']]  # One settings per device per vendor
        indexes = [
            models.Index(fields=['vendor', 'device_id']),
            models.Index(fields=['device_id']),
        ]
    
    def __str__(self):
        return f"Settings for {self.vendor.business_name or self.vendor.user.username} - {self.device_id}"
