from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Experiment, SessionBooking

# Register User model with custom admin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('bio', 'profile_pic')}),
    )

# Register Experiment model
@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = ['exp_key', 'name', 'url']
    list_filter = ['exp_key']
    search_fields = ['name', 'description']

# Register SessionBooking model
@admin.register(SessionBooking)
class SessionBookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'experiment', 'start_time', 'end_time', 'status', 'created_at']
    list_filter = ['status', 'experiment', 'created_at']
    search_fields = ['user__username', 'experiment__name']
    date_hierarchy = 'start_time'
    readonly_fields = ['created_at']

