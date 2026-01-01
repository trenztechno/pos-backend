from django.urls import path
from .views import SettingsPushView

urlpatterns = [
    path('push', SettingsPushView.as_view(), name='settings-push'),
]

