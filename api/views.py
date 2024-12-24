from django.shortcuts import render
from rest_framework import generics, status
from rest_framework import exceptions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from . import serializers as api_serializers
from . import models


# Create your views here.
class RegisterAccountView(generics.ListCreateAPIView):
    queryset = models.Profile.objects.all()
    serializer_class = api_serializers.CustomUserProfileSerializer

    def get_serializer_context(self):
        try:
            user_profile = models.Profile.objects.get(user=self.request.user)
        except models.Profile.DoesNotExist:
            return Response(
                {"error": "User not authenticated"}, status=status.HTTP_400_BAD_REQUEST
            )
        context = super().get_serializer_context()
        context["user_profile"] = user_profile
        return context


class LogoutView(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response(
                {"error": "Refresh token is required for logout."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"detail": "Logout Successfull."}, status=status.HTTP_205_RESET_CONTENT
            )
        except Exception as e:
            return Response(
                {"error": "Invalid or malformed refresh token"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PasswordChangeView(APIView):
    def post(self, request):
        try:
            user_profile = models.Profile.objects.get(user=request.user)
            user = user_profile.user
            # password match verification to be done at the frontend

            new_password = request.data.get("new_password", None)
            if not new_password:
                return Response(
                    {"error": "new password not specified"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.set_password(new_password)
            user.save()
            return Response(
                {"detail": "password changed successfull"},
                status=status.HTTP_200_OK,
            )
        except models.Profile.DoesNotExist:
            return Response(
                {"error": "user account not found"}, status=status.HTTP_400_BAD_REQUEST
            )


class PasswordResetView(generics.CreateAPIView):
    queryset = models.PasswordReset.objects.all()
    serializer_class = api_serializers.PasswordResetSerializer


class ProfileList(generics.ListCreateAPIView):
    queryset = models.Profile.objects.all()
    serializer_class = api_serializers.CustomUserProfileSerializer
