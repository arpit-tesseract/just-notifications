from django.shortcuts import render, get_object_or_404
from functools import reduce
import operator
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
from django.db.models import Subquery


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
        residential_category = validated_data.get('residential_category')
        existing_main_user_obj = validated_data.get('existing_main_user_id')
        existing_main_user_designation_obj = validated_data.get('existing_main_user_designation')

            
        try:
            with transaction.atomic():
                higher_designation = None
                relations = []

                posts = validated_data.get('posts', None)
                response_data = []
                
                single_user = False
                if len(posts) == 1:
                    single_user = True
                    
                for index, post in enumerate(posts):
                    user_details = post.pop("user_details", None)
                    existing_user_obj = user_details.pop("user_id", None)
                    user_post_no = post.pop("post_no", None)
                    relation_between_from_and_to_obj = post.pop("relation_between_from_and_to", None)
                    user_designation_obj = post.pop("user_designation", None)
                    
                    if user_details:
                        user_role_obj = user_details.pop("user_role", None)
                        user_personal_details = user_details.pop("personal_details", None)
                        user_bussiness_details = user_details.pop("bussiness_details", None)
                        residential_details = user_details.pop('residential_details')
                        residential_details['residential_type'] = "home"
                        
                        # create residential details
                        if residential_category != "current":
                            room_details = residential_details.pop('room_details')
                            category_of_user = user_details.pop('category_of_user')
                        
                        residential_obj, created = ResidentialDetail.objects.get_or_create(**residential_details)
                        
                        if created:
                            residential_obj.pending_rooms_to_allocate = {}
                            for key, val in residential_obj.room_details.items():
                                # print("Value:",val)
                                residential_obj.pending_rooms_to_allocate[key] = val.copy()
                                residential_obj.pending_rooms_to_allocate[key]["count"] = 1
                            residential_obj.save()
                            
                                    
                        # if user_id exists in user_details then update existing user details
                        if existing_user_obj is not None:
                            # update existing user details
                            user_obj = existing_user_obj
                            for attr, value in user_details.items():
                                setattr(user_obj, attr, value)
                            user_obj.save()
                        
                        # if user_id not exists in user_details then create new user        
                        else:    
                            user_obj = CustomUser.objects.create_user(**user_details)
                        
                        # assign residential details to user
                        if existing_main_user_obj:
                            user_obj.current_residential_details = residential_obj
                        else:
                            if residential_category == "current":
                                user_obj.current_residential_details = residential_obj
                            
                            if residential_category == "owner":
                                user_obj.owner_residential_details = residential_obj
                            
                            if residential_category == "permanent":
                                user_obj.permanent_residential_details = residential_obj
                            
                            if residential_category == "native":
                                user_obj.native_residential_details = residential_obj
                                
                            if residential_category == "inlaws":
                                user_obj.inlaws_residential_details = residential_obj
                                
                            if residential_category == "maternal":
                                user_obj.maternal_residential_details = residential_obj
                                
                            if residential_category == "business":
                                user_obj.business_residential_details = residential_obj
                        
                        # save user        
                        user_obj.save()
                    
                        # add user id in response data list it's help to submit data in next form
                        response_data.append(user_obj.id)
                        
                        # add user role to user 
                        user_obj.user_role.add(user_role_obj)
                        
                        pending_relations_to_update = []
                        
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
                                    # print(user_professional_residential_details)
                                    user_professional_residential_obj, created = ResidentialDetail.objects.get_or_create(**user_professional_residential_details)
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
                        
                        # create relation between users
                        if single_user:
                            allocate_rooms_for_from_user(user_obj, residential_category)
                            user_obj.is_verified = True
                            user_obj.save()
                            return Response(
                                {
                                    "posts":[user_obj.id],
                                    "existing_main_user_id": user_obj.id,
                                    "existing_main_user_designation": relation_between_from_and_to_obj.name
                                }, status=status.HTTP_201_CREATED
                            )
                            
                        if existing_main_user_obj and existing_main_user_obj != user_obj:
                            
                            try:
                                relation_obj = Relation.objects.get(
                                    from_user = existing_main_user_obj, 
                                    relation_category = residential_category, 
                                    from_user_designation = existing_main_user_designation_obj,
                                    relation_between_from_and_to = relation_between_from_and_to_obj,
                                    to_user_designation = user_designation_obj, 
                                    to_user = user_obj,
                                    post_no = user_post_no
                                )
                            except Relation.DoesNotExist:
                                relation_obj = Relation.objects.create(
                                    from_user = existing_main_user_obj, 
                                    relation_category = residential_category, 
                                    from_user_designation = existing_main_user_designation_obj,
                                    relation_between_from_and_to = relation_between_from_and_to_obj,
                                    to_user_designation = user_designation_obj, 
                                    to_user = user_obj,
                                    post_no = user_post_no
                                )
                            except Exception as e:
                                raise ValidationError(f"Error in creating relation between {from_user} and {to_user.get('user_obj')}.")
                        # else:
                        #     print("Different")
                        #     pending_relation = {
                        #         'from_user': None,
                        #         'relation_category': residential_category,
                        #         'from_user_designation': None,
                        #         'designation': user_designation_obj,
                        #         'to_user': user_obj,
                        #         'post_no': user_post_no
                        #     }
                        #     pending_relations_to_update.append(pending_relation)
                        

                        if higher_designation is None:
                            if user_obj.expired_date is None:
                                higher_designation = relation_between_from_and_to_obj
                                
                        else:
                            if higher_designation.code > relation_between_from_and_to_obj.code and user_obj.expired_date is None:
                                higher_designation = relation_between_from_and_to_obj
                        
                                
                    relations.append(
                        {
                            'relation_category': "current" if existing_main_user_designation_obj else residential_category,
                            'relation_between_from_and_to': relation_between_from_and_to_obj,
                            'user_designation': user_designation_obj,
                            'user_obj': user_obj,
                            'post_no': user_post_no,
                        }
                    )
                
                
                from_user, from_user_designation_obj, to_users = get_from_user_and_to_users(higher_designation, relations)
                
                
                relation_obj_lst = []
                for to_user in to_users:
                    
                    try:
                        relation_obj = Relation.objects.get(
                            from_user = from_user, 
                            relation_category = to_user.get('relation_category'), 
                            from_user_designation = from_user_designation_obj,
                            relation_between_from_and_to = to_user.get('relation_between_from_and_to'), 
                            to_user_designation = to_user.get('user_designation'),
                            to_user = to_user.get('user_obj'),
                            post_no = to_user.get('post_no')
                        )
                    except Relation.DoesNotExist:
                        relation_obj = Relation.objects.create(
                            from_user = from_user, 
                            relation_category = to_user.get('relation_category'), 
                            from_user_designation = from_user_designation_obj,
                            relation_between_from_and_to = to_user.get('relation_between_from_and_to'), 
                            to_user_designation = to_user.get('user_designation'),
                            to_user = to_user.get('user_obj'),
                            post_no = to_user.get('post_no')
                        )
                    except Exception as e:
                        raise ValidationError(f"Error in creating relation between {from_user} and {to_user.get('user_obj')}.")
                    
                    relation_obj_lst.append(relation_obj)
                
                # for pending_relation in pending_relations_to_update:
                #     try:
                #         Relation.objects.update_or_create(
                #             from_user = from_user, 
                #             relation_category = pending_relation.get('relation_category'), 
                #             to_user = pending_relation.get('to_user'),
                #             defaults= { 
                #                 'from_user_designation' : from_user_designation,
                #                 'designation' : pending_relation.get('designation'), 
                #                 'post_no' : pending_relation.get('post_no')
                #             }
                #         )
                #     # except Relation.DoesNotExist:
                #     #     Relation.objects.create(
                #     #         from_user = from_user, 
                #     #         relation_category = pending_relation.get('relation_category'), 
                #     #         from_user_designation = from_user_designation,
                #     #         designation = pending_relation.get('designation'), 
                #     #         to_user = pending_relation.get('to_user'),
                #     #         post_no = pending_relation.get('post_no')
                #     #     )
                #     except Exception as e:
                #         raise ValidationError(f"Error in creating relation between {pending_relation.get('from_user')} and {pending_relation.get('to_user')}.")
                
                
                # if from_user_exists then residential != "current" so don't need to verify or room sharing logic
                if existing_main_user_obj:
                    pass
                else:
                    # 1. Process the FROM_USER
                    # if residential == "current"
                    if from_user.expired_date is None:
                        from_user.is_verified = True
                        from_user.save()
                        allocate_rooms_for_from_user(from_user, residential_category)
                    
                    # 2. Process the TO_USER (for ex: wife, son)
                    for relation_obj in relation_obj_lst:
                        mark_as_verify_or_unverify_user(relation_obj.to_user, relation_obj.relation_category)
                        
                        if relation_obj.to_user.expired_date is not None:
                            continue
                        
                        if relation_obj.to_user_designation.name == "wife" or relation_obj.to_user_designation.name == "Wife":
                            allocate_room_same_as_parent(relation_obj.to_user, relation_obj.relation_category)
                        else:
                            if relation_obj.to_user.marital_status == "single" and relation_obj.to_user_designation.name in ['son', 'daughter']:
                                allocate_room_same_as_parent(relation_obj.to_user, relation_obj.relation_category)
                            
                            if relation_obj.to_user.category_of_user == "grp_tenant":
                                allocate_rooms_for_to_user(relation_obj.to_user, relation_obj.relation_category)
                                    
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "details": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(
            {
                "posts":response_data,
                "existing_main_user_id": existing_main_user_obj.id if existing_main_user_obj else from_user.id,
                "existing_main_user_designation": existing_main_user_designation_obj.name if existing_main_user_designation_obj else from_user_designation_obj.name
            }, status=status.HTTP_201_CREATED
        )
    
    def get(self, request, **kwargs):
        user_id = request.query_params.get("user_id", "").strip()
        existing_main_user_id = request.query_params.get("existing_main_user_id", "").strip()
        residential_category = request.query_params.get("residential_category", "").strip()
        
        if residential_category is None:
            return Response(
                {
                    "error": "'residential_category' is required in query params."
                }, status=status.HTTP_400_BAD_REQUEST
            )
            
        if not user_id and residential_category in ["current", "Current"]:
            return Response(
                {
                    "error": "'user_id' is required in query params."
                }, status=status.HTTP_400_BAD_REQUEST
            )
            
        
        if not existing_main_user_id and residential_category not in ["current", "Current"]:
            return Response(
                {
                    "error": "'existing_main_user_id' is required in query params."
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        residential_context = {'residential_category': residential_category}
            
        user_obj = get_object_or_404(CustomUser, id=user_id if user_id else existing_main_user_id)
        
        # get the relations of user
        relation_obj_lst = Relation.objects.filter(
            Q(from_user=user_obj) | Q(to_user=user_obj),
            relation_category__iexact=residential_category
        )
        
        if len(relation_obj_lst) == 0:
            result = {
                "existing_main_user_id": None,
                "existing_main_user_designation": None,
                "residential_category": residential_category,
                "posts": [
                        {
                            "user_details": UserSerializerForGet(user_obj, context=residential_context).data,
                            "user_designation": "self",
                            "relation_between_from_and_to": None,
                            "post_no": None,
                        }
                    ],
            }
            return Response(result, status=status.HTTP_200_OK)
        
        main_user_relation_obj = relation_obj_lst.first()
        posts_data = []
        
        # create first post for main user
        main_user_obj = main_user_relation_obj.from_user
        if residential_category in ["current", "Current"]:
            from_user_details = UserSerializerForGet(main_user_obj, context=residential_context).data
            post = {
                "user_details": from_user_details,
                "user_designation": main_user_relation_obj.from_user_designation.name,
                "relation_between_from_and_to": None,
                "post_no": main_user_relation_obj.post_no
            }
            posts_data.append(post)
        
        
        relation_obj_lst = Relation.objects.filter(
            from_user = main_user_obj,
            relation_category__iexact= residential_category
        )
        
        for index, relation_obj in enumerate(relation_obj_lst):
            post = {
                "user_details": UserSerializerForGet(relation_obj.to_user, context=residential_context).data,
                "user_designation": relation_obj.to_user_designation.name,
                "relation_between_from_and_to": {
                    "id": relation_obj.relation_between_from_and_to.id,
                    "name": relation_obj.relation_between_from_and_to.name
                },
                "post_no": relation_obj.post_no
            }
            posts_data.append(post)
                    
        result = {
            "existing_main_user_id": main_user_obj.id,
            "existing_main_user_designation": main_user_relation_obj.from_user_designation.name,
            "residential_category": residential_category,
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


class UserSuggestionsListView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        input_serializer = UserSuggestionInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        
        validated_data = input_serializer.validated_data
        filters = []
        
        if validated_data.get('full_name'):
            filters.append(Q(full_name__icontains=validated_data.get('full_name')))
        if validated_data.get('father_name'):
            filters.append(Q(full_name__icontains=validated_data.get('father_name')))
        if validated_data.get('email'):
            filters.append(Q(email__icontains=validated_data.get('email')))
        if validated_data.get('contact_no'):
            filters.append(Q(contact_no__icontains=validated_data.get('contact_no')))
        if validated_data.get('gender'):
            filters.append(Q(gender=validated_data.get('gender')))
            
        residential_details = validated_data.get('residential_details')
        r_user_obj_list = None
        if residential_details:
            try:
                residential_obj = ResidentialDetail.objects.get(**residential_details)
                r_user_obj_list = CustomUser.objects.filter(residential_details=residential_obj)
            except ResidentialDetail.DoesNotExist:
                pass
        
        personal_details = validated_data.get('personal_details')
        p_user_obj_list = None
        if personal_details:
            try:
                # 1. Your original query to get PersonalDetail objects
                personal_obj_list = PersonalDetail.objects.filter(**personal_details)

                # 2. Get all unique user_ids from that list
                user_ids = personal_obj_list.values_list('user_id', flat=True).distinct()

                # 3. Fetch the CustomUser objects matching those IDs
                p_user_obj_list = CustomUser.objects.filter(id__in=user_ids)
            except PersonalDetail.DoesNotExist:
                pass
        else:
            return Response([], status=status.HTTP_200_OK)
        
        if not filters:
            return Response([], status=status.HTTP_200_OK)
        
        user_obj_list = CustomUser.objects.none()

        if r_user_obj_list is not None:
            user_obj_list = user_obj_list | r_user_obj_list

        if p_user_obj_list is not None:
            user_obj_list = user_obj_list | p_user_obj_list
            
        suggested_users = user_obj_list.filter(reduce(operator.and_, filters))
        response_data = UserSuggestionOutputListSerializer(suggested_users, many=True).data
        return Response(response_data, status=status.HTTP_200_OK)


class UserSuggestionsDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, user_id):
        user_obj = get_object_or_404(CustomUser, id=user_id)
        response_data = UserSuggestionOutputDetailSerializer(user_obj).data
        return Response(response_data, status=status.HTTP_200_OK)
    
    
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
        user_role = request.query_params.get('user_role', "").strip()
        if user_role:
            try:
                UserRole.objects.get(name=user_role)
            except UserRole.DoesNotExist:
                return Response({"error": "Invalid user role."}, status=status.HTTP_400_BAD_REQUEST)
            except UserRole.MultipleObjectsReturned:
                return Response(
                    {
                        "error": "Something went wrong.",
                        "details": "Multiple user roles found with the same name."
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            user_role = "user"
            
            # distinct_from_user_objs = CustomUser.objects.filter(
            #     id__in=Subquery(Relation.objects.values("from_user").distinct()),
            #     is_superuser=False,
            #     is_archive=False,
            #     user_role__name=user_role
            # )
            # serializer = UserListSerializer(distinct_from_user_objs, many=True)
            # return Response(serializer.data, status=status.HTTP_200_OK)
        
        try:
            from_user_ids = Relation.objects.values_list("from_user", flat=True).distinct()
            distinct_from_user_objs = CustomUser.objects.filter(
                is_superuser=False,
                is_archive=False,
                user_role__name=user_role   
            ).filter(
                Q(id__in=from_user_ids) | ~Q(id__in=from_user_ids)
            ).select_related(
                "current_residential_details",
                "current_residential_details__country",
                "current_residential_details__state",
                "current_residential_details__city_village"
            )
        except Exception as e:
            return Response(
                {
                    "error": "Something went wrong.",
                    "details": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        serializer = UserListSerializer(distinct_from_user_objs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserFilterationView(FilteredQuerysetMixin, APIView):
    model = CustomUser
    permission_classes = [IsAuthenticated, SystemAdminPermission]
    pagination_class = UserManagementPagination
    
    def post(self, request):
        serializer = UserFilterInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_role = request.query_params.get('user_role', "").strip()
        if user_role:
            try:
                UserRole.objects.get(name=user_role)
            except UserRole.DoesNotExist:
                return Response({"error": "Invalid user role."}, status=status.HTTP_400_BAD_REQUEST)
            except UserRole.MultipleObjectsReturned:
                return Response(
                    {
                        "error": "Something went wrong.",
                        "details": "Multiple user roles found with the same name."
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            user_role = "user"
        
        validated_data = serializer.validated_data
        residetial_details = validated_data.get('residential_details')
        personal_details = validated_data.get('personal_details')
        bussiness_details = validated_data.get('bussiness_details')
        if bussiness_details:
            professional_residetial_details = bussiness_details.get('residential_details')
        
        query = Q()
        try:
            # 1. Filter by Residential Details 
            # (Assuming you are filtering by 'current_residential_details')
            if residetial_details:
                for key, value in residetial_details.items():
                    if value is not None and value != '':
                        # Use double underscore for related field lookup
                        lookup = f"current_residential_details__{key}"
                        query &= Q(**{lookup: value})
                        
            # 2. Filter by Personal Details
            # (OneToOne relationship)
            if personal_details:
                for key, value in personal_details.items():
                    if value is not None and value != '':
                        lookup = f"personal_details__{key}"
                        query &= Q(**{lookup: value})
            
            # 3. Filter by Professional/Business Details
            # (Reverse ForeignKey relationship: CustomUser <- ProfessionalDetail)
            if bussiness_details:
                for key, value in bussiness_details.items():
                    if value is not None and value != '':
                        # Note: Django lowercases the model name for reverse lookup by default
                        # unless related_name is defined. Assuming no related_name="xyz":
                        if key == "residential_details":
                            for bkey, bvalue in professional_residetial_details.items():
                                if bvalue is not None and bvalue != '':
                                    lookup = f"professionaldetail__residential_details__{bkey}"
                                    query &= Q(**{lookup: bvalue})
                            continue
                        
                        lookup = f"professionaldetail__{key}"
                        query &= Q(**{lookup: value})
            
            # print("query:", query)
            
            # Execute Query
            from_user_ids = Relation.objects.values_list("from_user", flat=True).distinct()
            distinct_from_user_objs = CustomUser.objects.filter(
                query,
                is_superuser=False,
                is_archive=False,
                user_role__name=user_role   
            ).filter(
                Q(id__in=from_user_ids) | ~Q(id__in=from_user_ids)
            ).select_related(
                "current_residential_details",
                "current_residential_details__country",
                "current_residential_details__state",
                "current_residential_details__city_village"
            )

        except Exception as e:
            return Response(
                {
                    "error": "Something went wrong",
                    "detail": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(
            UserListSerializer(distinct_from_user_objs, many=True).data,
            status=status.HTTP_200_OK
        )
                
class ModelAccessView(APIView):
    model = ModelAccess
    permission_classes = [IsAuthenticated, SystemAdminPermission, HasModelAccessPermission]
    
    def get(self, request, user_id=None):
        # try:
        if user_id is None:
            user_obj = request.user
        else:
            user_obj = get_object_or_404(CustomUser, id=user_id)
        
        # if user_obj.id == user_obj.id:
        #     return Response({"error": "You cannot edit your own model access rights."}, status=status.HTTP_403_FORBIDDEN)
        
        # Response for super admin
        if user_obj.check_is_super_admin():
            model_access_rights = get_model_access_rights_of_super_admin()
            return Response(
                model_access_rights,
                status=status.HTTP_200_OK
            )
        
        # Response for other users
        
        # Get all available model definitions
        all_models = ModelName.objects.all()
        
        user_access_map = {
            access.model: access 
            for access in ModelAccess.objects.filter(user=user_obj)
        }
        
        response_data = []
        for model_name_obj in all_models:
            model_identifier = model_name_obj.model
            
            if model_identifier in user_access_map:
                # CASE 1: Logic found in table -> Return stored logic
                access_obj = user_access_map[model_identifier]
                response_data.append({
                    "model": model_identifier,
                    "can_read": access_obj.can_read,
                    "can_create": access_obj.can_create,
                    "can_update": access_obj.can_update,
                    "can_delete": access_obj.can_delete,
                })
            else:
                # CASE 2: Logic NOT found -> Return TRUE (As per your request)
                response_data.append({
                    "model": model_identifier,
                    "can_read": True,   # Default Allowed
                    "can_create": False, # Default Allowed
                    "can_update": False, # Default Allowed
                    "can_delete": False, # Default Allowed
                })
        
        return Response(
            response_data,
            status=status.HTTP_200_OK
        )
            
        # except Exception as e:
        #     return Response(
        #         {
        #             "error":"Something went wrong",
        #             "details": str(e)
        #         }, status=status.HTTP_400_BAD_REQUEST)


    def post(self, request, user_id=None):
        if user_id is None:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        user_obj = get_object_or_404(CustomUser, id=user_id)
        logged_user = request.user
        
        if user_obj.id == logged_user.id:
            return Response({"error": "You cannot edit your own model access rights."}, status=status.HTTP_403_FORBIDDEN)
        
        # Expecting a list of model access entries

        logged_user_perms_map = {}
        if not request.user.check_is_super_admin():
            logged_user_perms_map = {
                acc.model.model: acc 
                for acc in ModelAccess.objects.filter(user=request.user)
            }

        # print("logged_user_perms_map:", logged_user_perms_map)
        # 2. Pass context to Serializer
        serializer = ModelAccessSerializer(
            data=request.data, 
            many=True,
            context={
                'request': request, 
                'logged_user_perms_map': logged_user_perms_map,
                'target_user': user_obj
            }
        )
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        if not isinstance(validated_data, list):
            return Response(
                {"error": "model_access_list must be a list."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not validated_data:
            return Response(
                {"error": "model_access_list cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Validate and create/update each record
            
            # Extract all model names from request
            requested_model_names = [item['model'] for item in validated_data]
            
            # Create a map: "City" -> <ModelName Object>
            db_models_map = {
                m.model: m 
                for m in ModelName.objects.filter(model__in=requested_model_names)
            }
            
            for item in validated_data:
                model_str = item.get("model")

                # Skip if model doesn't exist in our DB definition
                if model_str not in db_models_map:
                    continue
                
                model_obj = db_models_map[model_str]
                read_perm = item.get("can_read", False)
                create_perm = item.get("can_create", False)
                update_perm = item.get("can_update", False)
                delete_perm = item.get("can_delete", False)
                
                if read_perm == False or True in [create_perm, update_perm, delete_perm]:
                    ModelAccess.objects.update_or_create(
                        user=user_obj,
                        model=model_obj,
                        defaults={
                            "can_read": read_perm,
                            "can_create": create_perm,
                            "can_update": update_perm,
                            "can_delete": delete_perm,
                        }
                    )
            return Response(
                {
                    "message": "Model access rights successfully updated.",
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
    
    
# class RecordRuleView(APIView):
#     model = RecordRule
#     permission_classes = [IsAuthenticated, SystemAdminPermission, HasModelAccessPermission]

#     def get(self, request):
#         record_rule_id_str = request.query_params.get("record_rule_id", None)
#         if not record_rule_id_str:
#             return Response({"error": "Record rule id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
#         try:
#             record_rule_id = int(record_rule_id_str)
#             record_rule_obj = RecordRule.objects.get(id = record_rule_id)
#         except ValueError:
#             return Response({"error": "Invalid record_rule_id format."}, status=status.HTTP_400_BAD_REQUEST)
#         except RecordRule.DoesNotExist:
#             return Response({"error": "Record rule not found."}, status=status.HTTP_404_NOT_FOUND)
        
#         serializer = RecordRuleGetSerializer(record_rule_obj)
#         return Response(serializer.data, status=status.HTTP_200_OK)
    
#     def post(self, request):
#         user_id_str = request.query_params.get("user_id", None)
#         if not user_id_str:
#             return Response({"error": "User id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
#         try:
#             user_id = int(user_id_str)
#         except ValueError:
#             return Response({"error": "Invalid user_id format."}, status=status.HTTP_400_BAD_REQUEST)
        
#         user_obj = request.user
#         if user_obj.id == user_id:
#             return Response({"error": "You cannot set record rules for yourself."}, status=status.HTTP_403_FORBIDDEN)
        
#         user_obj = get_object_or_404(CustomUser, id=user_id)
#         serializer = RecordRuleSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
        
#         validated_data = serializer.validated_data
#         value = validated_data.get('value')
    
#         domain_filter = {
#             "id__in": value
#         }
        
#         model_obj = validated_data.get('model')
#         can_read = validated_data.get('can_read')
#         can_create = validated_data.get('can_create')
#         can_update = validated_data.get('can_update')
#         can_delete = validated_data.get('can_delete')
        
        
#         defaults = {
#             "domain_filter": domain_filter,
#             "name": f"{model_obj.model} Allocation",
#             "can_read": validated_data.get('can_read', False),
#             "can_create": validated_data.get('can_create', False),
#             "can_update": validated_data.get('can_update', False),
#             "can_delete": validated_data.get('can_delete', False),
#         }
        
#         print("defaults:", defaults)
#         record_rule, created = RecordRule.objects.update_or_create(
#             model=model_obj,
#             user=user_obj,
#             defaults=defaults
#         )
#         # record_rule.save()
        
#         return Response(
#             {
#                 "message": f"Record rule {'created' if created else 'updated'} successfully.",
#                 # "record_rule": RecordRuleSerializer(record_rule).data
#             },
#             status= status.HTTP_201_CREATED if created else status.HTTP_200_OK
#         )
    
#     def delete(self, request):
#         record_rule_id_str = request.query_params.get("record_rule_id", None)
#         if not record_rule_id_str:
#             return Response({"error": "Record rule id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
#         try:
#             record_rule_id = int(record_rule_id_str)
#             record_rule_obj = RecordRule.objects.get(id = record_rule_id)
#         except ValueError:
#             return Response({"error": "Invalid record_rule_id format."}, status=status.HTTP_400_BAD_REQUEST)
#         except RecordRule.DoesNotExist:
#             return Response({"error": "Record rule not found."}, status=status.HTTP_404_NOT_FOUND)
        
#         record_rule_obj.delete()
#         return Response(
#             {
#                 "message": "Record rule deleted successfully."
#             },
#             status=status.HTTP_200_OK
#         )


class RecordRuleView(APIView):
    permission_classes = [IsAuthenticated, SystemAdminPermission, HasModelAccessPermission]
    
    def get(self, request):
        user_id_str = request.query_params.get("user_id", None)
        if not user_id_str:
            return Response({"error": "User id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_id = int(user_id_str)
            record_rule_objs = RecordRule.objects.filter(user=user_id)
        except ValueError:
            return Response({"error": "Invalid record_rule_id format."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = RecordRuleGetSerializer(record_rule_objs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        if not isinstance(request.data, list):
            return Response({"error": "Expected a list of model objects."}, status=status.HTTP_400_BAD_REQUEST)

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
        serializer = RecordRuleCreateSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                deletions_occurred = False
                last_create_update_status = None # Will be True (created) or False (updated)
                
                # Handle empty list
                if len(serializer.validated_data) == 0:
                    return Response(
                        {"message": "No record rules to process."}, 
                        status=status.HTTP_200_OK
                    )
                    
                for item in serializer.validated_data:
                    model_name = item.get('model')
                    model_obj = item.get('model_obj')
                    model_ids = item.get('values') # e.g., {"1": {perms}, "2": {perms}}
                    
                    # Construct the filter strictly for this ID
                    if model_ids is None:
                        try:
                            record_rule_obj = RecordRule.objects.get(user=user_obj, model=model_obj)
                            record_rule_obj.delete()
                            deletions_occurred = True
                        except RecordRule.DoesNotExist:
                            pass
                        except Exception as e:
                            pass
                        continue
                        
                    domain_filter = {
                        'id__in': model_ids
                    }
                    # Use update_or_create for cleaner logic
                    record_rule_obj, created =RecordRule.objects.update_or_create(
                        model=model_obj,
                        user=user_obj,
                        defaults={
                            "name": f"{model_obj.model} Allocation",
                            "domain_filter": domain_filter,
                            "can_read": True,
                            "can_create": True,
                            "can_update": True,
                            "can_delete": True,
                        }
                    )
                    last_create_update_status = created
                    
                    # For Continent Model
                    # if model_name == "Continent":
                    #     glob_ids = []
                    #     select_path = (
                    #         "glob"
                    #     )       
                    #     qs = Continent.objects.filter(id__in=model_ids).select_related(select_path)
                        
                    #     for continent_obj in qs:
                    #         glob_id = continent_obj.glob.id
                    #         if glob_id not in glob_ids:
                    #             glob_ids.append(glob_id)
                                
                    #     # Use update_or_create for cleaner logic
                    #     glob_model_obj = get_ModelName_obj_by_name("Glob")
                    #     domain_filter = {
                    #         'id__in': glob_ids
                    #     }
                    #     RecordRule.objects.update_or_create(
                    #         model=glob_model_obj,
                    #         user=user_obj,
                    #         defaults={
                    #             "name": f"{glob_model_obj.model} Allocation",
                    #             "domain_filter": domain_filter,
                    #             "can_read": True,
                    #             "can_create": True,
                    #             "can_update": True,
                    #             "can_delete": True,
                    #         }
                    #     )
            if last_create_update_status is not None:
                if last_create_update_status: # True means created
                        flag = "created"
                        response_status = status.HTTP_201_CREATED
                else: # False means updated
                    flag = "updated"
                    response_status = status.HTTP_200_OK
                
                return Response(
                    {"message": f"Record rules {flag} successfully."}, 
                    status=response_status
                )
                    
            if deletions_occurred:
                # No create/update happened, but deletions did occur.
                return Response(
                    {"message": "Record rules deleted successfully."}, 
                    status=status.HTTP_200_OK # 200 OK is standard for a successful delete
                )

        except Exception as e:
            return Response(
                {
                    "error": "Something went wrong while creating record rules.",
                    "details": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PersonalDetailsGetView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user_id = request.query_params.get("user_id", "").strip()
        if user_id == "":
            return Response(
                {"error": "'user_id' is required in query params."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        personal_details_obj = get_object_or_404(PersonalDetail, user_id=user_id)
        serializer = PersonalDetailGetSerializer(personal_details_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BussinessDetailsGetView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user_id = request.query_params.get("user_id", "").strip()
        if user_id == "":
            return Response(
                {"error": "'user_id' is required in query params."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        professional_details_obj = get_object_or_404(ProfessionalDetail, user_id=user_id)
        bussiness_details_output = BussinessDetailsGetSerializer(professional_details_obj).data
        return Response(bussiness_details_output, status=status.HTTP_200_OK)


class ResidentialDetailsGetView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user_id = request.query_params.get("user_id", "").strip()
        if user_id == "":
            return Response(
                {"error": "'user_id' is required in query params."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_obj = get_object_or_404(CustomUser, id=user_id)
        residential_details_output = ResidentialDetailGetSerializer(user_obj.current_residential_details).data
        return Response(residential_details_output, status=status.HTTP_200_OK)

class GetSearchKeyView(APIView):
    permission_classes = [IsAuthenticated]
    
    PARENT_FIELD = {
        "room": "house",
        "house": "floor",
        "floor": "block",
        "block": "society",
        "society": "ward",
        "ward": "city_village",
        "city_village": "taluka",
        "taluka": "district",
        "district": "state",
        "state": "country",
        "country": "continent",
        "continent": "glob",
        "glob": None
    }
    
    MODEL_MAP = {
        "glob": Glob,
        "continent": Continent,
        "country": Country,
        "state": State,
        "district": District,
        "taluka": Taluka,
        "city_village": CityVillage,
        "ward": Ward,
        "society": Society,
        "block": Block,
        "floor": Floor,
        "house": House,
        "room": Room,
    }
    
    def build_chain(self, obj):
        print("function called")
        chain_items = []
        current = obj
        
        print("current:", current)
        
        while current:
            model_name = current.__class__.__name__  # e.g. Country
            key = model_name.lower()

            if model_name == "CityVillage":
                key = "city_village"

            chain_items.append(
                (key, {"id": current.id, "name": current.name})
            )
            
            print(chain_items)
            
            parent_field = self.PARENT_FIELD[key]
            # fun will break when parent_field = None
            if not parent_field: # "glob"
                break
            
            # for eg current = Country object
            current = getattr(current, parent_field)    # current = current.continent
            print("current - 2:", current)
        
        chain_items.reverse()
        return dict(chain_items)
    
    def get_hierarchy(self, search_key, record_rules):
        # Find record rule for this level
        rule = record_rules.filter(model__model__iexact=search_key.capitalize()).first()
        if not rule:
            return []

        ids = rule.domain_filter.get("id__in", [])
        if not ids:
            return []

        model_class = self.MODEL_MAP[search_key]
        objs = model_class.objects.filter(id__in=ids)

        # call function for each objects
        # for eg objs = [country1, country2, country3], then function will be called 3 times
        return [self.build_chain(obj) for obj in objs]
    

    def get(self, request):
        logged_user = request.user
        
        # Model priority (lowest first)
        LEVEL_ORDER = [
            "room",
            "house",
            "floor",
            "block",
            "society",
            "ward",
            "city_village",
            "taluka",
            "district",
            "state",
            "country",
            "continent",
            "glob",
        ]
        
        # Mapping between db model name → search_key
        MODEL_MAP = {
            "Glob": "glob",
            "Continent": "continent",
            "Country": "country",
            "State": "state",
            "District": "district",
            "Taluka": "taluka",
            "CityVillage": "city_village",
            "Ward": "ward",
            "Society": "society",
            "Block": "block",
            "Floor": "floor",
            "House": "house",
            "Room": "room",
        }

        record_rules = RecordRule.objects.filter(user=logged_user)

        # No rules → return blank
        if not record_rules.exists():
            return Response({"search_key": ""}, status=status.HTTP_200_OK)

        # Must have Glob access, otherwise deny
        if not record_rules.filter(model__model="Glob").exists():
            return Response({"search_key": ""}, status=status.HTTP_200_OK)

        # Get list of model names assigned to user
        assigned_model_names = list(record_rules.values_list("model__model", flat=True))
        print("assigned_model_names:", assigned_model_names)
        
        # Convert assigned models to search keys
        assigned_levels = {MODEL_MAP[m] for m in assigned_model_names}
        print("assigned_levels:", assigned_levels)

        # Select the lowest level user has
        for level in LEVEL_ORDER:
            if level in assigned_levels:
                hierarchy = self.get_hierarchy(level, record_rules)
                return Response(
                    {
                        "search_key": level,
                        "hierarchy": hierarchy
                    }, status=status.HTTP_200_OK)

        # Fallback (should not happen)
        return Response({"search_key": ""}, status=status.HTTP_200_OK)