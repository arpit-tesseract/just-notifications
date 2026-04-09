from rest_framework import serializers
from django.utils import timezone

from .models import *
from configuration.models import Dimension, Level, Node


class FamilyTypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyType
        fields = ['id', 'display_name']


class DocumentTypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = ['id', 'display_name', 'is_required']
        

class UserDetailsInputSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset = User.objects.all(), 
        required=True, allow_null=True
    )
    self_relation = serializers.ChoiceField(
        choices=['husband', 'wife', 'son', 'daughter', 'guest', 'workers'],
        required=True, allow_null=False
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
    dob = serializers.DateField(required=True, allow_null=True)
    blood_group = serializers.ChoiceField(
        choices=UserProfile.BLOOD_GROUP_CHOICES,
        required=True, allow_null=True
    )
    marital_status = serializers.ChoiceField(
        choices=UserProfile.MARITAL_STATUS_CHOICES,
        required=True, allow_null=True
    )
    expired_date = serializers.DateField(required=True, allow_null=True)
    personal_details = serializers.JSONField(required=True, allow_null=True)
    residential_details = serializers.JSONField(required=True, allow_null=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        gender = attrs.get('gender')
        self_relation = attrs.get('self_relation')
        user_id = attrs.get('user_id')
        contact_no = attrs.get('contact_no')
        email = attrs.get('email')

        if user_id:
            try:
                user_obj = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise serializers.ValidationError({"user_id": "User with this ID does not exist."})

        try:
            if user_id:
                user_obj = User.objects.filter(contact_no=contact_no).exclude(id=user_id)
            else:
                user_obj = User.objects.filter(contact_no=contact_no)

            if user_obj.exists():
                raise serializers.ValidationError({"contact_no": "User with this contact number already exists."})
        except User.DoesNotExist:
            pass
        
        if email:
            try:
                if user_id:
                    user_obj = User.objects.filter(email=email).exclude(id=user_id)
                else:
                    user_obj = User.objects.filter(email=email)

                if user_obj.exists():
                    raise serializers.ValidationError({"email": "User with this email already exists."})
            except User.DoesNotExist:
                pass


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
        print(value)
        return value


    def validate_personal_details(self, value):
        dimension_obj, _ = Dimension.objects.get_or_create(name="Personal")
        return self._validate_node_json(value, dimension_obj)
                  
    
    def validate_residential_details(self, value):
        dimension_obj, _ = Dimension.objects.get_or_create(name="Residential")
        return self._validate_node_json(value, dimension_obj)
    
    

class RegistrationInputSerializer(serializers.Serializer):
    registration_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=True,
        allow_null=True
    )
    user_category = serializers.ChoiceField(
        choices=User.USER_CATEGORY_CHOICES
    )
    # residential_type = serializers.ChoiceField(
    #     choices=['current', 'owner', 'permanent', 'native', 'inlaws', 'maternal', 'business']
    # )
    family_type = serializers.PrimaryKeyRelatedField(
        queryset=FamilyType.objects.filter(is_active=True)
    )
    family_members = UserDetailsInputSerializer(many=True, required=True, allow_null=False)


