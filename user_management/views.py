from django.shortcuts import render
from .models import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken


class LoginWithEmailPasswordView(APIView):
    def post(self, request):
        serializer = LoginEmailPasswordSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        email = validated_data.get('email').strip().lower()
        password = validated_data.get('password').strip()
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "Email does not exist"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if user.is_verified == False:
            return Response(
                {
                    "error": "Your account is not verified"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.check_password(password):
            return Response(
                {"error": "Incorrect password"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        refresh = RefreshToken.for_user(user)
        serializer = CustomUserBasicDetailsOutputSerializer(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": serializer.data
            },
            status=status.HTTP_200_OK)


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            access_token = request.data.get("access")

            # Blacklist refresh token
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            # Blacklist access token
            if access_token:
                token = AccessToken(access_token)
                # Add to blacklist manually
                outstanding, _ = OutstandingToken.objects.get_or_create(
                    jti=token["jti"],
                    defaults={
                        "token": str(token),
                        "expires_at": token["exp"],
                    },
                )
                BlacklistedToken.objects.get_or_create(token=outstanding)

            return Response({"detail": "Successfully logged out."}, status=status.HTTP_205_RESET_CONTENT)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    