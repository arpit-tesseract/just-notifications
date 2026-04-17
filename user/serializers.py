from rest_framework import serializers
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import *
from configuration.models import Dimension, Level, Node
from .utils import get_level_node_mapping

class ResidentialTypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResidentialType
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
        choices=['husband', 'wife', 'son', 'daughter', 'guest', 'worker'],
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
    relation = serializers.PrimaryKeyRelatedField(
        queryset = RelationType.objects.filter(is_active=True).exclude(
            name__in=['husband', 'wife', 'son', 'daughter', 'guest', 'worker']
        ), 
        many=True, required=True, allow_null=True
    )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        gender = attrs.get('gender')
        self_relation = attrs.get('self_relation')
        user_obj = attrs.get('user_id')
        contact_no = attrs.get('contact_no')
        email = attrs.get('email')

        if not user_obj:
            try:
                User.objects.get(contact_no=contact_no)
                raise serializers.ValidationError({"contact_no": "User with this contact number already exists."})
            except User.DoesNotExist:
                pass
        
        if email:
            try:
                if user_obj:
                    user_qs = User.objects.filter(email=email).exclude(id=user_obj.id)
                else:
                    user_qs = User.objects.filter(email=email)

                if user_qs.exists():
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
        return value


    def validate_personal_details(self, value):
        dimension_obj, _ = Dimension.objects.get_or_create(name="Personal")
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

    residential_type = serializers.PrimaryKeyRelatedField(
        queryset=ResidentialType.objects.filter(is_active=True)
    )

    residential_details = serializers.JSONField(required=True, allow_null=True)

    family_members = UserDetailsInputSerializer(many=True, required=True, allow_null=True)


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


    def validate_family_members(self, value):
        if value:
            # Count how many members have the relation "husband"
            husband_count = sum(1 for member in value if member.get('self_relation') == "husband")
            
            # Check the count and raise appropriate errors
            if husband_count == 0:
                raise serializers.ValidationError({"family_members": "Husband is required."})
            elif husband_count > 1:
                raise serializers.ValidationError({"family_members": "Only one husband is allowed."})
                
        return value


class RegistrationOutputSerializer(serializers.Serializer):
    registration_user = serializers.SerializerMethodField()
    residential_type = serializers.SerializerMethodField()
    user_category = serializers.SerializerMethodField()
    residential_details = serializers.SerializerMethodField()
    family_members = serializers.SerializerMethodField()

    def get_registration_user(self, family_obj):
        context = self.context
        return context.get('registration_user').id
        
    
    def get_user_category(self, family_obj):
        try:
            main_family_member_obj = family_obj.members.filter(is_main_user=True).first()
        except FamilyMember.DoesNotExist:
            raise ValidationError("Something went wrong. Please try again.")
        except Exception as e:
            raise ValidationError("Something went wrong. Please try again: ")
        return main_family_member_obj.user.user_category
    

    def get_residential_type(self, family_obj):
        context = self.context
        return context.get('residential_type').id


    def get_residential_details(self, family_obj):
        context = self.context
        residential_details = context.get('residential_details')
        node_data = residential_details.nodes
        return get_level_node_mapping(node_data)
        
    
    def get_family_members(self, family_obj):
        context = self.context
        registration_user_obj = context.get('registration_user')
        # residential_type_obj = context.get('residential_type')

        main_user_obj = family_obj.members.filter(is_main_user=True).first().user
        family_members_lst = []
        try:
            family_members = family_obj.members.filter(user__is_deleted=False)
            for member in family_members:
                user_obj = member.user
                print(user_obj)
                user_details = UserDetailsOutputSerializer(
                    user_obj.profile,
                    exclude=['residential_details']
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

    self_relation = serializers.SerializerMethodField()
    personal_details = serializers.SerializerMethodField()
    residential_details = serializers.SerializerMethodField()
    documents = UserDocumentOutputSerializer(
        source='user.documents',
        many=True
    )

    class Meta:
        model = UserProfile
        fields = [
            'user_id', 'self_relation', 'photo', 'email', 'contact_no', 'full_name', 'is_verified', 'pet_name', 
            'father_name', 'gender', 'dob', 'blood_group', 'marital_status', 'expired_date', 
            'personal_details', 'residential_details', 'documents'
        ]
    
    def __init__(self, *args, **kwargs):
        exclude = kwargs.pop('exclude', None)
        super().__init__(*args, **kwargs)

        if exclude:
            for field in exclude:
                self.fields.pop(field, None)

    def get_self_relation(self, obj):
        family_member_obj = FamilyMember.objects.filter(user=obj.user).first()
        return family_member_obj.self_relation_type.name
    
    def get_personal_details(self, obj):
        try:
            # nodes_data is {"1": 1, "2": 5, ...} where value is the Node ID
            nodes_data = obj.user.personal_details.nodes
            return get_level_node_mapping(nodes_data)

        except Exception:
            return None
    
    def get_residential_details(self, obj):
        try:
            # nodes_data is {"1": 1, "2": 5, ...} where value is the Node ID
            nodes_data = obj.user.current_residential_details.nodes
            return get_level_node_mapping(nodes_data)

        except Exception:
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
        fields = ['id', 'display_name']