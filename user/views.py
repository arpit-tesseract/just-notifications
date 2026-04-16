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

from .serializers import (
    RegistrationInputSerializer, ResidentialTypeListSerializer, DocumentTypeListSerializer, UserSuggestionListSerializer,
    UserDetailsOutputSerializer, RegistrationOutputSerializer, UserListSerializer, RelationTypeListSerializer
)
from .models import *
from .utils import (map_family_internal_relations, map_relations_with_husband_user)
# Create your views here.

class RegistrationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        input_serializer = RegistrationInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        validated_data = input_serializer.validated_data
        registration_user = validated_data.get('registration_user')
        user_category = validated_data.get('user_category')
        residential_type = validated_data.get('residential_type')
        residential_details_json = validated_data.get('residential_details')
        family_members = validated_data.get('family_members')

        if residential_type.name != "current" and not registration_user:
            return Response({
                "registration_user": "This field is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            created_users = []
            created_user_ids = []
            main_user_obj = None
            main_user_residential_obj = None
            husband_user = None

            # Residential Details
            user_residential_obj, _ = UserResidentialDetails.objects.get_or_create(
                nodes=residential_details_json
            )


            for member in family_members:
                personal_details_json = member.pop('personal_details', {})
                existing_user_obj = member.pop('user_id')
                relation_obj = member.pop('relation')

                self_relation = member.pop('self_relation')
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
                
                if residential_type.name == "current":
                    user_obj.is_verified = True

                user_obj.current_residential_details = user_residential_obj
                
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

                if self_relation == "husband":
                    husband_user = user_obj

                # Add to created users
                created_users.append(
                    {
                        "user": user_obj,
                        "self_relation_type": self_relation_type_obj,
                        "personal_details": user_personal_obj,
                        "relation": relation_obj
                    }
                )
                created_user_ids.append(user_obj.id)

                if main_user_obj is None and self_relation == 'husband' and member.get('expired_date') is None:
                    main_user_obj = user_obj
                    main_user_residential_obj = user_residential_obj

                elif main_user_obj is None and self_relation == 'wife' and member.get('expired_date') is None:
                    main_user_obj = user_obj
                    main_user_residential_obj = user_residential_obj


            if not main_user_obj:
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
                        is_main_user = user_obj.id == main_user_obj.id
                    )
                    family_name += user_obj.full_name[0].upper()
                
                family_obj.name = family_name
                family_obj.save()
                
                registration_user_family_obj = family_obj

                try:
                    with transaction.atomic():
                        family_resident_obj, _ = FamilyResident.objects.get_or_create(
                            family = family_obj,
                            residential_details = user_residential_obj,
                            residential_type = residential_type
                        )
                except IntegrityError:
                    raise ValidationError({
                        "residential_details": "For this residential details a family already exists."
                    })

            else:
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
                        FamilyMember.objects.get_or_create(
                            family = main_user_family_obj,
                            user = user_obj,
                            self_relation_type = user.get("self_relation_type"),
                            is_main_user = user_obj.id == main_user_obj.id
                        )
                        family_name += user_obj.full_name[0].upper()

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

                # try:
                #     family_resident_obj = FamilyResident.objects.get(
                #         family = main_user_family_obj,
                #         residential_type = current_residential_type_obj
                #     )
                # except FamilyResident.DoesNotExist:
                #     family_resident_obj = FamilyResident.objects.create(
                #         family = main_user_family_obj,
                #         residential_details = main_user_residential_obj,
                #         residential_type = current_residential_type_obj
                #     )
                
                # try:
                #     family_resident_obj = FamilyResident.objects.get(
                #         family = registration_user_family_obj,
                #         residential_type = residential_type
                #     )
                # except FamilyResident.DoesNotExist:
                #     family_resident_obj = FamilyResident.objects.create(
                #         family = registration_user_family_obj,
                #         residential_details = main_user_residential_obj,
                #         residential_type = residential_type
                #     )

                # 1. Check for Main User Family Resident
                # if FamilyResident.objects.filter(
                #     residential_details=main_user_residential_obj, 
                #     residential_type=current_residential_type_obj
                # ).exists():
                #     raise ValidationError({
                #         "residential_details": "A family resident with these residential details and this family type already exists."
                #     })

                # 1. Check for Main User Family Resident
                try:
                    with transaction.atomic():
                        family_resident_obj, created = FamilyResident.objects.get_or_create(
                            family=main_user_family_obj,
                            residential_type=current_residential_type_obj,
                            defaults={'residential_details': main_user_residential_obj}
                        )
                except IntegrityError:
                    raise ValidationError({
                        "residential_details": "For this residential details a family already exists."
                    })

                # 2. Check for Registration User Family Resident
                try:
                    with transaction.atomic():
                        registration_resident_obj, created = FamilyResident.objects.get_or_create(
                            family=registration_user_family_obj,
                            residential_type=residential_type,
                            defaults={'residential_details': main_user_residential_obj}
                        )
                except IntegrityError:
                    raise ValidationError({
                        "residential_details": "For this residential details a family already exists."
                    })
            
            # Map family internal relations
            map_family_internal_relations(created_users)

            # Map relations, native, inlaws, maternal
            map_relations_with_husband_user(registration_user_family_obj, created_users)
            
        
        return Response({
            "message": "User created successfully",
            "registration_user": registration_user.id if registration_user else None,
            "main_user": main_user_obj.id,
            "user_ids": created_user_ids
        }, status=status.HTTP_201_CREATED)
    

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
            registration_user_obj = get_object_or_404(User, id=registration_user)
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
        
        if registration_user_obj:
            try:
                family_member_obj = FamilyMember.objects.get(user=registration_user_obj, is_main_user=True)
                family_obj = family_member_obj.family

                try:
                    residential_obj = FamilyResident.objects.get(family=family_obj, residential_type=residential_type_obj).residential_details
                except FamilyResident.DoesNotExist:
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
                    family_obj = FamilyResident.objects.get(residential_details=residential_obj, residential_type__name="current").family
                except FamilyResident.DoesNotExist:
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
            residential_obj = FamilyResident.objects.get(family=family_obj, residential_type=residential_type_obj).residential_details
        except FamilyResident.DoesNotExist:
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


class RelationTypeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        relation_type_qs = RelationType.objects.filter(is_active=True).exclude(
            name__in=["husband", "wife", "son", "daughter", "guest", "worker"]
        )
        serializer = RelationTypeListSerializer(relation_type_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
