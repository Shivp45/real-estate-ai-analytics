from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    ChangeRoleSerializer,
    PasswordConfirmSerializer,
)
from .permissions import IsAdmin

User = get_user_model()


def get_tokens_for_user(user: User):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]  

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = get_tokens_for_user(user)
            return Response(
                {
                    "success": True,
                    "user": UserSerializer(user).data,
                    "tokens": tokens,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )



class LoginView(APIView):
    permission_classes = [AllowAny]  

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = serializer.validated_data["user"]
        tokens = get_tokens_for_user(user)
        return Response(
            {
                "success": True,
                "user": UserSerializer(user).data,
                "tokens": tokens,
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {"success": True, "user": UserSerializer(request.user).data},
            status=status.HTTP_200_OK,
        )


class UsersListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        from analytics.models import SearchHistory  # avoid circular import

        users = User.objects.all().order_by("-created_at")
        data = []
        for u in users:
            history_count = SearchHistory.objects.filter(user=u).count()
            data.append(
                {
                    "user": UserSerializer(u).data,
                    "history_count": history_count,
                }
            )
        return Response({"success": True, "users": data})


class ChangeUserRoleView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, user_id):
        try:
            target = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"success": False, "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        role_serializer = ChangeRoleSerializer(data=request.data)
        pwd_serializer = PasswordConfirmSerializer(data=request.data)

        if not role_serializer.is_valid() or not pwd_serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": {
                        "role": role_serializer.errors,
                        "password": pwd_serializer.errors,
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        admin_password = pwd_serializer.validated_data["password"]
        if not check_password(admin_password, request.user.password):
            return Response(
                {"success": False, "message": "Incorrect admin password."},
                status=status.HTTP_403_FORBIDDEN,
            )

        target.role = role_serializer.validated_data["role"]
        target.save()

        return Response(
            {
                "success": True,
                "message": "User role updated.",
                "user": UserSerializer(target).data,
            }
        )


class DeleteUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, user_id):
        try:
            target = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"success": False, "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if target == request.user:
            return Response(
                {"success": False, "message": "You cannot delete yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pwd_serializer = PasswordConfirmSerializer(data=request.data)
        if not pwd_serializer.is_valid():
            return Response(
                {"success": False, "errors": pwd_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        admin_password = pwd_serializer.validated_data["password"]
        if not check_password(admin_password, request.user.password):
            return Response(
                {"success": False, "message": "Incorrect admin password."},
                status=status.HTTP_403_FORBIDDEN,
            )

        target.delete()

        return Response(
            {"success": True, "message": "User deleted successfully."},
            status=status.HTTP_200_OK,
        )


class GoogleLoginView(APIView):
    authentication_classes = []   # public
    permission_classes = []       # public

    def post(self, request):
        id_token_value = request.data.get("id_token")
        if not id_token_value:
            return Response(
                {"success": False, "message": "Missing id_token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        client_id = settings.GOOGLE_CLIENT_ID
        if not client_id:
            return Response(
                {"success": False, "message": "Google login not configured."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            idinfo = id_token.verify_oauth2_token(
                id_token_value,
                google_requests.Request(),
                client_id,
            )
        except Exception:
            return Response(
                {"success": False, "message": "Invalid Google token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = idinfo.get("email")
        if not email:
            return Response(
                {"success": False, "message": "Google account missing email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user, created = User.objects.get_or_create(
            username=email,
            defaults={"email": email, "role": User.ROLE_USER},
        )

        if created:
            user.set_unusable_password()
            user.save()

        tokens = get_tokens_for_user(user)

        return Response(
            {
                "success": True,
                "user": UserSerializer(user).data,
                "tokens": tokens,
            }
        )
