from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    MeView,
    UsersListView,
    ChangeUserRoleView,
    DeleteUserView,
    GoogleLoginView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("me/", MeView.as_view(), name="me"),
    path("google-login/", GoogleLoginView.as_view(), name="google-login"),

    # Admin routes
    path("admin/users/", UsersListView.as_view(), name="admin-users"),
    path("admin/users/<uuid:user_id>/role/", ChangeUserRoleView.as_view(), name="change-role"),
    path("admin/users/<uuid:user_id>/delete/", DeleteUserView.as_view(), name="delete-user"),
]
