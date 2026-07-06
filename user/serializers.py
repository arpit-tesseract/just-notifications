from rest_framework import serializers
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import *
from phonenumber_field.serializerfields import PhoneNumberField as BasePhoneNumberField

class PhoneNumberField(BasePhoneNumberField):
    def to_internal_value(self, data):
        phone_number = super().to_internal_value(data)
        return str(phone_number) if phone_number else phone_number

from configuration.models import Dimension, Level, Node
from .utils import get_level_node_mapping, validate_dimension_nodes, get_all_role_descendant_names
from common.validators import validate_dob, validate_marriage_date, validate_expired_date, validate_email_format, validate_gstin
class LoginPhoneInputSerializer(serializers.Serializer):
    contact_no = PhoneNumberField(required=True)


class LoginPhoneOTPInputSerializer(serializers.Serializer):
    contact_no = PhoneNumberField(required=True)
    otp = serializers.IntegerField(
        min_value = 1000,   # min value as 1000
        max_value = 9999    # max value as 9999
    )

class LoginInputSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True, validators=[validate_email_format])
    password = serializers.CharField(write_only=True)


class RoleDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ['id', 'name', 'display_name']


# This Serializer Use after loggin success
class UserBasicDetailsOutputSerializer(serializers.ModelSerializer):
    roles = RoleDropdownSerializer(many=True)
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


class ResidentialTypeDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResidentialType
        fields = ['id', 'name', 'display_name']


class DocumentTypeDropdownSerializer(serializers.ModelSerializer):
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
    email = serializers.EmailField(required=True, allow_null=True, validators=[validate_email_format])
    contact_no = PhoneNumberField(required=True, allow_null=False)
    full_name = serializers.CharField(required=True, allow_null=False)
    pet_name = serializers.CharField(required=True, allow_null=True)
    father_name = serializers.CharField(required=True, allow_null=True)
    gender = serializers.ChoiceField(
        choices=UserProfile.GENDER_CHOICES,
        required=True, allow_null=True
    )
    post_no = serializers.DecimalField(max_digits=10, decimal_places=2, required=True, allow_null=True)
    dob = serializers.DateField(required=True, allow_null=True, validators=[validate_dob])
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
    marriage_date = serializers.DateField(required=True, allow_null=True, validators=[validate_marriage_date])
    education = serializers.ChoiceField(
        choices=UserProfile.EDUCATION_CHOICES,
        required=True, allow_null=True
    )
    education_detail = serializers.CharField(required=True, allow_null=True)

    expired_date = serializers.DateField(required=True, allow_null=True, validators=[validate_expired_date])
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
        
        dob = attrs.get('dob')
        marriage_date = attrs.get('marriage_date')
        expired_date = attrs.get('expired_date')
        
        if dob:
            if marriage_date and marriage_date < dob:
                raise serializers.ValidationError({"marriage_date": "Marriage date cannot be before Date of Birth."})
            if expired_date and expired_date < dob:
                raise serializers.ValidationError({"expired_date": "Expired date cannot be before Date of Birth."})
        
        return attrs
    

    
    def validate_personal_details(self, value):
        dimension_obj, _ = Dimension.objects.get_or_create(name="Personal")
        return validate_dimension_nodes(value, dimension_obj)
    
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

            validate_dimension_nodes(residential_nodes, residential_dimension_obj)
            validate_dimension_nodes(personal_nodes, personal_dimension_obj)
            validate_dimension_nodes(professional_nodes, professional_dimension_obj)

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
        return validate_dimension_nodes(value, dimension_obj)


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


class UserSuggestionDropdownSerializer(serializers.ModelSerializer):
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
    email = serializers.EmailField(source='user.email')
    contact_no = PhoneNumberField(source='user.contact_no')
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
                    "salary": detail.salary,
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
    roles = RoleDropdownSerializer(many=True)
    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'contact_no', 'is_verified', 'user_category', 'father_name',
            'profile_pic', 'roles'
        ]

class RelationTypeDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelationType
        fields = ['id', 'name', 'display_name', 'post_no']

class DesignationTypeDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignationType
        fields = ['id', 'name', 'display_name', 'post_no']


class BusinessFamilyDropdownSerializer(serializers.ModelSerializer):
    residential_code = serializers.SerializerMethodField()

    class Meta:
        model = BusinessFamily
        fields = ['id', 'name', 'is_verified', 'residential_code']
        
    def get_residential_code(self, obj):
        resident_mapping = ResidentMapping.objects.filter(business_family=obj).first()
        if resident_mapping and resident_mapping.residential_details:
            return resident_mapping.residential_details.residential_code
        return None


class BussinessFamilyDetailsOutputSerializer(serializers.ModelSerializer):
    residential_details = serializers.SerializerMethodField()
    stay_from = serializers.SerializerMethodField()
    stay_to = serializers.SerializerMethodField()
    family_members = serializers.SerializerMethodField()

    class Meta:
        model = BusinessFamily
        fields = ['name', 'is_verified', 'residential_details', 'stay_from', 'stay_to', 'family_members']

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



# ===========================================
# Merchant Registration Serializers
# ===========================================

class BusinessMemberProfessionalDetailsInputSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset = UserProfessionalDetails.objects.all(), required=True, allow_null=True)
    professional_details = serializers.JSONField(required=True, allow_null=True)
    designation = serializers.PrimaryKeyRelatedField(
        queryset = DesignationType.objects.filter(is_active=True),
        required=True, allow_null=True 
    )
    joined_date = serializers.DateField(required=True, allow_null=True)
    left_date = serializers.DateField(required=False, allow_null=True)
    experience = serializers.CharField(required=False, allow_null=True)
    salary = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        joined_date = attrs.get("joined_date")
        left_date = attrs.get("left_date")
        
        if joined_date and left_date and joined_date > left_date:
            raise serializers.ValidationError({
                "joined_date": "joined_date cannot be greater than left_date."
            })
            
        return attrs

class BusinessMemberInputSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset = User.objects.all(), 
        required=True, allow_null=True
    )
    self_designation_type = serializers.PrimaryKeyRelatedField(
        queryset = DesignationType.objects.filter(is_active=True), 
    )
    email = serializers.EmailField(required=True, allow_null=True, validators=[validate_email_format])
    contact_no = PhoneNumberField(required=True, allow_null=False)
    full_name = serializers.CharField(required=True, allow_null=False)
    pet_name = serializers.CharField(required=True, allow_null=True)
    father_name = serializers.CharField(required=True, allow_null=True)
    gender = serializers.ChoiceField(
        choices=UserProfile.GENDER_CHOICES,
        required=True, allow_null=True
    )
    post_no = serializers.DecimalField(max_digits=10, decimal_places=2, required=True, allow_null=True)
    dob = serializers.DateField(required=True, allow_null=True, validators=[validate_dob])
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
    marriage_date = serializers.DateField(required=True, allow_null=True, validators=[validate_marriage_date])
    education = serializers.ChoiceField(
        choices=UserProfile.EDUCATION_CHOICES,
        required=True, allow_null=True
    )
    education_detail = serializers.CharField(required=True, allow_null=True)

    expired_date = serializers.DateField(required=True, allow_null=True, validators=[validate_expired_date])
    expired_time = serializers.TimeField(required=True, allow_null=True)
    expired_place = serializers.CharField(required=True, allow_null=True)
    cremation_place = serializers.CharField(required=True, allow_null=True)

    personal_details = serializers.JSONField(required=True, allow_null=True)
    residential_details = serializers.JSONField(required=True, allow_null=True)
    professional_details = BusinessMemberProfessionalDetailsInputSerializer()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        gender = attrs.get('gender')
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
        
        dob = attrs.get('dob')
        marriage_date = attrs.get('marriage_date')
        expired_date = attrs.get('expired_date')
        
        if dob:
            if marriage_date and marriage_date < dob:
                raise serializers.ValidationError({"marriage_date": "Marriage date cannot be before Date of Birth."})
            if expired_date and expired_date < dob:
                raise serializers.ValidationError({"expired_date": "Expired date cannot be before Date of Birth."})
        
        return attrs
    
    def validate_personal_details(self, value):
        dimension_obj, _ = Dimension.objects.get_or_create(name="Personal")
        return validate_dimension_nodes(value, dimension_obj)

    def validate_residential_details(self, value):
        dimension_obj, _ = Dimension.objects.get_or_create(name="Residential")
        return validate_dimension_nodes(value, dimension_obj)
    
    def validate_professional_details(self, value):
        dimension_obj, _ = Dimension.objects.get_or_create(name="Professional")
        # value is the dictionary from BusinessMemberProfessionalDetailsInputSerializer
        if value and 'professional_details' in value:
            validate_dimension_nodes(value['professional_details'], dimension_obj)
        return value


class BusinessOperatingHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessOperatingHours
        fields = ['day_of_week', 'open_time', 'close_time']
        
    def validate(self, attrs):
        attrs = super().validate(attrs)
        open_time = attrs.get('open_time')
        close_time = attrs.get('close_time')
        
        if open_time and close_time and open_time >= close_time:
            raise serializers.ValidationError({
                "close_time": "Closing time must be strictly after opening time."
            })
        return attrs



class BusinessFamilyInputSerializer(serializers.ModelSerializer):
    residential_details = serializers.JSONField()
    professional_details = serializers.JSONField()
    operating_hours = BusinessOperatingHoursSerializer(many=True, required=True, allow_null=True)

    class Meta:
        model = BusinessFamily
        fields = [
            'id', 'name', 'company_type', 'registration_no', 'pan_no', 'gstin',
            'business_type', 'company_size',
            'email', 'contact_no', 'website', 'established_year',
            'latitude', 'longitude',
            'residential_details', 'professional_details', 'operating_hours'
        ]
        extra_kwargs = {
            'email': {'validators': [validate_email_format]},
            'gstin': {'validators': [validate_gstin]},
        }


class BusienssRegistrationInputSerializer(serializers.Serializer):
    role = serializers.SlugRelatedField(
        queryset=UserRole.objects.filter(is_active=True, parent=None),
        slug_field="name"
    )
    sub_role = serializers.PrimaryKeyRelatedField(queryset=UserRole.objects.filter(is_active=True))
    business_family = BusinessFamilyInputSerializer()
    residential_type = serializers.PrimaryKeyRelatedField(queryset=ResidentialType.objects.filter(is_active=True))
    
    business_members = BusinessMemberInputSerializer(many=True)
    
    
    def validate(self, attrs):
        attrs = super().validate(attrs)
        role_obj = attrs.get('role')
        sub_role_obj = attrs.get('sub_role')
        residential_type = attrs.get('residential_type')

        errors = {}

        if sub_role_obj.parent != role_obj:
            errors['sub_role'] = "Invalid sub role."

        if not residential_type.roles.filter(id=role_obj.id).exists():
            errors['residential_type'] = "Invalid residential type."

        if errors:
            raise serializers.ValidationError(errors)

        # Check for duplicate contact_no or email within the payload itself
        business_members = attrs.get('business_members', [])
        seen_contact_nos = set()
        seen_emails = set()
        member_errors = {}

        for index, member in enumerate(business_members):
            contact_no = member.get('contact_no')
            email = member.get('email')
            m_errors = {}

            if contact_no:
                if contact_no in seen_contact_nos:
                    m_errors["contact_no"] = "This contact number is already used by another member in this request."
                else:
                    seen_contact_nos.add(contact_no)
            
            if email:
                if email in seen_emails:
                    m_errors["email"] = "This email is already used by another member in this request."
                else:
                    seen_emails.add(email)
            
            if m_errors:
                member_errors[index] = m_errors

        if member_errors:
            raise serializers.ValidationError({"business_members": member_errors})

        return attrs


class BusinessRegisterOutputSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    sub_role = serializers.SerializerMethodField()
    residential_type = serializers.SerializerMethodField()
    business_family = serializers.SerializerMethodField()
    business_members = serializers.SerializerMethodField()

    class Meta:
        model = BusinessFamily
        fields = ['role', 'sub_role', 'residential_type', 'business_family', 'business_members']

    def get_role(self, obj):
        return obj.role.name if obj.role else None

    def get_sub_role(self, obj):
        return obj.sub_role.id if obj.sub_role else None

    def get_residential_type(self, obj):
        resident_mapping = ResidentMapping.objects.filter(business_family=obj).first()
        return resident_mapping.residential_type.id if resident_mapping and resident_mapping.residential_type else None

    def get_business_family(self, obj):
        resident_mapping = ResidentMapping.objects.filter(business_family=obj).first()
        residential_nodes = get_level_node_mapping(resident_mapping.residential_details.node_mappings.all()) if resident_mapping and resident_mapping.residential_details else {}
        
        prof_nodes = get_level_node_mapping(obj.professional_node_mappings.all())
        
        operating_hours = BusinessOperatingHoursSerializer(
            obj.businessoperatinghours_set.all(), many=True
        ).data

        return {
            "id": obj.id,
            "name": obj.name,
            "company_type": obj.company_type,
            "registration_no": obj.registration_no,
            "pan_no": obj.pan_no,
            "gstin": obj.gstin,
            "business_type": obj.business_type,
            "company_size": obj.company_size,
            "email": obj.email,
            "contact_no": str(obj.contact_no) if obj.contact_no else None,
            "website": obj.website,
            "established_year": obj.established_year,
            "latitude": obj.latitude,
            "longitude": obj.longitude,
            "residential_details": residential_nodes,
            "professional_details": prof_nodes,
            "operating_hours": operating_hours,
        }

    def get_business_members(self, obj):
        members = BusinessFamilyMember.objects.filter(business_family=obj, user__is_deleted=False)
        result = []
        for member in members:
            user = member.user
            profile = user.profile if hasattr(user, 'profile') else None
            personal_details = user.personal_details if hasattr(user, 'personal_details') else None
            
            prof_detail = UserProfessionalDetails.objects.filter(user=user, business_family=obj).first()

            prof_detail_data = {}
            member_residential_nodes = {}
            if prof_detail:
                if prof_detail.residential_details:
                    member_residential_nodes = get_level_node_mapping(prof_detail.residential_details.node_mappings.all())
                
                prof_detail_data = {
                    "id": prof_detail.id,
                    "designation": prof_detail.designation.id if prof_detail.designation else None,
                    "professional_details": get_level_node_mapping(prof_detail.professional_node_mappings.all()),
                    "joined_date": prof_detail.joined_date,
                    "left_date": prof_detail.left_date,
                    "experience": prof_detail.experience,
                    "salary": prof_detail.salary,
                    "is_active": prof_detail.is_active,
                }
            
            member_data = {
                "user_id": user.id,
                "self_designation_type": member.self_designation_type.id if member.self_designation_type else None,
                "post_no": member.post_no,
                "full_name": user.full_name,
                "email": user.email,
                "contact_no": str(user.contact_no) if user.contact_no else None,
                "pet_name": profile.pet_name if profile else None,
                "father_name": profile.father_name if profile else None,
                "gender": profile.gender if profile else None,
                "dob": profile.dob if profile else None,
                "birth_time": profile.birth_time if profile else None,
                "birth_place": profile.birth_place if profile else None,
                "blood_group": profile.blood_group if profile else None,
                "marital_status": profile.marital_status if profile else None,
                "marriage_date": profile.marriage_date if profile else None,
                "education": profile.education if profile else None,
                "education_detail": profile.education_detail if profile else None,
                "expired_date": profile.expired_date if profile else None,
                "expired_time": profile.expired_time if profile else None,
                "expired_place": profile.expired_place if profile else None,
                "cremation_place": profile.cremation_place if profile else None,
            }
            
            member_data["personal_details"] = get_level_node_mapping(personal_details.node_mappings.all()) if personal_details else {}
            member_data["residential_details"] = member_residential_nodes
            member_data["professional_details"] = prof_detail_data
            
            result.append(member_data)
        
        return result


class BusinessMemberPayloadSuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = []  # We will manually map everything to match the input payload

    def to_representation(self, user):
        profile = user.profile if hasattr(user, 'profile') else None
        personal_details = user.personal_details if hasattr(user, 'personal_details') else None
        
        business_id = self.context.get('business_id')
        residential_code = self.context.get('residential_code')
        
        # Try to find the member record if business_id is given
        member = None
        if business_id:
            member = BusinessFamilyMember.objects.filter(user=user, business_family_id=business_id).first()

        # Find the relevant professional details
        filters = Q(user=user, is_active=True)
        conditions = Q()
        if business_id:
            conditions |= Q(business_family_id=business_id)
        if residential_code:
            conditions |= Q(residential_details__residential_code=residential_code)
        
        prof_detail = UserProfessionalDetails.objects.filter(filters & conditions).first()

        prof_detail_data = {}
        member_residential_nodes = {}
        
        if prof_detail:
            if prof_detail.residential_details:
                member_residential_nodes = get_level_node_mapping(prof_detail.residential_details.node_mappings.all())
            
            prof_detail_data = {
                "id": prof_detail.id,
                "designation": prof_detail.designation.id if prof_detail.designation else None,
                "professional_details": get_level_node_mapping(prof_detail.professional_node_mappings.all()),
                "joined_date": prof_detail.joined_date,
                "left_date": prof_detail.left_date,
                "experience": prof_detail.experience,
                "salary": prof_detail.salary,
                "is_active": prof_detail.is_active,
            }

        member_data = {
            "user_id": user.id,
            "self_designation_type": member.self_designation_type.id if (member and member.self_designation_type) else None,
            "post_no": member.post_no if member else 0,
            "full_name": user.full_name,
            "email": user.email,
            "contact_no": str(user.contact_no) if user.contact_no else None,
        }
        
        if profile:
            member_data.update({
                "pet_name": profile.pet_name,
                "father_name": profile.father_name,
                "gender": profile.gender,
                "dob": profile.dob,
                "birth_time": profile.birth_time,
                "birth_place": profile.birth_place,
                "blood_group": profile.blood_group,
                "marital_status": profile.marital_status,
                "marriage_date": profile.marriage_date,
                "education": profile.education,
                "education_detail": profile.education_detail,
                "expired_date": profile.expired_date,
                "expired_time": profile.expired_time,
                "expired_place": profile.expired_place,
                "cremation_place": profile.cremation_place,
            })
        
        member_data["personal_details"] = get_level_node_mapping(personal_details.node_mappings.all()) if personal_details else {}
        member_data["residential_details"] = member_residential_nodes
        member_data["professional_details"] = prof_detail_data
        
        return member_data




class AdminMemberInputSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset = User.objects.all(), 
        required=True, allow_null=True
    )
    self_sub_role = serializers.PrimaryKeyRelatedField(
        queryset = UserRole.objects.filter(is_active=True), 
    )
    email = serializers.EmailField(required=True, allow_null=True, validators=[validate_email_format])
    contact_no = PhoneNumberField(required=True, allow_null=False)
    full_name = serializers.CharField(required=True, allow_null=False)
    pet_name = serializers.CharField(required=True, allow_null=True)
    father_name = serializers.CharField(required=True, allow_null=True)
    gender = serializers.ChoiceField(
        choices=UserProfile.GENDER_CHOICES,
        required=True, allow_null=True
    )
    dob = serializers.DateField(required=True, allow_null=True, validators=[validate_dob])
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
    marriage_date = serializers.DateField(required=True, allow_null=True, validators=[validate_marriage_date])

    education = serializers.ChoiceField(
        choices=UserProfile.EDUCATION_CHOICES,
        required=True, allow_null=True
    )
    education_detail = serializers.CharField(required=True, allow_null=True)

    expired_date = serializers.DateField(required=True, allow_null=True, validators=[validate_expired_date])
    expired_time = serializers.TimeField(required=True, allow_null=True)
    expired_place = serializers.CharField(required=True, allow_null=True)
    cremation_place = serializers.CharField(required=True, allow_null=True)

    personal_details = serializers.JSONField(required=True, allow_null=True)
    residential_details = serializers.JSONField(required=True, allow_null=True)
    professional_details = BusinessMemberProfessionalDetailsInputSerializer()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        gender = attrs.get('gender')
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
        
        dob = attrs.get('dob')
        marriage_date = attrs.get('marriage_date')
        expired_date = attrs.get('expired_date')
        
        if dob:
            if marriage_date and marriage_date < dob:
                raise serializers.ValidationError({"marriage_date": "Marriage date cannot be before Date of Birth."})
            if expired_date and expired_date < dob:
                raise serializers.ValidationError({"expired_date": "Expired date cannot be before Date of Birth."})
        
        return attrs
    
    def validate_personal_details(self, value):
        dimension_obj, _ = Dimension.objects.get_or_create(name="Personal")
        return validate_dimension_nodes(value, dimension_obj)

    def validate_residential_details(self, value):
        dimension_obj, _ = Dimension.objects.get_or_create(name="Residential")
        return validate_dimension_nodes(value, dimension_obj)
    
    def validate_professional_details(self, value):
        dimension_obj, _ = Dimension.objects.get_or_create(name="Professional")
        # value is the dictionary from BusinessMemberProfessionalDetailsInputSerializer
        if value and 'professional_details' in value:
            validate_dimension_nodes(value['professional_details'], dimension_obj)
        return value
    




class AdminRegistrationInputSerializer(serializers.Serializer):
    role = serializers.SlugRelatedField(
        queryset=UserRole.objects.filter(name="admin", is_active=True),
        slug_field="name"
    )
    admin_members = AdminMemberInputSerializer(many=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        role_obj = attrs.get('role')

        errors = {}

        # Check for duplicate contact_no or email within the payload itself
        admin_members = attrs.get('admin_members', [])
        seen_contact_nos = set()
        seen_emails = set()
        member_errors = {}

        for index, member in enumerate(admin_members):
            contact_no = member.get('contact_no')
            email = member.get('email')
            m_errors = {}

            if contact_no:
                if contact_no in seen_contact_nos:
                    m_errors["contact_no"] = "This contact number is already used by another member in this request."
                else:
                    seen_contact_nos.add(contact_no)
            
            if email:
                if email in seen_emails:
                    m_errors["email"] = "This email is already used by another member in this request."
                else:
                    seen_emails.add(email)
            
            if m_errors:
                member_errors[index] = m_errors

        if member_errors:
            raise serializers.ValidationError({"admin_members": member_errors})

        return attrs


class AdminRegistrationOutputSerializer(serializers.Serializer):
    role = serializers.SerializerMethodField()
    admin_members = serializers.SerializerMethodField()

    def get_role(self, obj):
        # Expects obj to be a dictionary like {"role": UserRole, "users": [User]}
        role_obj = obj.get("role")
        return role_obj.name if role_obj else None

    def get_admin_members(self, obj):
        users = obj.get("users", [])
        result = []
        for user in users:
            profile = user.profile if hasattr(user, 'profile') else None
            personal_details = user.personal_details if hasattr(user, 'personal_details') else None
            
            # Find the admin sub-role assigned to this user
            admin_role_names = get_all_role_descendant_names('admin')
            sub_role = user.roles.filter(name__in=admin_role_names).first()
            
            # Find professional details (assuming first active one for admin)
            prof_detail = UserProfessionalDetails.objects.filter(user=user, is_active=True).first()

            prof_detail_data = {}
            member_residential_nodes = {}
            if prof_detail:
                if prof_detail.residential_details:
                    member_residential_nodes = get_level_node_mapping(prof_detail.residential_details.node_mappings.all())
                
                prof_detail_data = {
                    "id": prof_detail.id,
                    "designation": prof_detail.designation.id if prof_detail.designation else None,
                    "professional_details": get_level_node_mapping(prof_detail.professional_node_mappings.all()),
                    "joined_date": prof_detail.joined_date,
                    "left_date": prof_detail.left_date,
                    "experience": prof_detail.experience,
                    "salary": prof_detail.salary,
                    "is_active": prof_detail.is_active,
                }
            
            member_data = {
                "user_id": user.id,
                "self_sub_role": sub_role.id if sub_role else None,
                "full_name": user.full_name,
                "email": user.email,
                "contact_no": str(user.contact_no) if user.contact_no else None,
                "pet_name": profile.pet_name if profile else None,
                "father_name": profile.father_name if profile else None,
                "gender": profile.gender if profile else None,
                "dob": profile.dob if profile else None,
                "birth_time": profile.birth_time if profile else None,
                "birth_place": profile.birth_place if profile else None,
                "blood_group": profile.blood_group if profile else None,
                "marital_status": profile.marital_status if profile else None,
                "marriage_date": profile.marriage_date if profile else None,
                "education": profile.education if profile else None,
                "education_detail": profile.education_detail if profile else None,
                "expired_date": profile.expired_date if profile else None,
                "expired_time": profile.expired_time if profile else None,
                "expired_place": profile.expired_place if profile else None,
                "cremation_place": profile.cremation_place if profile else None,
            }
            
            member_data["personal_details"] = get_level_node_mapping(personal_details.node_mappings.all()) if personal_details else {}
            member_data["residential_details"] = member_residential_nodes
            member_data["professional_details"] = prof_detail_data
            
            result.append(member_data)
        
        return result


class AdminResidentialResidentialNodeAssignmentItemSerializer(serializers.Serializer):
    level_id = serializers.PrimaryKeyRelatedField(queryset=Level.objects.all(), source='level')
    node_id = serializers.PrimaryKeyRelatedField(queryset=Node.objects.all(), source='node')

    def validate(self, attrs):
        level_obj = attrs.get('level')
        node_obj = attrs.get('node')
        if node_obj.level != level_obj:
            raise serializers.ValidationError({"node_id": "Node does not belong to the specified level."})
        return attrs

class AdminResidentialNodeAssignmentInputSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )
    assignments = AdminResidentialResidentialNodeAssignmentItemSerializer(many=True, required=True)

    def validate_user_id(self, value):
        if not value.roles.filter(parent__name="admin").exists():
            raise serializers.ValidationError(
                "Invalid User."
            )
        return value

class AdminResidentialNodeAssignmentOutputSerializer(serializers.ModelSerializer):
    level = serializers.SerializerMethodField()
    node = serializers.SerializerMethodField()

    class Meta:
        model = AdminResidentialNodeAssignment
        fields = ['level', 'node']

    def get_level(self, obj):
        return {"id": obj.level.id, "name": obj.level.name} if obj.level else None

    def get_node(self, obj):
        return {"id": obj.node.id, "name": obj.node.name} if obj.node else None