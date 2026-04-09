from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
import re

from .serializers import (
    RegistrationInputSerializer, FamilyTypeListSerializer, DocumentTypeListSerializer
)

from .models import *
# Create your views here.

class RegistrationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        input_serializer = RegistrationInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        validated_data = input_serializer.validated_data
        registration_user = validated_data.get('registration_user')
        user_category = validated_data.get('user_category')
        family_type = validated_data.get('family_type')
        print("family_type", family_type)
        family_members = validated_data.get('family_members')

        with transaction.atomic():
            created_users = []
            created_user_ids = []
            main_user_obj = None
            main_user_residential_obj = None

            for member in family_members:
                residential_details_json = member.pop('residential_details', {})
                personal_details_json = member.pop('personal_details', {})
                professional_details_json = member.pop('professional_details', {})
                user_id = member.pop('user_id')

                self_relation = member.pop('self_relation')

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

                if user_id:
                    user_obj, _ = User.objects.update_or_create(
                        id=user_id,
                        defaults=user_defaults
                    )
                else:
                    user_obj = User.objects.create(
                        full_name = full_name,
                        email = email,
                        contact_no = contact_no,
                        user_category = user_category,
                    )

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

                # Residential Details
                user_residential_obj, _ = UserResidentialDetails.objects.get_or_create(
                    nodes=residential_details_json
                )
                if family_type.name == 'current':
                    user_obj.current_residential_details = user_residential_obj
                    user_obj.save()
                

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
                    UserPersonalDetails.objects.create(
                        user = user_obj,
                        nodes = personal_details_json
                    )


                # Add to created users
                created_users.append(user_obj)
                created_user_ids.append(user_obj.id)

                print(f"name: {full_name}, self_relation: {self_relation}, expired_date: {member.get('expired_date')}")
                if main_user_obj is None and self_relation == 'husband' and member.get('expired_date') is None:
                    print("husband")
                    main_user_obj = user_obj
                    main_user_residential_obj = user_residential_obj

                elif main_user_obj is None and self_relation == 'wife' and member.get('expired_date') is None:
                    print("wife")
                    main_user_obj = user_obj
                    main_user_residential_obj = user_residential_obj
            

            if main_user_obj:
                if family_type.name == "current":
                    registration_user = main_user_obj
                
                if main_user_obj != registration_user:
                    try:
                        current_family_type = FamilyType.objects.get(name="current")
                    except FamilyType.DoesNotExist:
                        return Response({
                            "message": "Current family type does not exist.",
                            "status": status.HTTP_500_INTERNAL_SERVER_ERROR
                        })
                    
                    family_obj, _ = Family.objects.get_or_create(
                        main_user = main_user_obj,
                        family_type = current_family_type,
                        # nodes=main_user_residential_obj
                    )

                    for user in created_users:
                        FamilyMember.objects.get_or_create(
                            family = family_obj,
                            user = user
                        )


                family_obj, _ = Family.objects.update_or_create(
                    main_user = registration_user,
                    family_type = family_type,
                    defaults={
                        'residential_details': main_user_residential_obj
                    }
                )

                for user in created_users:
                    FamilyMember.objects.get_or_create(
                        family = family_obj,
                        user = user
                    )

        
        return Response({
            "message": "User created successfully",
            "registration_user": registration_user.id if registration_user else None,
            "main_user": main_user_obj.id,
            "user_ids": created_user_ids
        }, status=status.HTTP_201_CREATED)



class FamilyTypeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        family_type_qs = FamilyType.objects.filter(is_active=True)
        serializer = FamilyTypeListSerializer(family_type_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DocumentTypeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        document_type_qs = DocumentType.objects.filter(is_active=True)
        serializer = DocumentTypeListSerializer(document_type_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



# class DocumentUploadView(APIView):
#     permission_classes = [IsAuthenticated]
#     parser_classes = [MultiPartParser, FormParser]

#     def post(self, request, user_id):
#         try:
#             user_obj = User.objects.get(id=user_id)
#         except User.DoesNotExist:
#             return Response({"error": "User not found"}, status=404)
        
#         data = request.data

#         pattern = re.compile(r'documents\[(\d+)\]\[(\w+)\]')
#         documents = {}

#         # Step 1: Parse mapped FormData
#         for key, value in data.items():
#             match = pattern.match(key)
#             if match:
#                 doc_type_id, field = match.groups()
#                 doc_type_id = int(doc_type_id)

#                 if doc_type_id not in documents:
#                     documents[doc_type_id] = {}

#                 documents[doc_type_id][field] = value

#         if not documents:
#             return Response({"error": "No documents provided"}, status=400)

#         created_ids = []
#         errors = []

#         # Step 2: Validate + Save
#         with transaction.atomic():
#             for doc_type_id, doc in documents.items():

#                 file = doc.get("document")
#                 document_no = doc.get("document_no")

#                 try:
#                     document_type = DocumentType.objects.get(
#                         id=doc_type_id,
#                         is_active=True
#                     )
#                 except DocumentType.DoesNotExist:
#                     errors.append({f"documents[{doc_type_id}]": "Invalid document_type"})
#                     continue

#                 # File required Validation
#                 if not file:
#                     errors.append({f"documents[{doc_type_id}]": "File is required"})
#                     continue

#                 # Prevent crash if the frontend sends text instead of a physical file object
#                 if not hasattr(file, 'name'):
#                     errors.append({f"documents[{doc_type_id}]": "Invalid file format uploaded"})
#                     continue
                
#                 # Cleaner extension validation using a tuple
#                 ALLOWED_EXTENSIONS = (".pdf", ".jpg", ".jpeg", ".png")
#                 file_name = file.name.lower()

#                 if not file_name.endswith(ALLOWED_EXTENSIONS):
#                     errors.append({
#                         f"documents[{doc_type_id}]": f"Invalid extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
#                     })
#                     continue

#                 # if file.size > 5 * 1024 * 1024:
#                 #     errors.append({f"doc_type_{doc_type_id}": "File size should be less than 5MB"})
#                 #     continue

#                 # Save
#                 obj, _ = UserDocument.objects.update_or_create(
#                     user=user_obj,
#                     document_type=document_type,
#                     defaults={
#                         "document_no": document_no,
#                         "document": file,
#                     }
#                 )

#                 created_ids.append(obj.id)

#             # rollback if any error
#             if errors:
#                 transaction.set_rollback(True)
#                 return Response({
#                     "message": "Document Upload failed",
#                     "errors": errors
#                 }, status=400)

#         return Response({
#             "message": "Documents uploaded successfully",
#             "uploaded_ids": created_ids
#         }, status=status.HTTP_200_OK)
    

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
