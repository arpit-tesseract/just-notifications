from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .pagination import UserManagementPagination
from .models import *
from configuration.models import Designation
from .permissions import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework import viewsets
from .serializers import *
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from configuration.mixins import RecordRuleMixin, FilteredQuerysetMixin
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
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        relation_category = validated_data.get('relation_category')
        
        try:
            with transaction.atomic():
                # create residential details
                residential_details = validated_data.get('residential_details')
                residential_details['residential_type'] = "home"
                # room_details = residential_details.get('room_details', None)
                residential_obj, created = ResidentialDetail.objects.get_or_create(**residential_details)
                print("residential_obj:", residential_obj.pending_rooms_to_allocate)
                if created:
                    residential_obj.pending_rooms_to_allocate = {}
                    for key, val in residential_obj.room_details.items():
                        residential_obj.pending_rooms_to_allocate[key] = 1
                    # residential_obj.pending_rooms_to_allocate = {key: 1 for key in room_details.keys()}
                    residential_obj.save()
                    
                print("residential_obj", residential_obj.pending_rooms_to_allocate)
                    
                if isinstance(residential_obj, Response):
                    return residential_obj
                
                
                posts = validated_data.get('posts', None)
                
                higher_designation = None
                higher_designation_failed_count = 0
                relations = []

                response_data = []
                
                active_users = []
                room_details = residential_obj.room_details
                for index, post in enumerate(posts):
                    user_details = post.pop("user_details", None)
                    existing_user_obj = user_details.pop("user_id", None)
                    user_post_no = post.pop("post_no", None)
                    designation = post.pop("designation", None)
                    
                    if user_details:
                        user_role_obj = user_details.pop("user_role", None)
                        # user_residential_details = user_details.pop("residential_details", None)
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
                        
                        # add in list for room sharing in future
                        if user_obj.expired_date is None:
                            active_users.append(user_obj)
                        
                        # assign residential details
                        user_obj.residential_details = residential_obj
                        user_obj.save()
                        
                        # add user id in response data list
                        response_data.append(user_obj.id)
                        
                        # add user role to user 
                        user_obj.user_role.add(user_role_obj)
                        
                        # get higher designation for the create main user / from user
                        if higher_designation is None:
                            if user_obj.expired_date is None:
                                higher_designation = designation
                            #     if higher_designation_failed_count > 0:
                            #         higher_designation_failed_count -= 1
                            # else:
                            #     higher_designation_failed_count += 1
                                
                        else:
                            if higher_designation.code > designation.code and user_obj.expired_date is None:
                                higher_designation = designation
                            #     if higher_designation_failed_count > 0:
                            #         higher_designation_failed_count -= 1
                            # else:
                            #     higher_designation_failed_count += 1
                        
                        print(higher_designation_failed_count)
                        if higher_designation_failed_count >= 2:
                            raise Exception("Automatic set main user failed!")
                            # transaction.set_rollback(True)
                        
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
                                    user_professional_residential_details['residential_type'] = "bussiness"
                                    user_professional_residential_obj = get_or_create_residential_details(**user_professional_residential_details)
                                    if isinstance(user_professional_residential_obj, Response):
                                        return user_professional_residential_obj
                                
                                if user_professional_details is not None:
                                    # user_professional_details['residential_details'] = residential_obj
                                    ProfessionalDetail.objects.update_or_create(
                                        user = user_obj,
                                        residential_details = user_professional_residential_obj, 
                                        defaults=user_professional_details
                                    )
                                
                                # assign system admin role if brand is shashan
                                brand_id = user_professional_details.get("brand", None)
                                val = assign_system_admin_role_if_brand_is_shashan(user_obj, brand_id)
                                if isinstance(val, Response):
                                    return val
                                
                    relations.append(
                        {
                            'relation_category': relation_category,
                            'designation': designation,
                            'user_obj': user_obj,
                            'post_no': user_post_no,
                        }
                    )
                
                from_user, from_user_designation, to_users = get_from_user_and_to_users(higher_designation, relations)
                relation_obj_lst = []
                for to_user in to_users:
                    
                    try:
                        relation_obj = Relation.objects.get(
                            from_user = from_user, 
                            relation_category = to_user.get('relation_category'), 
                            from_user_designation = from_user_designation,
                            designation = to_user.get('designation'), 
                            to_user = to_user.get('user_obj'),
                            post_no = to_user.get('post_no')
                        )
                    except Relation.DoesNotExist:
                        relation_obj = Relation.objects.create(
                            from_user = from_user, 
                            relation_category = to_user.get('relation_category'), 
                            from_user_designation = from_user_designation,
                            designation = to_user.get('designation'), 
                            to_user = to_user.get('user_obj'),
                            post_no = to_user.get('post_no')
                        )
                    except Exception as e:
                        raise ValidationError(f"Error in creating relation between {from_user} and {to_user.get('user_obj')}.")
                    
                    relation_obj_lst.append(relation_obj)
                
                # 1. Process the FROM_USER (for ex: husband)
                if from_user.expired_date is None:
                    
                    # This function is now safe (if you use my updated version)
                    from_user.is_verified = True
                    from_user.save()
                    # mark_as_verify_or_unverify_user(from_user) 
                    allocate_rooms_for_from_user(from_user)
                    # Allocates room directly, WITHOUT finding a parent
                    # allocate_room_dict = allocate_rooms(0, room_details, from_user) 
                    # from_user.allocated_rooms = allocate_room_dict
                    # from_user.save()
                
                # 2. Process the TO_USER (for ex: wife, son)
                for relation_obj in relation_obj_lst:
                    mark_as_verify_or_unverify_user(relation_obj.to_user, relation_obj.relation_category)
                    
                    if relation_obj.to_user.expired_date is not None:
                        continue
                    
                    if relation_obj.designation.name == "wife" or relation_obj.designation.name == "Wife":
                        allocate_room_same_as_parent(relation_obj.to_user, relation_obj.relation_category)
                    else:
                        if relation_obj.to_user.marital_status == "single":
                            allocate_room_same_as_parent(relation_obj.to_user, relation_obj.relation_category)
                        # else:
                        #     allocate_rooms(relation_obj.to_user)
                            # allocate_room_dict = allocate_rooms(0, room_details, relation_obj.to_user) 
                            # relation_obj.to_user.allocated_rooms = allocate_room_dict
                            # relation_obj.to_user.save()
                
                # 2. Process the TO_USER (for ex: wife, son)
                # for user_obj in to_users: 
                #     if user_obj.expired_date is not None:
                #         continue
                    
                #     # is guaranteed to be a 'to_user' and has a parent
                #     mark_as_verify_or_unverify_user(user_obj) 
                #     allocate_room_same_as_parent(user_obj)
                        
                # for index, user_obj in enumerate(active_users):
                #     mark_as_verify_or_unverify_user(user_obj)
                #     if (user_obj.marital_status == "single") or (is_to_user(user_obj) and user_obj.marital_status == "married"):
                #         allocate_room_same_as_parent(user_obj)
                #     else:
                #         allocate_room_dict = allocate_rooms(index, room_details, user_obj)
                #         user_obj.allocated_rooms = allocate_room_dict
                #         user_obj.save()
                        
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
    
    
    def get(self, request, **kwargs):
        user_id = request.query_params.get("user_id", None)
        if user_id is None:
            return Response(
                {
                    "error": "User ID is required."
                }, status=status.HTTP_400_BAD_REQUEST
            )
            
        relation_category = request.query_params.get("relation_category", None)
        if relation_category is None:
            return Response(
                {
                    "error": "Relation Category is required."
                }, status=status.HTTP_400_BAD_REQUEST
            )
            
        user_obj = get_object_or_404(CustomUser, id=user_id)
        print("---------------------------------")
        print(f"DEBUG: user_obj is: {user_obj}")
        print(f"DEBUG: relation_category is: '{relation_category}'")
        print(f"DEBUG: Type of user_obj is: {type(user_obj)}")
        print("---------------------------------")
        # get the residential details of user
        residential_obj = user_obj.residential_details
        if residential_obj is None:
            return Response(
                {
                    "error": "Residential Details not found."
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        # get the relations of user
        relation_obj = Relation.objects.filter(
            Q(from_user=user_obj) | Q(to_user=user_obj),
            relation_category__iexact=relation_category
        ).first()
        
        print("Relation object:",relation_obj)
        if not relation_obj:
            result = {
                "residential_details": ResidentialDetailGetSerializer(residential_obj).data,
                "relation_category": relation_category,
                "number_of_post": 1,
                "posts": [
                        {
                            "user_details": UserSerializerForGet(user_obj).data,
                            "designation": "self",
                            "post_no": None,
                        }
                    ],
            }
            return Response(result, status=status.HTTP_200_OK)
            # return Response(
            #     {
            #         "error": "Relations not found."
            #     }, status=status.HTTP_400_BAD_REQUEST
            # )
        
        posts_data = []
        
        # create first post for from user
        from_user_details = UserSerializerForGet(relation_obj.from_user).data
        post = {
            "user_details": from_user_details,
            "designation": relation_obj.from_user_designation.name,
            "post_no": relation_obj.post_no
        }
        posts_data.append(post)
        
        relation_obj_lst = Relation.objects.filter(
            from_user = relation_obj.from_user,
            relation_category__iexact=relation_category
        )
        print("to user relation_obj_lst:",relation_obj_lst)
        for relation_obj in relation_obj_lst:
            user_details = UserSerializerForGet(relation_obj.to_user).data
            post = {
                "user_details": user_details,
                "designation": relation_obj.designation.name,
                "post_no": relation_obj.post_no
            }
            posts_data.append(post)
        
        # first_relation = relation_obj_lst[0]
        # from_user_post = {
        #     "user_details": UserSerializerForGet(first_relation.from_user).data,
        #     "designation": first_relation.designation.name,
        #     "post_no": first_relation.post_no
        # }
        # posts_data.append(from_user_post)
        
        result = {
            "residential_details": ResidentialDetailGetSerializer(residential_obj).data,
            "relation_category": relation_category,
            "number_of_post": len(posts_data),
            "posts": posts_data,
        }
        return Response(result, status=status.HTTP_200_OK)
    
    def delete(self, request):
        user_id = request.query_params.get("user_id", None)
        if user_id is None:
            return Response(
                {
                    "error": "User ID is required."
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        user_obj = get_object_or_404(CustomUser, id=user_id)
        user_obj.archive()
            
        return Response(
            {
                "message": "User deleted successfully."
            }, status=status.HTTP_200_OK
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


class UserListView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    model = CustomUser
    permission_classes = [IsAuthenticated, SystemAdminPermission, HasModelAccessPermission]
    pagination_class = UserManagementPagination
    def get(self, request):
        users = CustomUser.objects.filter(
            is_superuser=False, 
            is_archive=False,
            user_role__name="user")
        serializer = UserListSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ModelAccessView(APIView):
    model = ModelAccess
    permission_classes = [IsAuthenticated, SystemAdminPermission, HasModelAccessPermission]
    
    def get(self, request, user_id=None):
        try:
            if user_id is None:
                user_obj = request.user
            else:
                user_obj = get_object_or_404(CustomUser, id=user_id)
            
            # if user_obj.id == user_obj.id:
            #     return Response({"error": "You cannot edit your own model access rights."}, status=status.HTTP_403_FORBIDDEN)
            
            if user_obj.check_is_super_admin():
                model_access_rights = get_model_access_rights_of_super_admin()
                return Response(
                    model_access_rights,
                    status=status.HTTP_200_OK
                )
            
            model_access_rights_obj_lst = user_obj.model_access_permission.all()
            if model_access_rights_obj_lst.exists():
                serializer = ModelAccessSerializer(model_access_rights_obj_lst, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response([], status=status.HTTP_200_OK)
            
            # model_access_rights = get_default_model_access_rights()
            # return Response(
            #     model_access_rights,
            #     status=status.HTTP_200_OK
            # )
            
        except Exception as e:
            return Response(
                {
                    "error":"Something went wrong",
                    "details": str(e)
                }, status=status.HTTP_400_BAD_REQUEST)


    def post(self, request, user_id):
        try:
            user_obj = get_object_or_404(CustomUser, id=user_id)
            logged_user = request.user
            
            if user_obj.id == logged_user.id:
                return Response({"error": "You cannot edit your own model access rights."}, status=status.HTTP_403_FORBIDDEN)
            
            # Expecting a list of model access entries
            model_access_data = request.data
            if not isinstance(model_access_data, list) or not model_access_data:
                return Response(
                    {"error": "model_access_list must be a non-empty list."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate and create/update each record
            created_or_updated = []
            for item in model_access_data:
                model_name = item.get("model")
                if not model_name:
                    return Response(
                        {"error": "Each record must contain 'model'."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                model_obj = get_ModelName_obj_by_name(model_name)
                
                access_obj, created = ModelAccess.objects.update_or_create(
                    user=user_obj,
                    model=model_obj,
                    defaults={
                        "can_read": item.get("can_read", False),
                        "can_create": item.get("can_create", False),
                        "can_update": item.get("can_update", False),
                        "can_delete": item.get("can_delete", False),
                    }
                )
                created_or_updated.append(access_obj)
            serializer = ModelAccessSerializer(created_or_updated, many=True)
            return Response(
                {
                    "message": "Model access rights successfully updated.",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": "Something went wrong", "details": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class RecordRuleListView(APIView):
    model = RecordRule
    permission_classes = [IsAuthenticated, SystemAdminPermission, HasModelAccessPermission]

    def get(self, request):
        user_id_str = request.query_params.get("user_id", None)
        
        if user_id_str is None:
            user_obj = request.user
        else:
            try:
                user_id = int(user_id_str)
                user_obj = get_object_or_404(CustomUser, id=user_id)
            except ValueError:
                return Response(
                    {"error": "Invalid user_id format."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        record_rules = RecordRule.objects.filter(user=user_obj)
        serializer = RecordRuleListSerializer(record_rules, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
class RecordRuleView(APIView):
    model = RecordRule
    permission_classes = [IsAuthenticated, SystemAdminPermission, HasModelAccessPermission]

    def get(self, request):
        record_rule_id_str = request.query_params.get("record_rule_id", None)
        if not record_rule_id_str:
            return Response({"error": "Record rule id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            record_rule_id = int(record_rule_id_str)
            record_rule_obj = RecordRule.objects.get(id = record_rule_id)
        except ValueError:
            return Response({"error": "Invalid record_rule_id format."}, status=status.HTTP_400_BAD_REQUEST)
        except RecordRule.DoesNotExist:
            return Response({"error": "Record rule not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = RecordRuleGetSerializer(record_rule_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        user_id_str = request.query_params.get("user_id", None)
        if not user_id_str:
            return Response({"error": "User id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_id = int(user_id_str)
        except ValueError:
            return Response({"error": "Invalid user_id format."}, status=status.HTTP_400_BAD_REQUEST)
        
        user_obj = request.user
        if user_obj.id == user_id:
            return Response({"error": "You cannot set record rules for yourself."}, status=status.HTTP_403_FORBIDDEN)
        
        user_obj = get_object_or_404(CustomUser, id=user_id)
        serializer = RecordRuleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        value = validated_data.get('value')
    
        domain_filter = {
            "id__in": value
        }
        
        model_obj = validated_data.get('model')
        can_read = validated_data.get('can_read')
        can_create = validated_data.get('can_create')
        can_update = validated_data.get('can_update')
        can_delete = validated_data.get('can_delete')
        
        
        defaults = {
            "domain_filter": domain_filter,
            "name": f"{model_obj.model} Allocation",
            "can_read": validated_data.get('can_read', False),
            "can_create": validated_data.get('can_create', False),
            "can_update": validated_data.get('can_update', False),
            "can_delete": validated_data.get('can_delete', False),
        }
        
        print("defaults:", defaults)
        record_rule, created = RecordRule.objects.update_or_create(
            model=model_obj,
            user=user_obj,
            defaults=defaults
        )
        # record_rule.save()
        
        return Response(
            {
                "message": f"Record rule {'created' if created else 'updated'} successfully.",
                # "record_rule": RecordRuleSerializer(record_rule).data
            },
            status= status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
    
    def delete(self, request):
        record_rule_id_str = request.query_params.get("record_rule_id", None)
        if not record_rule_id_str:
            return Response({"error": "Record rule id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            record_rule_id = int(record_rule_id_str)
            record_rule_obj = RecordRule.objects.get(id = record_rule_id)
        except ValueError:
            return Response({"error": "Invalid record_rule_id format."}, status=status.HTTP_400_BAD_REQUEST)
        except RecordRule.DoesNotExist:
            return Response({"error": "Record rule not found."}, status=status.HTTP_404_NOT_FOUND)
        
        record_rule_obj.delete()
        return Response(
            {
                "message": "Record rule deleted successfully."
            },
            status=status.HTTP_200_OK
        )