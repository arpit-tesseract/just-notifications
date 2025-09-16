# serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import *
from configuration import models as configm
# from configuration.models import Accesses, PermissionAction, PermissionModule

class RoomMembersDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomMembersDetail
        fields = ['id', 'member_name']
        extra_kwargs = {'id': {'read_only': True}}

class RoomDetailSerializer(serializers.ModelSerializer):
    room_members = RoomMembersDetailSerializer(many=True, required=False)
    room_flash = serializers.PrimaryKeyRelatedField(
        queryset=configm.RoomFlash.objects.all()
    )

    class Meta:
        model = RoomDetail
        fields = ['id', 'room_name', 'room_member_count', 'room_flash', 'room_members']
        extra_kwargs = {'id': {'read_only': True}}

    def create(self, validated_data):
        members_data = validated_data.pop("room_members", [])
        address = self.context.get("address")
        room_detail = RoomDetail.objects.create(address=address, **validated_data)
        for member in members_data:
            RoomMembersDetail.objects.create(room_detail=room_detail, **member)
        return room_detail

class AddressSerializer(serializers.ModelSerializer):
    room_details = RoomDetailSerializer(many=True, required=False)
    
    class Meta:
        model = Address
        fields = ['id', 'block_number', 'floor', 'room_count', 'house_number', 'main_person', 'mobile_number', 'room_details']
        extra_kwargs = {'id': {'read_only': True}}

    def create(self, validated_data):
        room_details_data = validated_data.pop("room_details", [])
        address = Address.objects.create(**validated_data)
        for room in room_details_data:
            serializer = RoomDetailSerializer(data=room, context={"address": address})
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return address

class RelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relation
        fields = ['id', 'designation', 'designation_number', 'real_name', 'pet_name', 'father_name', 'mobile', 'photo', 'date_of_birth', 'blood_group']
        extra_kwargs = {'id': {'read_only': True}}

class PersonalTableSerializer(serializers.ModelSerializer):
    relations = RelationSerializer(many=True, required=False)
    
    class Meta:
        model = PersonalTable
        fields = ['id', 'religion', 'sampraday', 'panth', 'varna', 'caste', 'subcaste', 'gotra', 'subgotra', 'pidhi', 'relations', 'personal_code']
        extra_kwargs = {'id': {'read_only': True}}

class ReportCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportCard
        fields = ['id', 'input_diet', 'input_quantity', 'input_rate', 'gender', 'colour', 'height', 'length', 'width', 'volume', 'used_item', 'used_rate', 'used_qunatity', 'capacity']
        extra_kwargs = {'id': {'read_only': True}}

class ProfessionalDetailSerializer(serializers.ModelSerializer):
    report_cards = ReportCardSerializer(many=True, required=False)
    
    class Meta:
        model = ProfessionalDetail
        fields = ['id', 'section', 'classs', 'category', 'subcategory', 'sector', 'subsector', 'department', 'subdepartment', 'type', 'brand', 'postmodel', 'pay_scale', 'mfg_dt_time', 'mfg_life', 'report_cards', 'professional_code']
        extra_kwargs = {'id': {'read_only': True}}

class ResidentialDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResidentialDetail
        fields = ['id', 'continent', 'country', 'state', 'district', 'city', 'village', 'ward', 'society', 'block', 'houses', 'residential_code']
        extra_kwargs = {'id': {'read_only': True}}

# Serializer for user creation (registration)
class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    # Nested serializers for non-system users
    addresses = AddressSerializer(many=True, required=False)
    personal_details = PersonalTableSerializer(required=False)
    professional_details = ProfessionalDetailSerializer(required=False)
    residential_details = ResidentialDetailSerializer(required=False)
    
    class Meta:
        model = CustomUser
        fields = [
            'email', 'password', 'confirm_password', 'user_role', 'is_system_user',
            'date_of_birth', 'category_of_user',
            # System user allocation fields
            'continent_allocation', 'country_allocation', 'state_allocation',
            'district_allocation', 'city_allocation', 'village_allocation',
            'ward_allocation', 'block_allocation', 'society_allocation', 'access',
            # Nested data for non-system users
            'addresses', 'personal_details', 'professional_details', 'residential_details'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'access': {'required': False}
        }

    def validate(self, attrs):
        # Password confirmation
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError("Password and confirm password don't match.")
        
        is_system_user = attrs.get('is_system_user', False)
        
        if is_system_user:
            # For system users, allocation fields are required
            # required_allocations = ['access']  # At minimum, access is required
            # for field in required_allocations:
            #     if not attrs.get(field):
            #         raise serializers.ValidationError(f"{field} is required for system users.")
            pass
        else:
            # For non-system users, personal/professional details are required
            if not attrs.get('addresses'):
                raise serializers.ValidationError("Address details are required for non-system users.")
            
            if not attrs.get('personal_details'):
                raise serializers.ValidationError("Personal details are required for non-system users.")
            
            if not attrs.get('professional_details'):
                raise serializers.ValidationError("Professional details are required for non-system users.")
            
            if not attrs.get('residential_details'):
                raise serializers.ValidationError("Residential details are required for non-system users.")
        
        return attrs

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        # Remove nested data and password confirmation
        addresses_data = validated_data.pop('addresses', [])
        personal_data = validated_data.pop('personal_details', None)
        professional_data = validated_data.pop('professional_details', None)
        residential_data = validated_data.pop('residential_details', None)
        validated_data.pop('confirm_password')

        # Extract allocation/access data
        access_data = validated_data.pop('access', [])
        continent_allocation_data = validated_data.pop('continent_allocation', [])
        country_allocation_data = validated_data.pop('country_allocation', [])
        state_allocation_data = validated_data.pop('state_allocation', [])
        district_allocation_data = validated_data.pop('district_allocation', [])
        city_allocation_data = validated_data.pop('city_allocation', [])
        village_allocation_data = validated_data.pop('village_allocation',[])
        ward_allocation_data = validated_data.pop('ward_allocation', [])
        block_allocation_data = validated_data.pop('block_allocation', [])
        society_allocation_data = validated_data.pop('society_allocation', [])
        
        password = validated_data.pop('password')
        user = CustomUser.objects.create(**validated_data)
        
        # Set related allocations (For ManyToMany fields)
        # user.access.set(access_data)
        # user.access.set(continent_allocation_data)
        # user.access.set(country_allocation_data)
        # user.access.set(state_allocation_data)
        # user.access.set(district_allocation_data)
        # user.access.set(city_allocation_data)
        # user.access.set(village_allocation_data)
        # user.access.set(ward_allocation_data)
        # user.access.set(block_allocation_data)
        # user.access.set(society_allocation_data)
        
        # Map serializer/input variables to user model fields
        m2m_mapping = {
            "access": access_data,
            "continent_allocation": continent_allocation_data,
            "country_allocation": country_allocation_data,
            "state_allocation": state_allocation_data,
            "district_allocation": district_allocation_data,
            "city_allocation": city_allocation_data,
            "village_allocation": village_allocation_data,
            "ward_allocation": ward_allocation_data,
            "block_allocation": block_allocation_data,
            "society_allocation": society_allocation_data,
        }

        # Iterate and update
        for field, data in m2m_mapping.items():
            if data is not None:
                getattr(user, field).set(data)


        user.set_password(password)
        user.save()

        # Provider bydefault read access to system users
        # if user.is_system_user:
        #     default_modules = ["residential_details", "personal_details", "professional_details"]
        #     default_module_names = ['Residential Details', 'Personal Details', 'Professional Details']
        #     code = ['RD', 'PD', 'PRD']
        #     read_action, created = PermissionAction.objects.get_or_create(
        #         name="read",
        #         code='read'
        #         )
            
        #     for i in range(len(default_modules)):
        #         module, created = PermissionModule.objects.get_or_create(
        #             name=default_modules[i],
        #             display_name=default_module_names[i],
        #             code=code[i]
        #             )
        #         access, created = Accesses.objects.get_or_create(
        #             module=module,
        #             permission=read_action,
        #             defaults={"is_hidden": False, "on_hold": False, "hold_date": None},
        #         )
        #         user.access.add(access)
        
        # Create related objects for non-system users
        if not user.is_system_user:
            # Create personal details first (needed for relations)
            personal_table = None
            if personal_data:
                relations_data = personal_data.pop('relations', [])
                personal_table = PersonalTable.objects.create(user=user, **personal_data)
                
                # Create relations under personal table
                for relation_data in relations_data:
                    Relation.objects.create(personal_table=personal_table, **relation_data)

            # Create addresses with room details
            for address_data in addresses_data:
                room_details_data = address_data.pop('room_details', [])
                address = Address.objects.create(user=user, **address_data)
                
                # Create room details under address
                for room_data in room_details_data:
                    room_members_data = room_data.pop('room_members', [])
                    room = RoomDetail.objects.create(**room_data, address=address)
                    
                    # Create room members under room
                    for member_data in room_members_data:
                        RoomMembersDetail.objects.create(room=room, **member_data)
            
            # Create professional details
            if professional_data:
                ProfessionalDetail.objects.create(user=user, **professional_data)
            
            # Create residential details
            if residential_data:
                ResidentialDetail.objects.create(user=user, **residential_data)
        
        return user

# Serializer for user updates (without password confirmation)
class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    
    # Nested serializers for non-system users
    addresses = AddressSerializer(many=True, required=False)
    personal_details = PersonalTableSerializer(required=False)
    professional_details = ProfessionalDetailSerializer(required=False)
    residential_details = ResidentialDetailSerializer(required=False)
    
    class Meta:
        model = CustomUser
        fields = [
            'email', 'password', 'user_role', 'is_system_user',
            'date_of_birth', 'category_of_user', 'is_verified',
            # System user allocation fields
            'continent_allocation', 'country_allocation', 'state_allocation',
            'district_allocation', 'city_allocation', 'village_allocation',
            'ward_allocation', 'block_allocation', 'society_allocation', 'access',
            # Nested data for non-system users
            'addresses', 'personal_details', 'professional_details', 'residential_details'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
        }

    @transaction.atomic
    def update(self, instance, validated_data):
        # Handle password update
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        
        # Remove nested data for separate handling
        addresses_data = validated_data.pop('addresses', None)
        personal_data = validated_data.pop('personal_details', None)
        professional_data = validated_data.pop('professional_details', None)
        residential_data = validated_data.pop('residential_details', None)
        
        # Extract M2M fields 
        # to avoid this error at setattr(): TypeError at /api/user/users/4/
        # Direct assignment to the forward side of a many-to-many set is prohibited. Use access.set() instead.
        access_data = validated_data.pop('access', None)
        continent_data = validated_data.pop('continent_allocation', None)
        country_data = validated_data.pop('country_allocation', None)
        state_data = validated_data.pop('state_allocation', None)
        district_data = validated_data.pop('district_allocation', None)
        city_data = validated_data.pop('city_allocation', None)
        village_data = validated_data.pop('village_allocation', None)
        ward_data = validated_data.pop('ward_allocation', None)
        block_data = validated_data.pop('block_allocation', None)
        society_data = validated_data.pop('society_allocation', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update ManyToMany fields properly
        # Map your data variables to model fields
        m2m_mapping = {
            "access": access_data,
            "continent_allocation": continent_data,
            "country_allocation": country_data,
            "state_allocation": state_data,
            "district_allocation": district_data,
            "city_allocation": city_data,
            "village_allocation": village_data,
            "ward_allocation": ward_data,
            "block_allocation": block_data,
            "society_allocation": society_data,
        }

        # Iterate and update dynamically
        for field, data in m2m_mapping.items():
            if data is not None:
                getattr(instance, field).set(data)
        
        # Handle nested updates for non-system users
        if not instance.is_system_user:
            # Update addresses (replace all)
            if addresses_data is not None:
                instance.address_set.all().delete()  # Remove existing addresses
                for address_data in addresses_data:
                    room_details_data = address_data.pop('room_details', [])
                    address = Address.objects.create(user=instance, **address_data)
                    
                    # Create room details
                    for room_data in room_details_data:
                        room_members_data = room_data.pop('room_members', [])
                        room = RoomDetail.objects.create(**room_data, address=address)
                        
                        # Create room members
                        for member_data in room_members_data:
                            RoomMembersDetail.objects.create(room=room, **member_data)
            
            # Update personal details
            if personal_data is not None:
                relations_data = personal_data.pop('relations', [])
                personal_table, created = PersonalTable.objects.get_or_create(
                    user=instance, defaults=personal_data
                )
                if not created:
                    for attr, value in personal_data.items():
                        setattr(personal_table, attr, value)
                    personal_table.save()
                
                # Update relations (replace all)
                personal_table.relations.all().delete()
                for relation_data in relations_data:
                    Relation.objects.create(personal_table=personal_table, **relation_data)
            
            # Update professional details
            if professional_data is not None:
                prof_detail, created = ProfessionalDetail.objects.get_or_create(
                    user=instance, defaults=professional_data
                )
                if not created:
                    for attr, value in professional_data.items():
                        setattr(prof_detail, attr, value)
                    prof_detail.save()
            
            # Update residential details
            if residential_data is not None:
                res_detail, created = ResidentialDetail.objects.get_or_create(
                    user=instance, defaults=residential_data
                )
                if not created:
                    for attr, value in residential_data.items():
                        setattr(res_detail, attr, value)
                    res_detail.save()
        
        return instance

# Read-only serializer for user details
class UserDetailSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(source='address_set', many=True, read_only=True)
    personal_details = PersonalTableSerializer(source='personaltable_set.first', read_only=True)
    professional_details = ProfessionalDetailSerializer(source='professionaldetail_set.first', read_only=True)
    residential_details = ResidentialDetailSerializer(source='residentialdetail_set.first', read_only=True)
    
    class Meta:
        model = CustomUser
        fields= "__all__"
        
        
class LoginEmailPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)



class OTPserializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=4, max_length=4)
