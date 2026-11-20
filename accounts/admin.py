from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Student Profile & M-Pesa Contact'
    fields = ('phone_number',)


class CustomUserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]
    list_display = (
        'username', 'email', 'first_name', 'last_name', 
        'get_phone_number', 'is_staff', 'is_active', 'date_joined'
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'profile__phone_number')

    @admin.display(description='M-Pesa Phone')
    def get_phone_number(self, obj):
        try:
            return obj.profile.phone_number or '—'
        except Exception:
            return '—'


# Re-register User with customized admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_email', 'phone_number')
    search_fields = ('user__username', 'user__email', 'phone_number')

    @admin.display(description='Email')
    def user_email(self, obj):
        return obj.user.email
