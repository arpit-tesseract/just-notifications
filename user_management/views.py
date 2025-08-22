from django.shortcuts import render
from configuration import models as configm
from .models import *
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action, api_view, permission_classes
from django.db import transaction
from .serializers import *
from configuration.models import *
from configuration.serializers import *

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        else:
            return UserDetailSerializer
    
    def get_queryset(self):
        # You can add filtering based on user permissions here
        queryset = CustomUser.objects.all()
        
        # Example: Filter based on user role or permissions
        # if not self.request.user.is_superuser:
        #     # Add your filtering logic here
        #     pass
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def system_users(self):
        """Get all system users"""
        system_users = self.get_queryset().filter(is_system_user=True)
        serializer = self.get_serializer(system_users, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def regular_users(self):
        """Get all regular users"""
        regular_users = self.get_queryset().filter(is_system_user=False)
        serializer = self.get_serializer(regular_users, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def verify_user(self, request, pk=None):
        """Verify a user"""
        user = self.get_object()
        user.is_verified = True
        user.save()
        return Response({'message': 'User verified successfully'})
    
    @action(detail=True, methods=['post'])
    def unverify_user(self, request, pk=None):
        """Unverify a user"""
        user = self.get_object()
        user.is_verified = False
        user.save()
        return Response({'message': 'User unverified successfully'})

@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_access_option(request):
    user = request.user
    if user.user_role == 'superadmin':
        accesses = Accesses.objects.all()
    else:
        accesses = user.access.all()

    serializer = AccessesSerializer(accesses, many=True)
    return Response(serializer.data)