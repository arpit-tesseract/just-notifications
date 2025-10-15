# serializers.py
from rest_framework import serializers
from .models import *
        
class LoginEmailPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ['id', 'name','display_name']
        read_only_fields = ['id', 'name', 'display_name']



# This Serializer Use after loggin success
class CustomUserBasicDetailsOutputSerializer(serializers.ModelSerializer):
    user_role = UserRoleSerializer(many=True)
    # designation = DesignationSerializer(many=False)
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'email',
            'contact_no',
            'full_name',
            'pet_name',
            'father_name',
            'photo',
            'date_of_birth',
            'blood_group',
            'user_role',
        ]

class LogoutInputSerializer(serializers.Serializer):
    # access = serializers.CharField(write_only=True)
    refresh = serializers.CharField(write_only=True)
