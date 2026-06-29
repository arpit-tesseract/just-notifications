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



from .serializers import (
    LoginEmailPasswordSerializer,UserBasicDetailsOutputSerializer, LogoutInputSerializer,
    ResidentialTypeListSerializer, DocumentTypeListSerializer, RelationTypeListSerializer, DesignationTypeListSerializer,
    BusinessFamilyListSerializer, BussinessFamilyDetailsOutputSerializer,
    UserSuggestionListSerializer, UserDetailsOutputSerializer,
    RegistrationInputSerializer, RegistrationOutputSerializer, UserListSerializer, 
)
from .models import *
from .utils import (map_family_internal_relations, map_relations_with_husband_user, build_family_tree, build_family_tree_by_pidhi)
# Create your views here.


class LoginWithEmailPasswordView(APIView):
    def post(self, request):
        serializer = LoginEmailPasswordSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        email = validated_data.get('email').strip().lower()
        password = validated_data.get('password').strip()
            
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
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
        
        residential_obj, _ = ResidentialDetails.objects.get_or_create(
            nodes=residential_details_json
        )

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
                    user_personal_obj.nodes = personal_details_json
                    user_personal_obj.save()
                except UserPersonalDetails.DoesNotExist:
                    user_personal_obj = UserPersonalDetails.objects.create(
                        user = user_obj,
                        nodes = personal_details_json
                    )
                
                print("professional_details_lst", professional_details_lst)
                for professional_details in professional_details_lst:
                    company_name = professional_details.get('company')
                    residential_nodes = professional_details.get('residential_details', {})

                    bussiness_residential_obj, _ = ResidentialDetails.objects.get_or_create(
                        nodes=residential_nodes
                    )

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
                            professional_details_obj.personal_nodes = personal_nodes
                            professional_details_obj.professional_nodes = professional_nodes
                            professional_details_obj.designation = designation_obj
                            professional_details_obj.is_active = is_active
                            professional_details_obj.save()
                        except UserProfessionalDetails.DoesNotExist:
                            raise ValidationError({
                                "error": "Professional details not found"
                            })

                    else:
                        UserProfessionalDetails.objects.create(
                            user=user_obj,
                            business_family = business_family_obj,
                            residential_details=bussiness_residential_obj,
                            personal_nodes=personal_nodes,
                            professional_nodes=professional_nodes,
                            designation=designation_obj,
                            is_active=is_active
                        )
                    
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
                        family_resident_obj, _ = ResidentMapping.objects.get_or_create(
                            family = family_obj,
                            residential_details = residential_obj,
                            residential_type = residential_type,
                            defaults={
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
                        family_resident_obj, created = ResidentMapping.objects.get_or_create(
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
                        registration_resident_obj, created = ResidentMapping.objects.get_or_create(
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



class ResidentialTypeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        residential_type_qs = ResidentialType.objects.filter(is_active=True)
        serializer = ResidentialTypeListSerializer(residential_type_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DocumentTypeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        document_type_qs = DocumentType.objects.filter(is_active=True)
        serializer = DocumentTypeListSerializer(document_type_qs, many=True)
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


class UserSuggestionsListView(APIView):
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

            user_suggestions_seriaizer = UserSuggestionListSerializer(suggestions, many=True)

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



class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_role = request.query_params.get('user_role', "user").strip()
        
        # 1. Apply select_related early! 
        # This forces Django to JOIN the residential and personal tables immediately,
        # which is required because RawSQL needs those tables to exist in the SQL query.
        user_qs = User.objects.filter(roles__name=user_role).select_related(
            'current_residential_details', 
            'personal_details', 
            'profile'
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

                user_qs = user_qs.annotate(
                    res_json_val=RawSQL(
                        f"JSON_EXTRACT(user_userresidentialdetails.nodes, '$.\"{json_key}\"')",
                        []
                    )
                ).filter(res_json_val=parsed_value)
            
            # 3. Apply to Personal Filters
            elif key.startswith("per_"):
                json_key = key.replace("per_", "")
                
                # Assuming your app name is 'user', the table name is 'user_userpersonaldetails'
                user_qs = user_qs.annotate(
                    per_json_val=RawSQL(
                        f"JSON_EXTRACT(user_userpersonaldetails.nodes, '$.\"{json_key}\"')",
                        []
                    )
                ).filter(per_json_val=parsed_value)

        serializer = UserListSerializer(user_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RelationTypeView(APIView):
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

        serializer = RelationTypeListSerializer(relation_type_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DesignationTypeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        designation_type_qs = DesignationType.objects.filter(is_active=True)
        serializer = DesignationTypeListSerializer(designation_type_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BusinessFamilyListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id=None):
        if id:
            try:
                business_family_obj = BusinessFamily.objects.get(id=id, is_verified=True)
            except BusinessFamily.DoesNotExist:
                return Response({"error": "Business family not found"}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = BussinessFamilyDetailsOutputSerializer(business_family_obj)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        business_family_qs = BusinessFamily.objects.filter(is_verified=True)

        search_name = request.query_params.get("search", "").strip()
        if search_name:
            business_family_qs = business_family_qs.filter(name__icontains=search_name)

        serializer = BusinessFamilyListSerializer(business_family_qs, many=True)
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
    

