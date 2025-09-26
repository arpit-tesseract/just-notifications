from django.shortcuts import render
from configuration import models as configm
from .models import *
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action, permission_classes, api_view
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

from django.db import transaction
from .serializers import *
from configuration.models import *
from configuration.serializers import *


# class CustomUserViewSet(viewsets.ModelViewSet):
#     queryset = CustomUser.objects.all()
#     permission_classes = [AllowAny]
    
#     def get_serializer_class(self):
#         if self.action == 'create':
#             return UserCreateSerializer
#         elif self.action in ['update', 'partial_update']:
#             return UserUpdateSerializer
#         else:
#             return UserDetailSerializer
    
#     def get_queryset(self):
#         # You can add filtering based on user permissions here
#         queryset = CustomUser.objects.all()
        
#         # Example: Filter based on user role or permissions
#         # if not self.request.user.is_superuser:
#         #     # Add your filtering logic here
#         #     pass
            
#         return queryset
    
#     @action(detail=False, methods=['get'])
#     def system_users(self, request):
#         """Get all system users"""
#         system_users = self.get_queryset().filter(is_system_user=True)
#         serializer = self.get_serializer(system_users, many=True)
#         return Response(serializer.data)
    
#     @action(detail=False, methods=['get'])
#     def regular_users(self, request):
#         """Get all regular users"""
#         regular_users = self.get_queryset().filter(is_system_user=False)
#         serializer = self.get_serializer(regular_users, many=True)
#         return Response(serializer.data)
    
#     @action(detail=True, methods=['post'])
#     def verify_user(self, request, pk=None):
#         """Verify a user"""
#         user = self.get_object()
#         user.is_verified = True
#         user.save()
#         return Response({'message': 'User verified successfully'})
    
#     @action(detail=True, methods=['post'])
#     def unverify_user(self, request, pk=None):
#         """Unverify a user"""
#         user = self.get_object()
#         user.is_verified = False
#         user.save()
#         return Response({'message': 'User unverified successfully'})
    
#     @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticated])
#     def get_details(self, request):
#         user = CustomUser.objects.get(id=request.user.id)
#         serializers = UserDetailSerializer(user)
#         return Response(serializers.data, status=status.HTTP_200_OK)
    

class LoginWithEmailPasswordView(APIView):
    def post(self, request):
        print(request.data)
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
        
