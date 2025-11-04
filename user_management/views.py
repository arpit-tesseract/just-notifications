from django.shortcuts import render, get_object_or_404
import copy
import json
from .models import *
from configuration.models import Designation
from .permissions import *
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
from .utils import assign_system_admin_role_if_brand_is_shashan

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


class RegisterationView(RecordRuleMixin, APIView):
    model = CustomUser
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    parser_classes = [MultiPartParser, JSONParser, FormParser]
    
    @transaction.atomic
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        relation_category = validated_data.get('relation_category')
        posts = validated_data.get('posts', None)
        
        higher_designation = None
        relations = []

        response_data = []
        
        for index, post in enumerate(posts):
            user_details = post.pop("user_details", None)
            existing_user_obj = user_details.pop("user_id", None)
            user_custom_post_no = post.pop("custom_post_no", None)
            designation = post.pop("designation", None)
            
            # get higher designation
            if higher_designation is None:
                higher_designation = designation
            else:
                if higher_designation.post_no > designation.post_no:
                    higher_designation = designation
            
            if user_details:
                user_role_obj = user_details.pop("user_role", None)
                user_residential_details = user_details.pop("residential_details", None)
                user_personal_details = user_details.pop("personal_details", None)
                user_bussiness_details = user_details.pop("bussiness_details", None)
                
                # create to user
                if existing_user_obj is not None:
                    # update existing user
                    user_obj = existing_user_obj
                    for attr, value in user_details.items():
                        setattr(user_obj, attr, value)
                    user_obj.save()
                        
                else:    
                    user_obj = CustomUser.objects.create_user(**user_details)
                
                # create user role
                user_obj.user_role.add(user_role_obj)
                user_obj = user_obj
                response_data.append(user_obj.id)
                
                # create residential details
                if user_residential_details is not None:
                    user_residential_details['residential_type'] = "home"
                    residential_obj, created = ResidentialDetail.objects.update_or_create(
                        user=user_obj, 
                        defaults=user_residential_details
                    )
                    print("Residential:", residential_obj)
                    # print(residential_obj.total_no_of_rooms)
                    # create rooms based on total no of rooms
                    for i in range(1, residential_obj.total_no_of_rooms + 1):
                        RoomDetail.objects.update_or_create(
                            residential_details=residential_obj,
                            defaults={
                                "room_no": f"room - {i}"
                            }
                        )
                    
                
                # create personal details 
                if user_personal_details is not None:   
                    PersonalDetail.objects.update_or_create(
                        user=user_obj,
                        defaults= user_personal_details
                        )
                
                # create professional details
                if user_bussiness_details is not None:
                    for bussiness_detail in user_bussiness_details:
                        user_professional_details = bussiness_detail.get("professional_details", None)
                        user_professional_residential_details = bussiness_detail.get("professional_residential_details", None)
                        
                        if user_professional_residential_details is not None:
                            # Try to find if residential details already exists
                            category_of_user = user_professional_residential_details.pop("category_of_user", None)
                            
                            try:
                                residential_obj = ResidentialDetail.objects.get(
                                    residential_type="bussiness",
                                    **user_professional_residential_details
                                )
                            except ResidentialDetail.DoesNotExist:
                                # create residential details
                                residential_obj = ResidentialDetail.objects.create(
                                    residential_type ="bussiness",
                                    **user_professional_residential_details
                                )
                            except Exception as e:
                                return Response(
                                    {"error": "Something went wrong", "details": str(e)},
                                    status=status.HTTP_400_BAD_REQUEST
                                )                                
                        
                        if user_professional_details is not None:
                            user_professional_details['residential_details'] = residential_obj
                            ProfessionalDetail.objects.update_or_create(
                                user = user_obj, 
                                defaults=user_professional_details
                            )
                        
                        # assign system admin role if brand is shashan
                        brand_id = user_professional_details.get("brand", None)
                        val = assign_system_admin_role_if_brand_is_shashan(user_obj, brand_id)
                        if isinstance(val, Response):
                            return 
                        
            relations.append(
                {
                    'relation_category': relation_category,
                    'designation': designation,
                    'user_obj': user_obj,
                    'custom_post_no': user_custom_post_no,
                }
            )

        from_user, relations = get_higher_designation_user(higher_designation, relations)
        for relation in relations:
            try:
                relation_obj = Relation.objects.get(
                    from_user = from_user, 
                    relation_category = relation.get('relation_category'), 
                    designation = relation.get('designation'), 
                    to_user = relation.get('user_obj'),
                    custom_post_no = relation.get('custom_post_no')
                )
            except Relation.DoesNotExist:
                Relation.objects.create(
                    from_user = from_user, 
                    relation_category = relation.get('relation_category'), 
                    designation = relation.get('designation'), 
                    to_user = relation.get('user_obj'),
                    custom_post_no = relation.get('custom_post_no')
                )
            except Exception as e:
                return Response(
                    {"error": "Something went wrong", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            {
                "posts":response_data
            }, status=status.HTTP_201_CREATED
        )


class UserPhotoUploadView(RecordRuleMixin, APIView):
    model = CustomUser
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
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


class UserDocumentUploadView(RecordRuleMixin, APIView):
    model = Document
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
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

class UserRoleListView(APIView):
    def get(self, request):
        user_roles = UserRole.objects.all()
        serializer = UserRoleSerializer(user_roles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserRoleAssignView(APIView):
    permission_classes = [IsAuthenticated, SystemAdminPermission]
    
    def post(self, request):
        serializer = UserRoleAssignAndRemoveSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        user_id = validated_data.get("user_id")
        role_ids_to_add = validated_data.get("role_ids")
        
        # Loggedin user cannot add self roles except super admin
        logged_in_user = request.user        
        if logged_in_user.id == user_id:
            if logged_in_user.check_is_super_admin() == False:
                return Response(
                    {
                        "error": "You are not authorized to perform this action."
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
                
        # Check if role IDs are provided
        if role_ids_to_add is None or len(role_ids_to_add) == 0:
            return Response(
                {
                    "error": "No role IDs provided."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user exists
        user = get_object_or_404(CustomUser, id=user_id)
        roles = UserRole.objects.filter(id__in=role_ids_to_add)
        
        # Check if all role IDs are valid
        if not roles.exists():
            return Response(
                {
                    "error": "Invalid role IDs provided."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
               
        user.user_role.add(*roles)
        return Response(
            {
                "message": "Roles assigned successfully.",
                "roles": UserRoleSerializer(user.user_role.all(), many=True).data
            },
            status=status.HTTP_200_OK
        )


class UserRoleRemoveView(APIView):
    permission_classes = [IsAuthenticated, SystemAdminPermission]
    
    def post(self, request):
        serializer = UserRoleAssignAndRemoveSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user_id = serializer.validated_data['user_id']
        role_ids_to_remove = serializer.validated_data['role_ids']

        # Loggedin user cannot remove self roles except super admin
        logged_in_user = request.user        
        if logged_in_user.id == user_id:
            if logged_in_user.check_is_super_admin() == False:
                return Response(
                    {
                        "error": "You are not authorized to perform this action."
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
        # Check if role IDs are provided
        if role_ids_to_remove is None or len(role_ids_to_remove) == 0:
            return Response(
                {
                    "error": "No role IDs provided."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the user    
        user = get_object_or_404(CustomUser, id=user_id)
        
        # Get the count of roles the user currently has.
        current_role_count = user.user_role.count()
        
        # Get the count of roles the user is trying to remove.
        matching_roles_to_remove_count = user.user_role.filter(id__in=role_ids_to_remove).count()
        
        # Check if the user is trying to remove all roles.
        if current_role_count > 0 and matching_roles_to_remove_count == current_role_count:
            return Response(
                {
                    "error": "Cannot remove all roles. A user must have at least one role."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        roles = UserRole.objects.filter(id__in=role_ids_to_remove)
        if not roles.exists():
            return Response(
                {
                    "error": "Invalid role IDs provided."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        user.user_role.remove(*roles)
        return Response(
            {
                "message": "Roles removed successfully.",
                "roles": UserRoleSerializer(user.user_role.all(), many=True).data
            },
            status=status.HTTP_200_OK
        )

class GetUserRoleView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id=None):
        if user_id is None:
            user_id = request.user.id
        user_obj = get_obj_by_modle_and_id(CustomUser, user_id)
        if user_obj is None:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        user_roles = user_obj.user_role.all()
        serializer = UserRoleSerializer(user_roles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)