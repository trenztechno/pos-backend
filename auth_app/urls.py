from django.urls import path
from .views import (
    login,
    logout,
    register,
    forgot_password,
    reset_password,
    profile,
    create_staff_user,
    list_vendor_users,
    reset_staff_password,
    remove_staff_user,
)

urlpatterns = [
    path('register', register, name='register'),
    path('login', login, name='login'),
    path('logout', logout, name='logout'),
    path('forgot-password', forgot_password, name='forgot_password'),
    path('reset-password', reset_password, name='reset_password'),
    path('profile', profile, name='profile'),

    # Vendor multi-user management (owner only)
    path('vendor/users/create', create_staff_user, name='vendor-create-staff-user'),
    path('vendor/users', list_vendor_users, name='vendor-list-users'),
    path('vendor/users/<int:user_id>/reset-password', reset_staff_password, name='vendor-reset-staff-password'),
    path('vendor/users/<int:user_id>', remove_staff_user, name='vendor-remove-staff-user'),
]

