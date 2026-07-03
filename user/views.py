from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction, IntegrityError
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from django.db.models.expressions import RawSQL
import re
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken


from configuration.mixins import AssignedNodeFilterMixin
from .mixins import AdminRoleFilterMixin
from common.pagination import CommonPagination
from .serializers import (
    LoginInputSerializer,UserBasicDetailsOutputSerializer, LogoutInputSerializer,
    ResidentialTypeDropdownSerializer, DocumentTypeDropdownSerializer, RelationTypeDropdownSerializer, DesignationTypeDropdownSerializer,
    BusinessFamilyDropdownSerializer, BussinessFamilyDetailsOutputSerializer,
    UserSuggestionDropdownSerializer, UserDetailsOutputSerializer,
    RegistrationInputSerializer, RegistrationOutputSerializer, UserListSerializer, LoginPhoneInputSerializer,LoginPhoneOTPInputSerializer,
    BusienssRegistrationInputSerializer, RoleDropdownSerializer,
    BusinessMemberPayloadSuggestionSerializer, BusinessRegisterOutputSerializer
)
from .models import *
from .utils import (map_family_internal_relations, map_relations_with_husband_user, build_family_tree, build_family_tree_by_pidhi, get_or_create_residential_details)
# Create your views here.

class LoginOTPView(APIView):
    def post(self,request):
        serializer_obj = LoginPhoneInputSerializer(data = request.data)

        if serializer_obj.is_valid():
            contact_no = serializer_obj.validated_data.get('contact_no')
            try:
                user_obj = User.objects.get(contact_no = contact_no)
            except User.DoesNotExist:
                message = {
                    'error' : 'User does not exsist'
                }
                return Response(message,status=status.HTTP_400_BAD_REQUEST)
            
            message = {
                'success' : 'otp sent successfully'
            }
            return Response(message, status=status.HTTP_200_OK)
        return Response(serializer_obj.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginPhoneOTPView(APIView):
    def post(self,request):
        serializer_obj = LoginPhoneOTPInputSerializer(data=request.data)
        if serializer_obj.is_valid():
            contact_no = serializer_obj.validated_data.get('contact_no')
            otp = serializer_obj.validated_data.get('otp')
            try:
                user_obj = User.objects.get(contact_no = contact_no)
            except User.DoesNotExist:
                message = {
                    'error' : 'User does not exsist'
                }
                return Response(message,status=status.HTTP_400_BAD_REQUEST)    
            if otp ==   1234:
                    
                refresh = RefreshToken.for_user(user_obj)
                serializer_obj = UserBasicDetailsOutputSerializer(user_obj)
                return Response(
                                {   
                                    'message' : "Login successfully",
                                    "refresh": str(refresh),
                                    "access": str(refresh.access_token),
                                    "user": serializer_obj.data
                                },
                            status=status.HTTP_200_OK)
            else:
                return Response(
                    {
                        "error" : 'Invalid otp'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer_obj.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        serializer = LoginInputSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        email = validated_data.get('email').strip()
        password = validated_data.get('password')
            
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Wrong Email or password"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.is_verified:
            return Response(
                {
                    "error": "Your account is not verified"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.check_password(password):
            return Response(
                {"error": "Wrong Email or password"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        refresh = RefreshToken.for_user(user)
        serializer = UserBasicDetailsOutputSerializer(user)
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


class RegistrationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        input_serializer = RegistrationInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        validated_data = input_serializer.validated_data

        registration_type = validated_data.get('registration_type')
        registration_user = validated_data.get('registration_user')
        user_category = validated_data.get('user_category')
        residential_type = validated_data.get('residential_type')
        residential_details_json = validated_data.get('residential_details')
        stay_from = validated_data.get('stay_from')
        stay_to = validated_data.get('stay_to')
        company_name = validated_data.get("company")
        family_members = validated_data.get('family_members')

        if residential_type.name != "current" and not registration_user:
            return Response({
                "registration_user": "This field is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Residential Details
        # residential_obj = None
        # if residential_details_json:
        #     residential_obj, _ = ResidentialDetails.objects.get_or_create(
        #         nodes=residential_details_json
        #     )
        
        residential_obj, _ = get_or_create_residential_details(residential_details_json)

        with transaction.atomic():
            created_users = []
            created_user_ids = []
            main_user_obj = None
            main_user_residential_obj = None
            husband_user = None            
            business_family_obj = None

            for member in family_members:
                personal_details_json = member.pop('personal_details', {})
                professional_details_lst = member.pop('professional_details', [])
                existing_user_obj = member.pop('user_id')
                relation_obj = member.pop('relation')

                self_relation = member.pop('self_relation', None)
                self_designation = member.pop('self_designation', None)

                if self_relation:
                    try:
                        self_relation_type_obj = RelationType.objects.get(name=self_relation)
                    except RelationType.DoesNotExist:
                        raise ValidationError({
                            "self_relation": "Invalid self relation."
                        })

                # User details
                full_name = member.pop('full_name')
                email = member.pop('email', None)
                contact_no = member.pop('contact_no')
                post_no = member.pop('post_no', None)

                user_defaults = {
                    "full_name": full_name,
                    "email": email,
                    "contact_no": contact_no,
                    "user_category": user_category,
                }

                if existing_user_obj:
                    user_obj, _ = User.objects.update_or_create(
                        id=existing_user_obj.id,
                        defaults=user_defaults
                    )
                    
                else:                        
                    user_obj = User.objects.create(
                        full_name = full_name,
                        email = email,
                        contact_no = contact_no,
                        user_category = user_category,
                    )
                
                if residential_type.name == "current" and registration_type == "resident":
                    user_obj.is_verified = True

                user_obj.current_residential_details = residential_obj
                
                user_obj.save()

                role, _ = UserRole.objects.get_or_create(
                    name="user",
                    display_name="User"
                )
                user_obj.roles.add(role)

                # User Profile update or create
                user_profile_obj, _ = UserProfile.objects.update_or_create(
                    user = user_obj,
                    defaults=member
                )
                

                # Personal Details
                # user_personal_obj, _ = UserPersonalDetails.objects.update_or_create(
                #     user = user_obj,
                #     defaults={
                #         'nodes': personal_details_json
                #     }
                # )

                try:
                    user_personal_obj = UserPersonalDetails.objects.get(user=user_obj)
                except UserPersonalDetails.DoesNotExist:
                    user_personal_obj = UserPersonalDetails.objects.create(
                        user = user_obj
                    )
                
                # Bulk create mapping for personal details
                user_personal_obj.node_mappings.all().delete()
                personal_mappings_to_create = []
                for level_id, node_id in personal_details_json.items():
                    if level_id and node_id:
                        personal_mappings_to_create.append(
                            PersonalNodeMapping(
                                personal_detail=user_personal_obj, level_id=int(level_id), node_id=int(node_id)
                            )
                        )
                if personal_mappings_to_create:
                    PersonalNodeMapping.objects.bulk_create(personal_mappings_to_create)
                
                print("professional_details_lst", professional_details_lst)
                for professional_details in professional_details_lst:
                    company_name = professional_details.get('company')
                    residential_nodes = professional_details.get('residential_details', {})

                    bussiness_residential_obj, _ = get_or_create_residential_details(residential_nodes)

                    try:
                        temp_resident_mapping_obj = ResidentMapping.objects.get(
                            residential_details=bussiness_residential_obj,
                            residential_type__name="business",
                            business_family__name__iexact=company_name
                        )
                        business_family_obj = temp_resident_mapping_obj.business_family
                    except ResidentMapping.DoesNotExist:
                        business_family_obj = BusinessFamily.objects.create(name=company_name)
                        business_residential_type_obj = ResidentialType.objects.get(name="business")

                        ResidentMapping.objects.create(
                            residential_details=bussiness_residential_obj,
                            residential_type=business_residential_type_obj,
                            business_family=business_family_obj
                        )
                    


                    designation_obj = professional_details.get('designation')
                    personal_nodes = professional_details.get('personal_details', {})
                    professional_nodes = professional_details.get('professional_details', {})
                    profession_id = professional_details.get('id', None)
                    is_active = professional_details.get('is_active', True)
                    
                    if profession_id:
                        try:
                            professional_details_obj = UserProfessionalDetails.objects.get(
                                id=profession_id,
                                user=user_obj
                            )
                            professional_details_obj.business_family = business_family_obj
                            professional_details_obj.residential_details = bussiness_residential_obj
                            professional_details_obj.designation = designation_obj
                            professional_details_obj.is_active = is_active
                            professional_details_obj.save()
                        except UserProfessionalDetails.DoesNotExist:
                            raise ValidationError({
                                "error": "Professional details not found"
                            })

                    else:
                        professional_details_obj = UserProfessionalDetails.objects.create(
                            user=user_obj,
                            business_family = business_family_obj,
                            residential_details=bussiness_residential_obj,
                            designation=designation_obj,
                            is_active=is_active
                        )
                        
                    # Delete and recreate professional mappings
                    professional_details_obj.professional_node_mappings.all().delete()
                    prof_mappings_to_create = []
                    for level_id, node_id in professional_nodes.items():
                        if level_id and node_id:
                            prof_mappings_to_create.append(ProfessionalNodeMapping(
                                professional_detail=professional_details_obj, level_id=int(level_id), node_id=int(node_id)
                            ))
                    if prof_mappings_to_create:
                        ProfessionalNodeMapping.objects.bulk_create(prof_mappings_to_create)

                    # Delete and recreate professional personal mappings
                    professional_details_obj.personal_node_mappings.all().delete()
                    prof_pers_mappings_to_create = []
                    for level_id, node_id in personal_nodes.items():
                        if level_id and node_id:
                            prof_pers_mappings_to_create.append(ProfessionalPersonalNodeMapping(
                                professional_detail=professional_details_obj, level_id=int(level_id), node_id=int(node_id)
                            ))
                    if prof_pers_mappings_to_create:
                        ProfessionalPersonalNodeMapping.objects.bulk_create(prof_pers_mappings_to_create)
                    
                    # Create members for this bussiness 
                    business_family_member_obj, _ = BusinessFamilyMember.objects.get_or_create(
                        business_family = business_family_obj,
                        user = user_obj,
                        self_designation_type = designation_obj
                    )

                if self_relation == "husband":
                    husband_user = user_obj

                # Add to created users
                created_users.append(
                    {
                        "user": user_obj,
                        "self_relation_type": self_relation_type_obj if self_relation else None,
                        "self_designation_type": self_designation,
                        "personal_details": user_personal_obj,
                        "relation": relation_obj,
                        "post_no": post_no,
                    }
                )
                created_user_ids.append(user_obj.id)

                if main_user_obj is None and self_relation == 'husband' and member.get('expired_date') is None:
                    main_user_obj = user_obj
                    main_user_residential_obj = residential_obj

                elif main_user_obj is None and self_relation == 'wife' and member.get('expired_date') is None:
                    main_user_obj = user_obj
                    main_user_residential_obj = residential_obj


            if not main_user_obj and residential_type.name != "business":
                raise ValidationError({
                    "error": "Main user not found"
                })
            
            if residential_type.name == "current":
                registration_user = main_user_obj
             
                main_user_family_member_obj = FamilyMember.objects.filter(
                    user = main_user_obj,
                    is_main_user = True
                ).first()

                if main_user_family_member_obj:
                    family_obj = main_user_family_member_obj.family
                else:
                    family_obj = Family.objects.create(
                    )

                family_name = ""
                for user in created_users:
                    user_obj = user.get("user")
                    FamilyMember.objects.get_or_create(
                        family = family_obj,
                        user = user_obj,
                        self_relation_type = user.get("self_relation_type"),
                        post_no = user.get("post_no"),
                        is_main_user = user_obj.id == main_user_obj.id
                    )
                    family_name += user_obj.full_name[0].upper()
                
                family_obj.name = family_name
                family_obj.save()
                
                registration_user_family_obj = family_obj

                try:
                    with transaction.atomic():
                        family_resident_obj, _ = ResidentMapping.objects.update_or_create(
                            family = family_obj,
                            residential_type = residential_type,
                            defaults={
                                'residential_details': residential_obj,
                                'stay_from': stay_from,
                                'stay_to': stay_to
                            }
                        )
                except IntegrityError:
                    raise ValidationError({
                        "residential_details": "For this residential details a family already exists."
                    })
                
            elif residential_type.name == "business":
                for user in created_users:
                    user_obj = user.get("user")
                    self_designation_type = user.get("self_designation_type")

                    try:
                        temp_resident_mapping_obj = ResidentMapping.objects.get(
                            residential_details=residential_obj,
                            residential_type=residential_type,
                            business_family__name__iexact=company_name
                        )
                        business_family_obj = temp_resident_mapping_obj.business_family
                        business_family_obj.is_verified = registration_type == "corporate"
                        business_family_obj.save()

                    except ResidentMapping.DoesNotExist:
                        business_family_obj = BusinessFamily.objects.create(
                            name = company_name, 
                            is_verified = registration_type == "corporate"
                        )

                        ResidentMapping.objects.create(
                            residential_details=residential_obj,
                            residential_type=residential_type,
                            business_family=business_family_obj,
                            stay_from=stay_from,
                            stay_to=stay_to
                        )

                    business_family_member_obj, _ = BusinessFamilyMember.objects.get_or_create(
                        business_family = business_family_obj,
                        user = user_obj,
                        self_designation_type = self_designation_type
                    )
                    
            else:
                print("created users", created_users)
                current_residential_type_obj = ResidentialType.objects.get(name="current")

                main_user_family_members = FamilyMember.objects.filter(
                    user = main_user_obj,
                    is_main_user = True
                )

                if main_user_family_members.exists():
                    main_user_family_obj = main_user_family_members.first().family
                else:
                    main_user_family_obj = Family.objects.create(
                    )

                family_name = ""
                for user in created_users:
                    user_obj = user.get("user")
                    member = FamilyMember.objects.get_or_create(
                        family = main_user_family_obj,
                        user = user_obj,
                        self_relation_type = user.get("self_relation_type"),
                        is_main_user = user_obj.id == main_user_obj.id
                    )
                    family_name += user_obj.full_name[0].upper()
                    
                    print("member", member)
                    main_user_family_obj.name = family_name
                    main_user_family_obj.save()

                registration_user_family_member_obj = FamilyMember.objects.filter(
                    user = registration_user,
                    is_main_user = True
                ).first()

                if not registration_user_family_member_obj:
                    raise ValidationError({
                        "error": "Registration Family not found"
                    })
                
                registration_user_family_obj = registration_user_family_member_obj.family


                # 1. Check for Main User Family Resident
                try:
                    with transaction.atomic():
                        family_resident_obj, created = ResidentMapping.objects.update_or_create(
                            family=main_user_family_obj,
                            residential_type=current_residential_type_obj,
                            defaults={
                                'residential_details': main_user_residential_obj,
                                'stay_from': stay_from,
                                'stay_to': stay_to
                            }
                        )
                except IntegrityError:
                    raise ValidationError({
                        "residential_details": "For this residential details a family already exists."
                    })

                # 2. Check for Registration User Family Resident
                try:
                    with transaction.atomic():
                        registration_resident_obj, created = ResidentMapping.objects.update_or_create(
                            family=registration_user_family_obj,
                            residential_type=residential_type,
                            defaults={
                                'residential_details': main_user_residential_obj,
                                'stay_from': stay_from,
                                'stay_to': stay_to
                            }
                        )
                except IntegrityError:
                    raise ValidationError({
                        "residential_details": "For this residential details a family already exists."
                    })
            
            # Map family internal relations
            if residential_type.name != "business":
                map_family_internal_relations(created_users)

                # Map relations, native, inlaws, maternal
                map_relations_with_husband_user(registration_user_family_obj, created_users)
            
        
        # return Response({
        #     "message": "User created successfully",
        #     "registration_user": registration_user.id if registration_user else None,
        #     "main_user": main_user_obj.id if main_user_obj else None,
        #     "user_ids": created_user_ids
        # }, status=status.HTTP_201_CREATED)

        # --- NEW: Serialize and return the created data ---
        if residential_type.name == "business":
            target_instance = business_family_obj
        else:
            target_instance = registration_user_family_obj

        # Use the exact same serializer and context as your GET request
        serializer = RegistrationOutputSerializer(
            target_instance,
            context={
                "residential_type": residential_type,
                "registration_user": registration_user,
                "residential_details": residential_obj
            }
        )

        # Optional: You can wrap the serialized data with your success message and user_ids
        # so the frontend still gets everything it expects.
        response_data = {
            "message": "User created successfully",
            "registration_user": registration_user.id if registration_user else None,
            "main_user": main_user_obj.id if main_user_obj else None,
            "user_ids": created_user_ids,
            "data": serializer.data  # <--- The full GET response is now embedded here
        }

        return Response(response_data, status=status.HTTP_201_CREATED)
    

    def get(self, request):
        user_id = request.query_params.get("user_id", "").strip()
        residential_type = request.query_params.get("residential_type", "current").strip()
        registration_user = request.query_params.get("registration_user", "").strip()

        # user_id param validation
        if not user_id and not registration_user:
            return Response({
                "user_id": "This param is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if user_id:
            if user_id.isdigit():
                user_id = int(user_id)
            else:
                return Response({
                    "user_id": "Invalid user id format"
                }, status=status.HTTP_400_BAD_REQUEST)
            user_obj = get_object_or_404(User, id=user_id)

        # registration_user param validation
        if registration_user:
            if registration_user.isdigit():
                registration_user = int(registration_user)
            else:
                return Response({
                    "registration_user": "Invalid registration_user id format"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                registration_user_obj = User.objects.get(id=registration_user)
            except User.DoesNotExist:
                return Response({
                    "registration_user": "Invalid registration_user id"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # registration_user_obj = get_object_or_404(User, id=registration_user)
            print("registration_user_obj:", registration_user_obj)
        else:
            registration_user_obj = None
        
        # residential_type param validation
        try: 
            residential_type_obj = ResidentialType.objects.get(name=residential_type)
        except ResidentialType.DoesNotExist:
            return Response({
                "error": "Something went wrong. Please try again.",
                "details": "Invalid residential_type"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if residential_type != "current" and not registration_user_obj:
            return Response({
                "error": "Something went wrong. Please try again.",
                "details": "registration_user is required when residential_type is not 'current'"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if registration_user_obj and residential_type != "business":
            try:
                family_member_obj = FamilyMember.objects.get(user=registration_user_obj, is_main_user=True)
                family_obj = family_member_obj.family

                try:
                    residential_obj = ResidentMapping.objects.get(family=family_obj, residential_type=residential_type_obj).residential_details
                except ResidentMapping.DoesNotExist:
                    return Response({
                        "error": "Something went wrong. Please try again.",
                        "details": "Residential details not found"
                    }, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    return Response({
                        "error": "Something went wrong. Please try again.",
                        "details": str(e)
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    family_obj = ResidentMapping.objects.get(residential_details=residential_obj, residential_type__name="current").family
                except ResidentMapping.DoesNotExist:
                    return Response({
                        "error": "Something went wrong. Please try again.",
                        "details": "Family not found"
                    }, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    return Response({
                        "error": "Something went wrong. Please try again.",
                        "details": str(e)
                    }, status=status.HTTP_400_BAD_REQUEST)
                
            except FamilyMember.DoesNotExist:
                return Response({
                    "error": "Something went wrong. Please try again.",
                    "details": "Family member not found"
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer = RegistrationOutputSerializer(
                family_obj,
                context = {
                    "residential_type": residential_type_obj,
                    "registration_user": registration_user_obj,
                    "residential_details": residential_obj
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        

        if registration_user_obj and residential_type == "business":
            try:
                family_member_obj = BusinessFamilyMember.objects.get(
                    business_family__is_verified=True,
                    user=registration_user_obj, 
                    is_active=True
                )
            except BusinessFamilyMember.DoesNotExist:
                try:
                    family_member_obj = BusinessFamilyMember.objects.get(
                    user=registration_user_obj, 
                    is_active=True
                )
                except BusinessFamilyMember.DoesNotExist:
                    return Response({
                        "error": "Something went wrong. Please try again.",
                        "details": "Family member not found"
                })

                business_family_obj = family_member_obj.business_family
                try:
                    business_residential_obj = ResidentMapping.objects.get(business_family=business_family_obj, residential_type=residential_type_obj).residential_details
                except ResidentMapping.DoesNotExist:
                    return Response({
                        "error": "Something went wrong. Please try again.",
                        "details": "Residential details not found"
                    }, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    return Response({
                        "error": "Something went wrong. Please try again.",
                        "details": str(e)
                    }, status=status.HTTP_400_BAD_REQUEST)
            

            serializer = RegistrationOutputSerializer(
                business_family_obj,
                context = {
                    "residential_type": residential_type_obj,
                    "registration_user": registration_user_obj,
                    "residential_details": business_residential_obj
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
                

        

        # Get all family members whis has user == user_id
        family_member_qs = FamilyMember.objects.filter(user=user_obj)
        if not family_member_qs.exists():
            return Response({
                "error": "Something went wrong. Please try again.",
                "details": "Family members not found"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        family_member_obj = family_member_qs.filter(is_main_user=True).first()

        # First priority if it's main user then fetch thier family
        if family_member_obj:
            family_obj = family_member_obj.family
        else:
            # If not then fetch family whis has user == user_id
            family_member_obj = family_member_qs.first()
            if family_member_obj:
                family_obj = family_member_obj.family
            else:
                return Response({
                    "error": "Something went wrong. Please try again."
                }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            residential_obj = ResidentMapping.objects.get(family=family_obj, residential_type=residential_type_obj).residential_details
        except ResidentMapping.DoesNotExist:
            return Response({
                "error": "Something went wrong. Please try again.",
                "details": "Residential details not found"
        }, status=status.HTTP_400_BAD_REQUEST)

        if not registration_user:
            registration_user_obj = family_obj.members.filter(is_main_user=True).first().user    
            
        serializer = RegistrationOutputSerializer(
            family_obj,
            context = {
                "residential_type": residential_type_obj,
                "registration_user": registration_user_obj,
                "residential_details": residential_obj
            }
        )
        return Response(serializer.data, status=status.HTTP_200_OK)



class ResidentialTypeDropdownView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role_name = request.query_params.get('role', 'user').strip()
        residential_type_qs = ResidentialType.objects.filter(is_active=True, roles__name=role_name)
        serializer = ResidentialTypeDropdownSerializer(residential_type_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DocumentTypeDropdownView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        document_type_qs = DocumentType.objects.filter(is_active=True)
        serializer = DocumentTypeDropdownSerializer(document_type_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MultiUserDocumentUploadView(APIView):
    # CRITICAL: Restrict to admins so users can't upload to other people's profiles
    permission_classes = [IsAuthenticated] 
    parser_classes = [MultiPartParser, FormParser]

    # Note: user_id is removed from here since it comes from the payload now
    def post(self, request): 
        data = request.data

        # The new pattern!
        pattern = re.compile(r'users\[(\d+)\]\[documents\]\[(\d+)\]\[(\w+)\]')
        
        # Structure will be: { user_id: { doc_type_id: { field: value } } }
        parsed_data = {} 

        # Step 1: Parse mapped FormData
        for key, value in data.items():
            match = pattern.match(key)
            if match:
                user_id, doc_type_id, field = match.groups()

                try:
                    user_id = int(user_id)
                    doc_type_id = int(doc_type_id)
                except ValueError:
                    # If it can't be converted to a number, reject the request safely!
                    return Response({
                        "error": f"Invalid format in key '{key}'. The User ID and Document ID must be pure numbers (e.g., 1, 2)."
                    }, status=400)
                

                # Build the nested dictionary safely
                if user_id not in parsed_data:
                    parsed_data[user_id] = {}
                if doc_type_id not in parsed_data[user_id]:
                    parsed_data[user_id][doc_type_id] = {}

                parsed_data[user_id][doc_type_id][field] = value

        if not parsed_data:
            return Response({"error": "No documents provided"}, status=400)

        # created_ids = []
        errors = []

        # Step 2: Validate + Save
        with transaction.atomic():
            
            # Loop through Users first
            for user_id, user_docs in parsed_data.items():
                
                # Verify User Exists
                try:
                    user_obj = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    errors.append({f"users[{user_id}]": "User not found"})
                    continue

                # Loop through the Documents for this specific User
                for doc_type_id, doc in user_docs.items():
                    
                    # Create a standard error key so the frontend knows exactly where it failed
                    err_key = f"users[{user_id}][documents][{doc_type_id}]"

                    file = doc.get("document")
                    document_no = doc.get("document_no")

                    try:
                        document_type = DocumentType.objects.get(
                            id=doc_type_id,
                            is_active=True
                        )
                    except DocumentType.DoesNotExist:
                        errors.append({err_key: "Invalid document_type"})
                        continue

                    # --- NEW: Check for deletion flag FIRST ---
                    # form data sends strings, so check for 'true' or '1'
                    is_deleted_str = str(doc.get("is_deleted", "")).lower()
                    is_deleted = is_deleted_str in ['true', '1', 'yes']

                    if is_deleted:
                        if document_type.name == "photo":
                            try:
                                user_profile_obj = UserProfile.objects.get(user=user_obj)
                                # Delete the actual file from storage (optional but recommended)
                                if user_profile_obj.photo:
                                    user_profile_obj.photo.delete(save=False) 
                                user_profile_obj.photo = None
                                user_profile_obj.save()
                            except UserProfile.DoesNotExist:
                                pass
                        else:
                            # Delete the record from the database
                            docs_to_delete = UserDocument.objects.filter(
                                user=user_obj, 
                                document_type=document_type
                            )
                            # Loop to ensure file signals fire and files are removed from storage
                            for d in docs_to_delete:
                                d.soft_delete(user=request.user)
                        
                        # Move to the next document, do not process file uploads
                        continue 

                    # Regex Validation for document_no
                    if document_type.regex_pattern and document_no:
                        if not re.match(document_type.regex_pattern, document_no):
                            error_msg = document_type.regex_error_message or f"Invalid format for {document_type.display_name}."
                            errors.append({err_key: error_msg})
                            continue

                    # File required Validation
                    if not file:
                        errors.append({err_key: "File is required"})
                        continue

                    # Prevent crash if the frontend sends text instead of a physical file object
                    if not hasattr(file, 'name'):
                        errors.append({err_key: "Invalid file format uploaded"})
                        continue
                    
                    # Cleaner extension validation using a tuple
                    ALLOWED_EXTENSIONS = (".pdf", ".jpg", ".jpeg", ".png")
                    file_name = file.name.lower()

                    if document_type.name == "photo":
                        ALLOWED_EXTENSIONS = (".jpg", ".jpeg", ".png")

                    if not file_name.endswith(ALLOWED_EXTENSIONS):
                        errors.append({
                            err_key: f"Invalid extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
                        })
                        continue

                    # Save
                    if document_type.name == "photo":
                        try:
                            user_profile_obj = UserProfile.objects.get(user=user_obj)
                            user_profile_obj.photo = file
                            user_profile_obj.save()
                        except UserProfile.DoesNotExist:
                            pass
                    else:            
                        obj, _ = UserDocument.objects.update_or_create(
                            user=user_obj,
                            document_type=document_type,
                            defaults={
                                "document_no": document_no,
                                "document": file,
                            }
                        )

                    # created_ids.append(obj.id)

            # rollback if any error across ANY user
            if errors:
                transaction.set_rollback(True)
                return Response({
                    "message": "Document Bulk Upload failed",
                    "errors": errors
                }, status=400)

        return Response({
            "message": "Documents uploaded successfully",
            # "created_ids": created_ids
        }, status=status.HTTP_200_OK)


class BusinessMemberSuggestionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business_id = request.query_params.get('business_id')
        residential_code = request.query_params.get('residential_code')

        if not business_id and not residential_code:
            return Response({
                "suggestions": []
            }, status=status.HTTP_200_OK)

        filters = Q(is_active=True)

        conditions = Q()
        if business_id:
            conditions |= Q(business_family_id=business_id)
        if residential_code:
            conditions |= Q(residential_details__residential_code=residential_code)
        
        filters &= conditions
        
        prof_qs = UserProfessionalDetails.objects.filter(filters).values_list('user_id', flat=True)
        
        # Only suggest active users not already deleted
        suggestions = User.objects.filter(
            id__in=prof_qs, 
            is_deleted=False
        ).distinct()

        user_suggestions_serializer = BusinessMemberPayloadSuggestionSerializer(
            suggestions, 
            many=True,
            context={'business_id': business_id, 'residential_code': residential_code}
        )

        return Response({
            "suggestions": user_suggestions_serializer.data
        }, status=status.HTTP_200_OK)


class UserSuggestionsDropdownView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id=None):
        if user_id is None:
            full_name = request.query_params.get('name', "").strip()
            contact_no = request.query_params.get('contact_no', "").strip()

            filters = Q()

            if full_name:
                filters |= Q(full_name__icontains=full_name)
            if contact_no:
                filters |= Q(contact_no__icontains=contact_no)
            
            if not filters:
                return Response({
                    "suggestions": []
                }, status=status.HTTP_200_OK)

            suggestions = User.objects.filter(
                filters
            ).distinct()[:10]

            user_suggestions_seriaizer = UserSuggestionDropdownSerializer(suggestions, many=True)

            return Response({
                "suggestions": user_suggestions_seriaizer.data
            }, status=status.HTTP_200_OK)

        
        try:
            user_profile_obj = UserProfile.objects.get(user=user_id)
        except UserProfile.DoesNotExist:
            return Response({
                "user_details": {}
            }, status=status.HTTP_200_OK)
        
        user_details_serializer = UserDetailsOutputSerializer(user_profile_obj)
        return Response({
            "user_details": user_details_serializer.data
        }, status=status.HTTP_200_OK)



class UserListView(AssignedNodeFilterMixin, AdminRoleFilterMixin, APIView):
    permission_classes = [IsAuthenticated]
    model = User
    node_filter_field = "current_residential_details__node_mappings__node_id__in"

    def get(self, request):
        role_name = request.query_params.get('role', "user").strip()

        role_ids, error_response = self.get_allowed_role_ids(request, role_name)
        if error_response:
            return error_response
        
        # 1. Apply select_related early! 
        # This forces Django to JOIN the residential and personal tables immediately,
        # which is required because RawSQL needs those tables to exist in the SQL query.
        
        user_qs = (
            self.get_queryset().filter(roles__id__in=role_ids)
            .distinct()
            .select_related(
                "current_residential_details",
                "personal_details",
                "profile",
            )
        )

        for key, value in request.query_params.items():
            # Cast the value to an integer if it consists only of digits
            if value.isdigit():
                parsed_value = int(value)
            else:
                parsed_value = value

            # 2. Apply to Residential Filters
            if key.startswith("res_"):
                json_key = key.replace("res_", "")

                user_qs = user_qs.filter(
                    current_residential_details__node_mappings__level_id=int(json_key),
                    current_residential_details__node_mappings__node_id=parsed_value
                )
            
            # 3. Apply to Personal Filters
            elif key.startswith("per_"):
                json_key = key.replace("per_", "")
                
                user_qs = user_qs.filter(
                    personal_details__node_mappings__level_id=int(json_key),
                    personal_details__node_mappings__node_id=parsed_value
                )

        paginator = CommonPagination()
        paginated_qs = paginator.paginate_queryset(user_qs, request, view=self)
        serializer = UserListSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


class RelationTypeDropdownView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        category_param = request.query_params.get('category', '').strip()
        role_param = request.query_params.get('role', 'user').strip()

        if category_param:
            relation_type_qs = RelationType.objects.filter(is_active=True, category=category_param, role__name=role_param).exclude(
                name__in=["husband", "wife", "son", "daughter", "guest", "worker"]
            )
        else:
            relation_type_qs = RelationType.objects.filter(
                is_active=True, 
                category='general', 
                role__name=role_param,
                name__in=["husband", "wife", "son", "daughter", "guest", "worker"]
            )

        serializer = RelationTypeDropdownSerializer(relation_type_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DesignationTypeDropdownView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        designation_type_qs = DesignationType.objects.filter(is_active=True)
        serializer = DesignationTypeDropdownSerializer(designation_type_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BusinessFamilyDropdownView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business_family_qs = BusinessFamily.objects.all()

        search_name = request.query_params.get("search", "").strip()
        if search_name:
            business_family_qs = business_family_qs.filter(name__icontains=search_name)[:10]

        serializer = BusinessFamilyDropdownSerializer(business_family_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    

from django.utils import timezone    

class DeleteUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print(int(timezone.now().timestamp()))
        user_id = request.data.get("user_id")
        want_continue = request.data.get("want_to_continue", False)

        if not user_id:
            return Response({"user_id": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(user_id, int):
            return Response({"user_id": "Invalid format"}, status=status.HTTP_400_BAD_REQUEST)
        
        if want_continue and not isinstance(want_continue, bool):
            return Response({"want_continue": "Invalid format"}, status=status.HTTP_400_BAD_REQUEST)
        
        user_obj = get_object_or_404(User, id=user_id)

        # Safety Check: Prevent the user from deleting themselves
        if user_obj.id == request.user.id:
            return Response({"error": "You cannot delete yourself."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            existing_main_member_obj = FamilyMember.objects.select_related(
                "family",
                "user",
                "self_relation_type"
            ).get(user=user_obj, is_main_user=True)

            family_obj = existing_main_member_obj.family
            member_count = family_obj.members.filter(user__is_deleted=False).count()

            warning_relation = None
            if existing_main_member_obj.self_relation_type.name == "husband":
                warning_relation = "Wife"
                # Look for a valid spouse (Fetch directly excluding deleted users)
                future_main_member_obj = FamilyMember.objects.filter(
                    family=family_obj, 
                    self_relation_type__name="wife",
                    user__is_deleted=False
                ).select_related(
                    "user__profile",
                    "self_relation_type"
                ).first()
            else:
                warning_relation = "Husband"
                # Look for a valid spouse (Fetch directly excluding deleted users)
                future_main_member_obj = FamilyMember.objects.filter(
                    family=family_obj, 
                    self_relation_type__name="husband",
                    user__is_deleted=False
                ).select_related(
                    "user__profile",
                    "self_relation_type"
                ).first()

            print("future_main_member_obj:", future_main_member_obj)
            if future_main_member_obj is None:
                if not want_continue and member_count > 1:
                    return Response({"warning": f"{warning_relation} is not found for this user family so after delete then whole family will be deleted."}, status=status.HTTP_400_BAD_REQUEST)

                for member in family_obj.members.all():
                    member.user.soft_delete(user=request.user)
                return Response({"message": "Successfully deleted."}, status=status.HTTP_200_OK)


            if future_main_member_obj.user.profile.expired_date:
                if not want_continue:
                    return Response({"warning": f"{future_main_member_obj.self_relation_type.display_name}-{future_main_member_obj.user.full_name} is expired of this family so after delete then whole family will be deleted."}, status=status.HTTP_400_BAD_REQUEST)

                for member in family_obj.members.all():
                    member.user.soft_delete(user=request.user)
                return Response({"message": "Successfully deleted."}, status=status.HTTP_200_OK)
                

            if not want_continue:
                return Response({"warning": f"After delete {existing_main_member_obj.user.full_name} {warning_relation}: '{future_main_member_obj.user.full_name}' will be main user."}, status=status.HTTP_400_BAD_REQUEST)
            
            existing_main_member_obj.is_main_user = False
            existing_main_member_obj.save()

            future_main_member_obj.is_main_user = True
            future_main_member_obj.save()

        except FamilyMember.DoesNotExist:
            pass
        except Exception as e:
            print(e)
            return Response({"error": "Something went wrong. Please try again."}, status=status.HTTP_400_BAD_REQUEST)
        
        
        # Call custom Soft Delete method to preserve the Audit Trail
        user_obj.soft_delete(user=request.user)

    
        return Response({
            "message": f"Successfully deleted.",
        }, status=status.HTTP_200_OK)


class FamilyTreeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        data = build_family_tree(user)

        return Response(data)   




class FamilyTreeByPidhiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        """
        GET /api/family-tree-by-pidhi/<user_id>/
        """

        main_member = FamilyMember.objects.filter(
            user=user_id,
            is_main_user=True
        ).first()

        if main_member:
            member = main_member
        else:
            member = FamilyMember.objects.filter(
                user=user_id
            ).first()


        if not member:
            return Response(
                {"error": "Family not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        family_id = member.family_id

        data = build_family_tree_by_pidhi(family_id)

        return Response(data, status=200)
    


class BusinessRegisterView(APIView):
    """
    POST /api/users/business/register/

    Registers a new Business (BusinessFamily) along with its members.

    Expected payload (validated by BusienssRegistrationInputSerializer):
    {
        "role": "<role_name>",
        "sub_role": <sub_role_id>,
        "residential_type": <residential_type_id>,
        "business_family": {
            "name": "",
            "company_type": "",
            "registration_no": "",
            "pan_no": "",
            "gstin": "",
            "business_type": "",
            "company_size": "",
            "email": "",
            "contact_no": "",
            "website": "",
            "established_year": null,
            "latitude": null,
            "longitude": null,
            "residential_details": {"<level_id>": <node_id>, ...},
            "professional_details": {"<level_id>": <node_id>, ...},
            "operating_hours": [
                {"day_of_week": "monday", "open_time": "09:00", "close_time": "18:00"},
                ...
            ]
        },
        "business_members": [
            {
                "user_id": null,
                "self_designation_type": <designation_type_id>,
                "contact_no": "",
                "email": "",
                "full_name": "",
                ...<profile fields>...,
                "personal_details": {"<level_id>": <node_id>, ...},
                "residential_details": {"<level_id>": <node_id>, ...},
                "professional_details": {
                    "id": null,                        # null = new, or PK of existing UserProfessionalDetails
                    "designation": <designation_id>,   # designation within the business
                    "professional_details": {"<level_id>": <node_id>, ...},
                    "joined_date": "YYYY-MM-DD",
                    "left_date": null,
                    "experience": "",
                    "is_active": true
                }
            },
            ...
        ]
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        input_serializer = BusienssRegistrationInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        validated_data = input_serializer.validated_data

        role_obj = validated_data.get('role')
        sub_role_obj = validated_data.get('sub_role')
        residential_type = validated_data.get('residential_type')
        business_data = validated_data.get('business_family')
        business_members = validated_data.get('business_members')

        with transaction.atomic():
            # ------------------------------------------------------------------
            # 1. Build / update BusinessFamily
            # ------------------------------------------------------------------
            operating_hours_data = business_data.pop('operating_hours', [])
            residential_details_json = business_data.pop('residential_details', {})
            professional_details_json = business_data.pop('professional_details', {})

            business_family_id = business_data.pop('id', None)

            business_family_defaults = {
                **business_data,
                'role': role_obj,
                'sub_role': sub_role_obj,
            }

            if business_family_id:
                try:
                    business_family_obj = BusinessFamily.objects.get(id=business_family_id)
                    for attr, value in business_family_defaults.items():
                        setattr(business_family_obj, attr, value)
                    business_family_obj.save()
                except BusinessFamily.DoesNotExist:
                    raise ValidationError({"business_family": "Business family not found."})
            else:
                business_family_obj = BusinessFamily.objects.create(**business_family_defaults)

            # ------------------------------------------------------------------
            # 2. Operating Hours – replace all for idempotency
            # ------------------------------------------------------------------
            if operating_hours_data:
                BusinessOperatingHours.objects.filter(business_family=business_family_obj).delete()
                hours_to_create = [
                    BusinessOperatingHours(
                        business_family=business_family_obj,
                        day_of_week = hours['day_of_week'],
                        open_time = hours['open_time'],
                        close_time = hours['close_time'],
                    )
                    for hours in operating_hours_data
                ]
                BusinessOperatingHours.objects.bulk_create(hours_to_create)

            # ------------------------------------------------------------------
            # 3. Residential Details for the business
            # ------------------------------------------------------------------
            from .utils import get_or_create_residential_details
            business_residential_obj, _ = get_or_create_residential_details(residential_details_json)

            # Link the business to the residential address via ResidentMapping
            resident_mapping, _ = ResidentMapping.objects.get_or_create(
                business_family = business_family_obj,
                residential_type = residential_type,
                defaults={'residential_details': business_residential_obj},
            )
            # If an existing mapping exists, update the residential details
            if resident_mapping.residential_details != business_residential_obj:
                resident_mapping.residential_details = business_residential_obj
                resident_mapping.save()

            # ------------------------------------------------------------------
            # 4. Professional Node Mappings for the business itself
            # ------------------------------------------------------------------
            business_family_obj.professional_node_mappings.all().delete()
            prof_mappings = [
                BusinessFamilyProfessionalNodeMapping(
                    business_family=business_family_obj,
                    level_id=int(level_id),
                    node_id=int(node_id),
                )
                for level_id, node_id in professional_details_json.items()
                if level_id and node_id
            ]
            if prof_mappings:
                BusinessFamilyProfessionalNodeMapping.objects.bulk_create(prof_mappings)

            # ------------------------------------------------------------------
            # 5. Business Members
            # ------------------------------------------------------------------
            for member_data in business_members:
                existing_user_obj = member_data.pop('user_id', None)
                designation_type_obj = member_data.pop('self_designation_type')
                post_no = member_data.pop('post_no', None)

                # Personal / residential node JSONs
                personal_details_json = member_data.pop('personal_details', {}) or {}
                residential_details_json_member = member_data.pop('residential_details', {}) or {}

                # --- NEW: professional_details is now a nested validated dict ---
                prof_details_data = member_data.pop('professional_details', {}) or {}

                # Unpack the nested professional details
                prof_id = prof_details_data.get('id')           # UserProfessionalDetails instance or None
                prof_nodes_json = prof_details_data.get('professional_details', {}) or {}
                prof_designation = prof_details_data.get('designation')  # DesignationType instance
                prof_joined_date = prof_details_data.get('joined_date')
                prof_left_date = prof_details_data.get('left_date')
                prof_experience = prof_details_data.get('experience')
                prof_is_active = prof_details_data.get('is_active', True)

                # Use prof_designation if provided, otherwise fall back to self_designation_type
                effective_designation = prof_designation or designation_type_obj

                # User-level fields
                full_name = member_data.pop('full_name')
                email = member_data.pop('email', None)
                contact_no = member_data.pop('contact_no')

                user_defaults = {
                    'full_name': full_name,
                    'email': email,
                    'contact_no': contact_no,
                }

                if existing_user_obj:
                    user_obj, _ = User.objects.update_or_create(
                        id=existing_user_obj.id,
                        defaults=user_defaults,
                    )
                else:
                    user_obj = User.objects.create(**user_defaults)

                user_role_obj = UserRole.objects.get(name="user")
                # Assign role to the user
                user_obj.roles.add(user_role_obj)
                user_obj.save()

                # User Profile (remaining profile fields after popping all non-profile keys)
                UserProfile.objects.update_or_create(
                    user = user_obj,
                    defaults = member_data,
                )

                # ----------------------------------------------------------
                # Personal Details + node mappings
                # ----------------------------------------------------------
                try:
                    user_personal_obj = UserPersonalDetails.objects.get(user=user_obj)
                except UserPersonalDetails.DoesNotExist:
                    user_personal_obj = UserPersonalDetails.objects.create(user=user_obj)

                if personal_details_json:
                    user_personal_obj.node_mappings.all().delete()
                    personal_mappings = [
                        PersonalNodeMapping(
                            personal_detail = user_personal_obj,
                            level_id = int(level_id),
                            node_id = int(node_id),
                        )
                        for level_id, node_id in personal_details_json.items()
                        if level_id and node_id
                    ]
                    if personal_mappings:
                        PersonalNodeMapping.objects.bulk_create(personal_mappings)

                # ----------------------------------------------------------
                # Residential Details for the member's workplace address
                # ----------------------------------------------------------
                member_residential_obj, _ = get_or_create_residential_details(
                    residential_details_json_member
                )

                # ----------------------------------------------------------
                # UserProfessionalDetails — update existing record by ID or
                # get-or-create against the (user, business_family) pair
                # ----------------------------------------------------------
                prof_detail_defaults = {
                    'residential_details': member_residential_obj,
                    'designation': effective_designation,
                    'joined_date': prof_joined_date,
                    'left_date': prof_left_date,
                    'experience': prof_experience,
                    'is_active': prof_is_active,
                }

                if prof_id:
                    # Serializer resolved the PK to a UserProfessionalDetails instance
                    professional_details_obj = prof_id
                    if professional_details_obj.user != user_obj or \
                       professional_details_obj.business_family != business_family_obj:
                        raise ValidationError({
                            "professional_details": "Professional details record does not belong to this user/business."
                        })
                    for attr, val in prof_detail_defaults.items():
                        setattr(professional_details_obj, attr, val)
                    professional_details_obj.save()
                else:
                    professional_details_obj, created = UserProfessionalDetails.objects.get_or_create(
                        user = user_obj,
                        business_family = business_family_obj,
                        defaults = prof_detail_defaults,
                    )
                    if not created:
                        for attr, val in prof_detail_defaults.items():
                            setattr(professional_details_obj, attr, val)
                        professional_details_obj.save()

                # Professional node mappings for the member
                if prof_nodes_json:
                    professional_details_obj.professional_node_mappings.all().delete()
                    member_prof_mappings = [
                        ProfessionalNodeMapping(
                            professional_detail=professional_details_obj,
                            level_id=int(level_id),
                            node_id=int(node_id),
                        )
                        for level_id, node_id in prof_nodes_json.items()
                        if level_id and node_id
                    ]
                    if member_prof_mappings:
                        ProfessionalNodeMapping.objects.bulk_create(member_prof_mappings)

                # ----------------------------------------------------------
                # BusinessFamilyMember link
                # ----------------------------------------------------------
                business_member_obj, created = BusinessFamilyMember.objects.get_or_create(
                    business_family=business_family_obj,
                    user=user_obj,
                    defaults={
                        'self_designation_type': designation_type_obj,
                        'post_no': post_no or 0,
                        'is_active': True,
                    },
                )
                if not created:
                    business_member_obj.self_designation_type = designation_type_obj
                    if post_no is not None:
                        business_member_obj.post_no = post_no
                    business_member_obj.save()

        # ------------------------------------------------------------------
        # 6. Return response
        # ------------------------------------------------------------------
        serializer = BusinessRegisterOutputSerializer(business_family_obj)
        return Response(
            {
                "message": "Business registered successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )



from .serializers import AdminRegistrationInputSerializer, AdminRegistrationOutputSerializer

class AdminRegistrationView(AdminRoleFilterMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        admin_role = get_object_or_404(
            UserRole,
            name="admin",
            is_active=True
        )

        sub_role = request.query_params.get("sub_role")
        user_id = request.query_params.get("user_id")

        role_ids, error_response = self.get_allowed_role_ids(request, "admin")
        if error_response:
             return error_response

        if sub_role:
            role = get_object_or_404(
                UserRole,
                name=sub_role,
                is_active=True
            )
            
            if role.id not in role_ids:
                return Response({"error": "You don't have permission to view this role."}, status=status.HTTP_403_FORBIDDEN)

            user_objs = User.objects.filter(
                roles=role,
                is_deleted=False
            ).distinct()

        else:
            user_objs = User.objects.filter(
                roles__in=role_ids,
                is_deleted=False
            ).distinct()

        if user_id:
            user_objs = user_objs.filter(id=user_id)

        output_data = {
            "role": admin_role,
            "users": user_objs
        }

        serializer = AdminRegistrationOutputSerializer(output_data)
        return Response(serializer.data, status=status.HTTP_200_OK)


    def post(self, request):
        print(request.data)
        serializer = AdminRegistrationInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        role_obj = validated_data.get('role')
        admin_members = validated_data.get('admin_members', [])
        
        registered_users = []

        try:
            with transaction.atomic():
                for member_data in admin_members:
                    existing_user_obj = member_data.pop('user_id', None)
                    sub_role_obj = member_data.pop('self_sub_role')

                    # Personal / residential node JSONs
                    personal_details_json = member_data.pop('personal_details', {}) or {}
                    residential_details_json_member = member_data.pop('residential_details', {}) or {}

                    # Professional details nested dict
                    prof_details_data = member_data.pop('professional_details', {}) or {}

                    prof_id = prof_details_data.get('id')           
                    prof_nodes_json = prof_details_data.get('professional_details', {}) or {}
                    prof_designation = prof_details_data.get('designation') 
                    prof_salary = prof_details_data.get('salary')  
                    prof_joined_date = prof_details_data.get('joined_date')
                    prof_left_date = prof_details_data.get('left_date')
                    prof_experience = prof_details_data.get('experience')
                    prof_is_active = prof_details_data.get('is_active', True)

                    # User-level fields
                    full_name = member_data.pop('full_name')
                    email = member_data.pop('email', None)
                    contact_no = member_data.pop('contact_no')

                    user_defaults = {
                        'full_name': full_name,
                        'email': email,
                        'contact_no': contact_no,
                    }

                    if existing_user_obj:
                        user_obj, _ = User.objects.update_or_create(
                            id=existing_user_obj.id,
                            defaults=user_defaults,
                        )
                    else:
                        user_obj = User.objects.create(**user_defaults)

                    # Assign the admin role and sub_role to the user
                    if existing_user_obj:
                        admin_sub_roles = user_obj.roles.filter(parent__name='admin')
                        if admin_sub_roles.exists():
                            user_obj.roles.remove(*admin_sub_roles)

                    user_obj.roles.add(sub_role_obj)
                    user_obj.is_verified = True
                    user_obj.save()
                    
                    registered_users.append(user_obj)

                    # User Profile 
                    UserProfile.objects.update_or_create(
                        user = user_obj,
                        defaults = member_data,
                    )

                    # Personal Details 
                    try:
                        user_personal_obj = UserPersonalDetails.objects.get(user=user_obj)
                    except UserPersonalDetails.DoesNotExist:
                        user_personal_obj = UserPersonalDetails.objects.create(user=user_obj)

                    if personal_details_json:
                        user_personal_obj.node_mappings.all().delete()
                        personal_mappings = [
                            PersonalNodeMapping(
                                personal_detail = user_personal_obj,
                                level_id = int(level_id),
                                node_id = int(node_id),
                            )
                            for level_id, node_id in personal_details_json.items()
                            if level_id and node_id
                        ]
                        if personal_mappings:
                            PersonalNodeMapping.objects.bulk_create(personal_mappings)

                    # Residential Details 
                    from .utils import get_or_create_residential_details
                    member_residential_obj, _ = get_or_create_residential_details(
                        residential_details_json_member
                    )

                    # Professional Details (Not linked to a BusinessFamily)
                    prof_detail_defaults = {
                        'residential_details': member_residential_obj,
                        'designation': prof_designation,
                        'salary': prof_salary,
                        'joined_date': prof_joined_date,
                        'left_date': prof_left_date,
                        'experience': prof_experience,
                        'is_active': prof_is_active,
                    }

                    if prof_id:
                        professional_details_obj = prof_id
                        if professional_details_obj.user != user_obj:
                            raise ValidationError({
                                "professional_details": "Professional details record does not belong to this user."
                            })
                        for attr, val in prof_detail_defaults.items():
                            setattr(professional_details_obj, attr, val)
                        professional_details_obj.save()
                    else:
                        professional_details_obj, created = UserProfessionalDetails.objects.get_or_create(
                            user = user_obj,
                            business_family = None,
                            defaults = prof_detail_defaults,
                        )
                        if not created:
                            for attr, val in prof_detail_defaults.items():
                                setattr(professional_details_obj, attr, val)
                            professional_details_obj.save()

                    if prof_nodes_json:
                        professional_details_obj.professional_node_mappings.all().delete()
                        member_prof_mappings = [
                            ProfessionalNodeMapping(
                                professional_detail=professional_details_obj,
                                level_id=int(level_id),
                                node_id=int(node_id),
                            )
                            for level_id, node_id in prof_nodes_json.items()
                            if level_id and node_id
                        ]
                        if member_prof_mappings:
                            ProfessionalNodeMapping.objects.bulk_create(member_prof_mappings)

        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        output_data = {
            "role": role_obj,
            "users": registered_users
        }
        
        output_serializer = AdminRegistrationOutputSerializer(output_data)
        
        return Response({
            "message": "Admin registration successful.",
            "data": output_serializer.data
        }, status=status.HTTP_201_CREATED)
    

class UserRoleDropdownView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role_name = request.query_params.get('role', '').strip()

        role_qs = UserRole.objects.filter(is_active=True)
        if role_name:
            role_qs = role_qs.filter(parent__name=role_name, is_active=True)

        serializer = RoleDropdownSerializer(role_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


from .serializers import AdminResidentialNodeAssignmentInputSerializer, AdminResidentialNodeAssignmentOutputSerializer
from configuration.models import Level, Node

class AdminResidentialNodeAssignmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({"error": "user_id query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        assignments = AdminResidentialNodeAssignment.objects.select_related('level', 'node').filter(user_id=user_id)
        serializer = AdminResidentialNodeAssignmentOutputSerializer(assignments, many=True)
        return Response({"user_id": int(user_id), "assignments": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AdminResidentialNodeAssignmentInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user_id']
        assignments = serializer.validated_data['assignments']

        processed_ids = []
        
        try:
            with transaction.atomic():
                for item in assignments:
                    # Serializer uses source='level' and source='node'
                    level_obj = item['level']
                    node_obj = item['node']

                    assignment_obj, created = AdminResidentialNodeAssignment.objects.get_or_create(
                        user=user,
                        level=level_obj,
                        node=node_obj,
                    )
                    processed_ids.append(assignment_obj.id)
                
                # Remove assignments that were not included in the payload
                AdminResidentialNodeAssignment.objects.filter(user=user).exclude(id__in=processed_ids).delete()
                
        except Exception as e:
             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        updated_assignments = AdminResidentialNodeAssignment.objects.select_related('level', 'node').filter(user_id=user.id)
        out_serializer = AdminResidentialNodeAssignmentOutputSerializer(updated_assignments, many=True)
        return Response({"message": "Admin node assignments updated successfully.", "user_id": user.id, "assignments": out_serializer.data}, status=status.HTTP_200_OK)