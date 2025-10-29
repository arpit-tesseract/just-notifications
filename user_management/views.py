from django.shortcuts import render, get_object_or_404
import json
from .models import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .serializers import *
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from configuration.mixins import RecordRuleMixin
from configuration.permissions import HasModelAccessPermission
from rest_framework.parsers import MultiPartParser, JSONParser, FormParser
from .utils import verify_shashan_brand_by_id, get_role_obj_by_name, assign_system_admin_role_if_brand_is_shashan

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
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data.get('refresh')

        # Attempt to blacklist the refresh token
        try:
            token = RefreshToken(refresh_token)
        except (TokenError, InvalidToken):
            # Invalid or malformed token
            return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)

        # Verify token belongs to requesting user
        user_id = int(token.payload.get('user_id'))
        if user_id != request.user.id:
            return Response(
                {"error": "You are not authorized to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            token.blacklist()
            # if blacklist is successful then return success response
            return Response(
                {
                    "message": "Successfully logged out."
                }, status=status.HTTP_200_OK
            )
        except Exception as e:
            # Token already blacklisted or invalid
            Response(
                {"error": "Something went wrong", "details": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class RegisterationView(APIView):
    # model = CustomUser
    # permission_classes = [IsAuthenticated, HasModelAccessPermission]
    parser_classes = [MultiPartParser, JSONParser, FormParser]
    @transaction.atomic
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        relation_category = validated_data.get('relation_category')
        from_user_details = validated_data.get('from_user_details', None)
        existing_from_user_id = validated_data.get("existing_from_user_id", None)
        posts = validated_data.get('posts', None)
        
        # create from/main user
        if from_user_details is not None:
            from_user_role_obj = from_user_details.pop("user_role_obj", None)
            from_user_residential_details = from_user_details.pop("residential_details", None)
            from_user_personal_details = from_user_details.pop("personal_details", None)
            from_user_professional_details = from_user_details.pop("professional_details", None)
            # create from user
            from_user_obj = CustomUser.objects.create_user(**from_user_details)
            from_user_obj.user_role.add(from_user_role_obj)
            from_user = from_user_obj
            
            # create residential details
            if from_user_residential_details is not None:
                ResidentialDetail.objects.create(user=from_user, **from_user_residential_details)
            
            # create personal details 
            if from_user_personal_details is not None:   
                PersonalDetail.objects.create(user=from_user, **from_user_personal_details)
            
            # create professional details
            if from_user_professional_details is not None:
                ProfessionalDetail.objects.create(user=from_user, **from_user_professional_details)
            
            brand_id = from_user_professional_details.get("brand", None)
            val = assign_system_admin_role_if_brand_is_shashan(from_user, brand_id)
            if isinstance(val, Response):
                return val
                    
        if existing_from_user_id is not None:
            from_user = existing_from_user_id
        
        existing_from_user_id = from_user.id
        post_lst = []
        for post in posts:
            to_user_details = post.pop("to_user_details", None)
            existing_to_user_id = post.pop("existing_to_user_id", None)
            
            if to_user_details is not None:
                to_user_role_obj = to_user_details.pop("user_role_obj", None)
                to_user_residential_details = to_user_details.pop("residential_details", None)
                to_user_personal_details = to_user_details.pop("personal_details", None)
                to_user_professional_details = to_user_details.pop("professional_details", None)
                to_user_custom_post_no = to_user_details.pop("custom_post_no", None)
                # create to user
                to_user_obj = CustomUser.objects.create_user(**to_user_details)
                to_user_obj.user_role.add(to_user_role_obj)
                to_user = to_user_obj
                
                # create residential details
                if to_user_residential_details is not None:
                    ResidentialDetail.objects.create(user=to_user, **to_user_residential_details)
                
                # create personal details 
                if to_user_personal_details is not None:   
                    PersonalDetail.objects.create(user=to_user, **to_user_personal_details)
                
                # create professional details
                if to_user_professional_details is not None:
                    ProfessionalDetail.objects.create(user=to_user, **to_user_professional_details)
                
                brand_id = to_user_professional_details.get("brand", None)
                val = assign_system_admin_role_if_brand_is_shashan(to_user, brand_id)
                if isinstance(val, Response):
                    return val
            
            if existing_to_user_id is not None:
                to_user = existing_to_user_id
            
            post_lst.append(to_user.id)
            designation = post.pop("designation")
            relation_obj = Relation.objects.create(
                from_user=from_user, 
                relation_category=relation_category, 
                designation=designation, 
                to_user=to_user,
                custom_post_no = to_user_custom_post_no
            )
        data = {
            "existing_from_user_id": existing_from_user_id,
            "posts": post_lst
        }
        user_data = UserRegistrationOutPutSerializer(data)
        return Response(
            {
                "data":user_data.data
            }, status=status.HTTP_201_CREATED
        )


class UserPhotoUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    
    def patch(self, request, user_id):
        user = get_object_or_404(CustomUser, id=user_id)
        serializer = UserPhotoUploadSerializer(
            instance=user, 
            data=request.data, 
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDocumentUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, user_id):
        user = get_object_or_404(CustomUser, id=user_id)
        # Get or create the document record for this user
        document, created = Document.objects.get_or_create(user=user)
        
        serializer = UserDocumentUploadSerializer(
            instance=document, 
            data=request.data, 
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)