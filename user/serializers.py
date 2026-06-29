from rest_framework import serializers
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import *
from configuration.models import Dimension, Level, Node
from .utils import get_level_node_mapping


class LoginInputSerializer(serializers.Serializer):
    contact_no = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ['id', 'name','display_name']
        read_only_fields = ['id', 'name', 'display_name']

# This Serializer Use after loggin success
class UserBasicDetailsOutputSerializer(serializers.ModelSerializer):
    roles = UserRoleSerializer(many=True)
    # designation = DesignationSerializer(many=False)
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'contact_no',
            'full_name',
            'roles',
        ]

class LogoutInputSerializer(serializers.Serializer):
    # access = serializers.CharField(write_only=True)
    refresh = serializers.CharField(write_only=True)


class ResidentialTypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResidentialType
        fields = ['id', 'name', 'display_name']


class DocumentTypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = ['id', 'display_name', 'is_required']


class UserProfessionalDetailsInputSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True, allow_null=True)
    company = serializers.CharField(required=True, allow_null=True)
    residential_details = serializers.JSONField(required=True, allow_null=True)
    personal_details = serializers.JSONField(required=True, allow_null=True)
    professional_details = serializers.JSONField(required=True, allow_null=True)
    designation = serializers.PrimaryKeyRelatedField(
        queryset = DesignationType.objects.filter(is_active=True),
        required=True, allow_null=True 
    )
    joined_date = serializers.DateField(required=True, allow_null=True)
    left_date = serializers.DateField(required=False, allow_null=True)
    experience = serializers.CharField(required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False)

    def validate_id(self, value):
        if value:
            try:
                professional_details = UserProfessionalDetails.objects.get(id=value)
            except UserProfessionalDetails.DoesNotExist:
                raise serializers.ValidationError("Professional details not found.")
            except Exception as e:
                raise serializers.ValidationError(str(e))

        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        joined_date = attrs.get("joined_date")
        left_date = attrs.get("left_date")
        
        if joined_date and left_date and joined_date > left_date:
            raise serializers.ValidationError({
                "joined_date": "joined_date cannot be greater than left_date."
            })
            
        return attrs

        

class UserDetailsInputSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset = User.objects.all(), 
        required=True, allow_null=True
    )
    self_relation = serializers.ChoiceField(
        choices=['husband', 'wife', 'son', 'daughter', 'guest', 'worker'],
        required=False
    )
    self_designation = serializers.PrimaryKeyRelatedField(
        queryset = DesignationType.objects.filter(is_active=True), 
        required=False
    )
    email = serializers.EmailField(required=True, allow_null=True)
    contact_no = serializers.CharField(required=True, allow_null=False)
    full_name = serializers.CharField(required=True, allow_null=False)
    pet_name = serializers.CharField(required=True, allow_null=True)
    father_name = serializers.CharField(required=True, allow_null=True)
    gender = serializers.ChoiceField(
        choices=UserProfile.GENDER_CHOICES,
        required=True, allow_null=True
    )
    post_no = serializers.DecimalField(max_digits=10, decimal_places=2, required=True, allow_null=True)
    dob = serializers.DateField(required=True, allow_null=True)
    birth_time = serializers.TimeField(required=True, allow_null=True)
    birth_place = serializers.CharField(required=True, allow_null=True)
    blood_group = serializers.ChoiceField(
        choices=UserProfile.BLOOD_GROUP_CHOICES,
        required=True, allow_null=True
    )
    marital_status = serializers.ChoiceField(
        choices=UserProfile.MARITAL_STATUS_CHOICES,
        required=True, allow_null=True
    )
    marriage_date = serializers.DateField(required=True, allow_null=True)
    education = serializers.ChoiceField(
        choices=UserProfile.EDUCATION_CHOICES,
        required=True, allow_null=True
    )
    education_detail = serializers.CharField(required=True, allow_null=True)

    expired_date = serializers.DateField(required=True, allow_null=True)
    expired_time = serializers.TimeField(required=True, allow_null=True)
    expired_place = serializers.CharField(required=True, allow_null=True)
    cremation_place = serializers.CharField(required=True, allow_null=True)
    relation = serializers.PrimaryKeyRelatedField(
        queryset = RelationType.objects.filter(is_active=True).exclude(
            name__in=['husband', 'wife', 'son', 'daughter', 'guest', 'worker']
        ), 
        many=True, required=True, allow_null=True
    )
    personal_details = serializers.JSONField(required=True, allow_null=True)
    professional_details = UserProfessionalDetailsInputSerializer(
        many=True,
        required=True,
        allow_null=True
    )
    # professional_details = serializers.ListField(
    #     child=serializers.JSONField(),
    #     required=False,
    #     allow_null=True
    # )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        gender = attrs.get('gender')
        self_relation = attrs.get('self_relation')
        user_obj = attrs.get('user_id')
        contact_no = attrs.get('contact_no')
        email = attrs.get('email')

        if not user_obj:
            user_objs = User.objects.filter(contact_no=contact_no)
            if user_objs.exists():
                raise serializers.ValidationError({"contact_no": "User with this contact number already exists."})
            
            if email:
                user_objs = User.objects.filter(email=email)
                if user_objs.exists():
                    raise serializers.ValidationError({"email": "User with this email already exists."})
        else:
            user_objs = User.objects.filter(contact_no=contact_no).exclude(id=user_obj.id)
            if user_objs.exists():
                raise serializers.ValidationError({"contact_no": "User with this contact number already exists."})
            
            if email:
                user_objs = User.objects.filter(email=email).exclude(id=user_obj.id)
                if user_objs.exists():
                    raise serializers.ValidationError({"email": "User with this email already exists."})
    

        if self_relation:
            if gender == 'male' and self_relation not in ['husband', 'guest', 'workers', 'son']:
                raise serializers.ValidationError({"gender": "Invalid gender."})

            if gender == 'female' and self_relation not in ['wife', 'guest', 'workers', 'daughter']:
                raise serializers.ValidationError({"gender": "Invalid gender."})
        
        return attrs
    
    def validate_expired_date(self, value):
        if value and value > timezone.now().date():
            raise serializers.ValidationError("Expired date cannot be in the future.")
        return value
    
    def validate_dob(self, value):
        if value and value > timezone.now().date():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value
    
    def _validate_node_json(self, value, dimension_obj):
        # 1. Allow null/empty values to pass through if they aren't required
        if not value:
            return value
            
        # 2. Ensure it is actually a dictionary {...}, not a list [...]
        if not isinstance(value, dict):
            raise serializers.ValidationError(f"must be a JSON object.")
        
        valid_level_ids = set(Level.objects.filter(dimension=dimension_obj).values_list('id', flat=True))
        
        valid_node_ids = set(Node.objects.filter(dimension=dimension_obj).values_list('id', flat=True))

        # 3. Validate that every Key (Level) and Value (Node) is a valid ID
        for level_id, node_id in value.items():
            if not str(level_id).isdigit():
                raise serializers.ValidationError(f"Invalid Level ID '{level_id}'. It must be numeric.")
            
            # Assuming node_id should also be numeric. If it can be a string, remove this check!
            if not str(node_id).isdigit(): 
                raise serializers.ValidationError({
                    level_id: f"Invalid Node ID '{node_id}'. It must be numeric."
                })
            
            # if int(level_id) not in valid_level_ids:
            #     raise serializers.ValidationError({
            #         level_id: f"Invalid Level ID '{level_id}'."
            #     })

            # if int(node_id) not in valid_node_ids:
            #     raise serializers.ValidationError({
            #         level_id: f"Invalid Node ID '{node_id}'."
            #     })
        return value


    def validate_personal_details(self, value):
        dimension_obj, _ = Dimension.objects.get_or_create(name="Personal")
        return self._validate_node_json(value, dimension_obj)
    
    def validate_professional_details(self, value):
        personal_dimension_obj, _ = Dimension.objects.get_or_create(name="Personal")
        residential_dimension_obj, _ = Dimension.objects.get_or_create(name="Residential")
        professional_dimension_obj, _ = Dimension.objects.get_or_create(name="Professional")

        if not value:
            return value

        ids = []

        for index, item in enumerate(value):

            residential_nodes = item.get("residential_details")
            personal_nodes = item.get("personal_details")
            professional_nodes = item.get("professional_details")
            row_id = item.get("id")

            self._validate_node_json(residential_nodes, residential_dimension_obj)
            self._validate_node_json(personal_nodes, personal_dimension_obj)
            self._validate_node_json(professional_nodes, professional_dimension_obj)

            if row_id:
                if row_id in ids:
                    raise serializers.ValidationError({
                        index: "Duplicate profession id."
                    })
                ids.append(row_id)

        return value
    


class RegistrationInputSerializer(serializers.Serializer):
    registration_type = serializers.ChoiceField(
        choices=['resident', 'corporate'],
    )

    registration_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=True,
        allow_null=True
    )

    user_category = serializers.ChoiceField(
        choices=User.USER_CATEGORY_CHOICES
    )

    residential_type = serializers.PrimaryKeyRelatedField(
        queryset=ResidentialType.objects.filter(is_active=True)
    )

    residential_details = serializers.JSONField()

    stay_from = serializers.DateField(required=False, allow_null=True)
    stay_to = serializers.DateField(required=False, allow_null=True)

    company = serializers.CharField(required=False, allow_null=True)

    family_members = UserDetailsInputSerializer(many=True, required=True, allow_null=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        company = attrs.get("company")
        residential_details = attrs.get("residential_details")
        residential_type = attrs.get("residential_type")
        family_members = attrs.get("family_members", [])
        
        stay_from = attrs.get("stay_from")
        stay_to = attrs.get("stay_to")

        if stay_from and stay_to and stay_from > stay_to:
            raise serializers.ValidationError({
                "stay_from": "stay_from date cannot be greater than stay_to date."
            })
        

        if not company and residential_type.name == "business":
            raise serializers.ValidationError({
                "company": "Company name is required."
            })

        if residential_type.name != "business":
            husband_count = sum(1 for member in family_members if member.get('self_relation') == "husband")
            
            # Check the count and raise appropriate errors
            if husband_count == 0:
                raise serializers.ValidationError({"family_members": "Husband is required."})
            elif husband_count > 1:
                raise serializers.ValidationError({"family_members": "Only one husband is allowed."})

        # require self_designation for each member
        errors = {}

        seen_contact_numbers = set()
        seen_emails = set()
        for index, member in enumerate(family_members):
            member_errors = {}

            # --- NEW: Duplicate Contact Number Check ---
            contact_no = member.get("contact_no")
            if contact_no:
                if contact_no in seen_contact_numbers:
                    member_errors["contact_no"] = "This contact number is already used by another family member in this request."
                else:
                    seen_contact_numbers.add(contact_no)
                
            # --- NEW: Duplicate Email Check ---
            email = member.get("email")
            if email:
                if email in seen_emails:
                    member_errors["email"] = "This email is already used by another family member in this request."
                else:
                    seen_emails.add(email)

            # ENFORCE self_designation requirement
            if not member.get("self_designation") and residential_type.name == "business":
                errors[index] = {
                    "self_designation": "This field is required."
                }

            if not member.get("self_relation") and residential_type.name != "business":
                errors[index] = {
                    "self_relation": "This field is required."
                }
            
            professional_details_lst = member.get("professional_details", [])

            # ENFORCE designation requirement if NOT business tab
            if residential_type.name != "business":
                prof_errors = {}
                for p_index, prof_details in enumerate(professional_details_lst):
                    if not prof_details.get("designation"):
                        prof_errors[p_index] = {"designation": "This field is required."}
                    
                    if not prof_details.get("company"):
                        prof_errors[p_index] = {"company": "This field is required."}
                
                if prof_errors:
                    member_errors["professional_details"] = prof_errors

            # MAP details if it IS business and there are no errors yet
            elif residential_type.name == "business" and not member_errors:
                self_designation = member.get("self_designation")
                personal_details = member.get("personal_details")

                for prof_details in professional_details_lst:
                    prof_details['company'] = company
                    prof_details['residential_details'] = residential_details
                    prof_details['personal_details'] = personal_details
                    prof_details['designation'] = self_designation

                # Re-assign back to the member dictionary
                member['professional_details'] = professional_details_lst
            
            # If this specific member had any errors, add it to the main error dictionary
            if member_errors:
                errors[index] = member_errors                

        if errors:
            raise serializers.ValidationError({
                "family_members": errors
            })

        return attrs
    

    def validate_residential_details(self, value):
        dimension_obj, _ = Dimension.objects.get_or_create(name="Residential")

        if not value:
            return value
            
        # 2. Ensure it is actually a dictionary {...}, not a list [...]
        if not isinstance(value, dict):
            raise serializers.ValidationError(f"must be a JSON object.")
        
        valid_level_ids = set(Level.objects.filter(dimension=dimension_obj).values_list('id', flat=True))
        
        valid_node_ids = set(Node.objects.filter(dimension=dimension_obj).values_list('id', flat=True))

        # 3. Validate that every Key (Level) and Value (Node) is a valid ID
        for level_id, node_id in value.items():
            if not str(level_id).isdigit():
                raise serializers.ValidationError(f"Invalid Level ID '{level_id}'. It must be numeric.")
            
            # Assuming node_id should also be numeric. If it can be a string, remove this check!
            if not str(node_id).isdigit(): 
                raise serializers.ValidationError({
                    level_id: f"Invalid Node ID '{node_id}'. It must be numeric."
                })
            
            # if int(level_id) not in valid_level_ids:
            #     raise serializers.ValidationError({
            #         level_id: f"Invalid Level ID '{level_id}'."
            #     })

            # if int(node_id) not in valid_node_ids:
            #     raise serializers.ValidationError({
            #         level_id: f"Invalid Node ID '{node_id}'."
            #     })
        return value


    # def validate_family_members(self, value):
    #     if value:
    #         # Count how many members have the relation "husband"
    #         husband_count = sum(1 for member in value if member.get('self_relation') == "husband")
            
    #         # Check the count and raise appropriate errors
    #         if husband_count == 0:
    #             raise serializers.ValidationError({"family_members": "Husband is required."})
    #         elif husband_count > 1:
    #             raise serializers.ValidationError({"family_members": "Only one husband is allowed."})
                
    #     return value


class RegistrationOutputSerializer(serializers.Serializer):
    registration_user = serializers.SerializerMethodField()
    residential_type = serializers.SerializerMethodField()
    user_category = serializers.SerializerMethodField()
    residential_details = serializers.SerializerMethodField()
    stay_from = serializers.SerializerMethodField()
    stay_to = serializers.SerializerMethodField()
    family_members = serializers.SerializerMethodField()

    def get_registration_user(self, family_obj):
        context = self.context
        return context.get('registration_user').id
        
    
    def get_user_category(self, family_obj):
        context = self.context
        registration_user_obj = context.get('registration_user')
        return registration_user_obj.user_category
        # try:
        #     main_family_member_obj = family_obj.members.filter(is_main_user=True).first()
        # except FamilyMember.DoesNotExist:
        #     raise ValidationError("Something went wrong. Please try again.")
        # except Exception as e:
        #     raise ValidationError("Something went wrong. Please try again: ")
        # return main_family_member_obj.user.user_category
    

    def get_residential_type(self, family_obj):
        context = self.context
        return context.get('residential_type').id


    def get_residential_details(self, family_obj):
        context = self.context
        residential_details = context.get('residential_details')
        if not residential_details:
            return None
        return {
            "residential_code": residential_details.residential_code,
            "nodes": get_level_node_mapping(residential_details.node_mappings.all()),
        }

    def get_stay_from(self, family_obj):
        context = self.context
        residential_type = context.get('residential_type')
        try:
            resident_mapping = ResidentMapping.objects.get(
                family=family_obj,
                residential_type=residential_type
            )
            return resident_mapping.stay_from
        except ResidentMapping.DoesNotExist:
            return None

    def get_stay_to(self, family_obj):
        context = self.context
        residential_type = context.get('residential_type')
        try:
            resident_mapping = ResidentMapping.objects.get(
                family=family_obj,
                residential_type=residential_type
            )
            return resident_mapping.stay_to
        except ResidentMapping.DoesNotExist:
            return None
    
    def get_family_members(self, family_obj):
        context = self.context
        registration_user_obj = context.get('registration_user')
        residential_type_obj = context.get('residential_type')

        if residential_type_obj.name == "business":
            family_members = family_obj.members.filter(user__is_deleted=False)
            family_members_lst = []

            for member in family_members:
                user_obj = member.user
                print(user_obj)
                user_details = UserDetailsOutputSerializer(
                    user_obj.profile,
                    exclude=['residential_details'],
                    context = {
                        'self_designation': member.self_designation_type,
                        'post_no': member.post_no
                    }
                ).data   
                family_members_lst.append(user_details)

            return family_members_lst

        main_user_obj = family_obj.members.filter(is_main_user=True).first().user
        family_members_lst = []
        try:
            family_members = family_obj.members.filter(user__is_deleted=False)
            for member in family_members:
                user_obj = member.user
                print(user_obj)
                user_details = UserDetailsOutputSerializer(
                    user_obj.profile,
                    exclude=['residential_details'],
                    context = {
                        'self_relation': member.self_relation_type,
                        'post_no': member.post_no
                    }
                ).data
                
                if main_user_obj != registration_user_obj:
                    relation_lst = []
                    try:
                        user_relation_qs = UserRelations.objects.filter(from_user=user_obj, to_user=registration_user_obj)
                        for user_relation_obj in user_relation_qs:
                            relation_type_obj = user_relation_obj.relation_type
                            relation_lst.append({
                                "id": relation_type_obj.id,
                                "name": relation_type_obj.display_name
                            })

                        user_details['relation'] = relation_lst
                    except UserRelations.DoesNotExist:
                        user_details['relation'] = []
                else:
                    user_details['relation'] = []

                family_members_lst.append(user_details)
        except FamilyMember.DoesNotExist:
            raise ValidationError("Something went wrong. Please try again.")
        except Exception as e:
            raise ValidationError("Something went wrong. Please try again: {}".format(e))
        
        return family_members_lst


class UserSuggestionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'contact_no']


class UserDocumentOutputSerializer(serializers.ModelSerializer):
    document_type_name = serializers.CharField(source='document_type.name', read_only=True)

    class Meta:
        model = UserDocument
        fields = ['id', 'document_type', 'document_type_name', 'document_no', 'document']


class UserDetailsOutputSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id')
    email = serializers.CharField(source='user.email')
    contact_no = serializers.CharField(source='user.contact_no')
    full_name = serializers.CharField(source='user.full_name')
    is_verified = serializers.BooleanField(source='user.is_verified')

    post_no = serializers.SerializerMethodField()
    self_relation = serializers.SerializerMethodField()
    self_designation = serializers.SerializerMethodField()
    personal_details = serializers.SerializerMethodField()
    residential_details = serializers.SerializerMethodField()
    professional_details = serializers.SerializerMethodField()
    documents = UserDocumentOutputSerializer(
        source='user.documents',
        many=True
    )

    class Meta:
        model = UserProfile
        fields = [
            'user_id', 'post_no', 'self_relation', 'photo', 'email', 'contact_no', 'full_name', 'is_verified', 'pet_name', 
            'father_name', 'gender', 'dob', 'birth_time', 'birth_place', 'blood_group', 'marital_status', 'marriage_date',
            'education', 'education_detail', 'expired_date',  'expired_time', 'expired_place', 'cremation_place',
            'personal_details', 'residential_details', 'professional_details', 'documents', 'self_designation'
        ]
    
    def __init__(self, *args, **kwargs):
        exclude = kwargs.pop('exclude', None)
        super().__init__(*args, **kwargs)

        if exclude:
            for field in exclude:
                self.fields.pop(field, None)
    
    def get_post_no(self, obj):
        context = self.context
        return context.get('post_no')

    def get_self_relation(self, obj):
        context = self.context
        self_relation = context.get('self_relation')
        if self_relation:
            return self_relation.name
        return None

    def get_self_designation(self, obj):
        context = self.context
        self_designation = context.get('self_designation')
        if self_designation:
            return {
                "id": self_designation.id,
                "name": self_designation.display_name
            }
        return None
    

    
    def get_personal_details(self, obj):
        try:
            personal_details_obj = obj.user.personal_details
            return {
                "personal_code": personal_details_obj.personal_code,
                "is_verified": personal_details_obj.is_verified,
                "nodes": get_level_node_mapping(personal_details_obj.node_mappings.all()),
            }
        except Exception:
            return None
    
    def get_residential_details(self, obj):
        try:
            residential_obj = obj.user.current_residential_details
            return {
                "residential_code": residential_obj.residential_code,
                "nodes": get_level_node_mapping(residential_obj.node_mappings.all()),
            }
        except Exception:
            return None
    
    def get_professional_details(self, obj):
        try:
            professional_details = obj.user.professional_details.all()
            result = []
            for detail in professional_details:
                if detail.residential_details:
                    residential_node_mapping = {
                        "residential_code": detail.residential_details.residential_code,
                        "nodes": get_level_node_mapping(detail.residential_details.node_mappings.all()),
                    }
                else:
                    residential_node_mapping = None

                result.append({
                    "id": detail.id,
                    "company": detail.business_family.name if detail.business_family else None,
                    "designation": {
                        "id": detail.designation.id,
                        "name": detail.designation.display_name
                    } if detail.designation else None,
                    "professional_code": detail.professional_code,
                    "joined_date": detail.joined_date,
                    "left_date": detail.left_date,
                    "experience": detail.experience,
                    "residential_details": residential_node_mapping,
                    "personal_details": {
                        "nodes": get_level_node_mapping(detail.personal_node_mappings.all())
                    },
                    "professional_details": {
                        "nodes": get_level_node_mapping(detail.professional_node_mappings.all())
                    },
                    "is_active": detail.is_active,
                })
            return result

        except Exception as e:
            print(e)
            return None


class UserListSerializer(serializers.ModelSerializer):
    profile_pic = serializers.ImageField(source='profile.photo')
    father_name = serializers.CharField(source='profile.father_name')
    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'contact_no', 'is_verified', 'user_category', 'father_name',
            'profile_pic'
        ]

class RelationTypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelationType
        fields = ['id', 'name', 'display_name', 'post_no']

class DesignationTypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignationType
        fields = ['id', 'name', 'display_name']


class BusinessFamilyListSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessFamily
        fields = ['id', 'name']


class BussinessFamilyDetailsOutputSerializer(serializers.ModelSerializer):
    residential_details = serializers.SerializerMethodField()
    stay_from = serializers.SerializerMethodField()
    stay_to = serializers.SerializerMethodField()
    family_members = serializers.SerializerMethodField()

    class Meta:
        model = BusinessFamily
        fields = ['name', 'residential_details', 'stay_from', 'stay_to', 'family_members']

    def get_residential_details(self, obj):
        try:
            resident_mapping = ResidentMapping.objects.get(business_family=obj)
            return {
                "residential_code": resident_mapping.residential_details.residential_code,
                "nodes": get_level_node_mapping(resident_mapping.residential_details.node_mappings.all())
            }
        except ResidentMapping.DoesNotExist:
            return None
        except Exception:
            return ValidationError("Something went wrong. Please try again.")

    def get_stay_from(self, obj):
        try:
            return ResidentMapping.objects.get(business_family=obj).stay_from
        except ResidentMapping.DoesNotExist:
            return None

    def get_stay_to(self, obj):
        try:
            return ResidentMapping.objects.get(business_family=obj).stay_to
        except ResidentMapping.DoesNotExist:
            return None
    
    def get_family_members(self, obj):
        try:
            family_members = obj.members.filter(user__is_deleted=False)
            family_members_lst = []

            for member in family_members:
                user_obj = member.user
                print(user_obj)
                user_details = UserDetailsOutputSerializer(
                    user_obj.profile,
                    exclude=['residential_details'],
                    context = {
                        'self_designation': member.self_designation_type,
                        'post_no': member.post_no,
                    }
                ).data   
                family_members_lst.append(user_details)
        except Exception as e:
            raise ValidationError("Something went wrong. Please try again.")
        
        return family_members_lst

# Family Tree Serializers

class FamilyTreeNodeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    gender = serializers.CharField(allow_null=True)
    relation = serializers.CharField()
    pidhi = serializers.IntegerField(allow_null=True)
    is_main_user = serializers.BooleanField()
    photo = serializers.CharField(allow_null=True)


class FamilyTreeEdgeSerializer(serializers.Serializer):
    from_user = serializers.IntegerField()
    to_user = serializers.IntegerField()
    relation = serializers.CharField()


class FamilyTreeResponseSerializer(serializers.Serializer):
    family_id = serializers.IntegerField()
    nodes = FamilyTreeNodeSerializer(many=True)
    edges = FamilyTreeEdgeSerializer(many=True)