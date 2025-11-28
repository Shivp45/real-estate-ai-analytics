from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    list_display = ("username", "email", "role", "is_staff", "is_superuser", "date_joined")
    list_filter = ("role", "is_staff", "is_superuser")
    search_fields = ("username", "email")

    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Roles & Permissions", {"fields": ("role", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2", "role", "is_staff", "is_superuser"),
        }),
    )
