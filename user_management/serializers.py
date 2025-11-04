# serializers.py
from .utils import *
from rest_framework import serializers
from .models import *
from .validators import *        
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
    

class PersonalDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalDetail
        fields = "__all__"
        read_only_fields = ['id','user', 'personal_code']


class ResidentialDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResidentialDetail
        fields = ['category_of_user', 'glob', 'continent', 'country', 'state', 'district', 'taluka', 'city_village', 'ward', 'society', 'block', 'floor', 'house_no', 'total_no_of_rooms']
        read_only_fields = ['id','user', 'residential_code']
        extra_kwargs = {
            'category_of_user': {'required': False},
        }
    
    def validate(self, attrs):
        text_fields = [
            'society',
            'block',
            'floor',
            'house_no',
            'total_no_of_rooms'
        ]
        for field in text_fields:
            if field in attrs:
                try:
                    temp = clean_str(attrs.get(field))
                except:
                    temp = None
                attrs[field] = temp
        return attrs

class ProfessionalDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessionalDetail
        fields = "__all__"
        read_only_fields = ['id','user', 'professional_code', 'residential_details']
    
    def validate(self, attrs):
        text_fields = [
            'pay_scale',
            'mfg_life',
        ]
        for field in text_fields:
            if field in attrs:
                try:
                    temp = clean_str(attrs.get(field))
                except:
                    temp = None
                attrs[field] = temp
        
        # verify designation category is professional
        designation = attrs.get("designation")
        if designation is None:
            raise serializers.ValidationError({"designation": "Designation is Required."})
        
        if designation.category != "professional":
            raise serializers.ValidationError({"designation": "Invalid designation."})
        
        return attrs


class BussinessDetailSerializer(serializers.Serializer):
    professional_details = ProfessionalDetailSerializer(many=False)
    professional_residential_details = ResidentialDetailSerializer(many=False)


class UserSerializerForPost(serializers.ModelSerializer):
    user_id = serializers.IntegerField(required=False, allow_null=True)
    email = serializers.EmailField(validators=[validate_email])
    contact_no = serializers.CharField(validators=[])
    full_name = serializers.CharField(validators=[validate_full_name])
    father_name = serializers.CharField(validators=[validate_full_name])
    blood_group = serializers.CharField(validators=[validate_blood_group])
    date_of_birth = serializers.DateField(validators=[validate_dob])
    user_role_name = serializers.CharField()
    user_role = UserRoleSerializer(many=False, read_only=True)
    residential_details = ResidentialDetailSerializer(many=False)
    personal_details = PersonalDetailSerializer(many=False)
    bussiness_details = BussinessDetailSerializer(many=True, required=False, allow_null=True)
    class Meta:
        model = CustomUser
        fields = ['user_id', 'email', 'contact_no', 'user_role', 'user_role_name','full_name', 'pet_name', 'father_name', 'date_of_birth', 'blood_group', 'is_married', 'is_verified', 'residential_details', 'personal_details', 'bussiness_details']
        # read_only_fields = []
    

    def validate(self, attrs):
        # verify user role    
        user_role_name = attrs.get('user_role_name', None)
        if user_role_name is None:
            raise serializers.ValidationError({"user_role_name": "User role is required."})
    
        user_role = get_role_obj_by_name(user_role_name)
        if user_role is None:
            raise serializers.ValidationError({"user_role_name": "Invalid user role."})
    
        # set user role
        attrs.pop('user_role_name')
        attrs['user_role'] = user_role
        
        user_email = attrs.get('email', None)
        user_contact_no = attrs.get('contact_no', None)
        user_id = attrs.get('user_id', None)
        
        if user_id is not None:
            user_obj = get_obj_by_modle_and_id(CustomUser, user_id)
            if user_obj is None:
                raise serializers.ValidationError({"user_id": "User not found."})
            attrs['user_id'] = user_obj
            
            if user_obj.email != user_email:
                if check_email_exists_in_CustomUser(user_email):
                    raise serializers.ValidationError("Email already exists.")
                
            if user_obj.contact_no != user_contact_no:
                if check_contact_no_exists_in_CustomUser(user_contact_no):
                    raise serializers.ValidationError("Contact number already exists.")
            
        else:
            if check_email_exists_in_CustomUser(user_email):
                raise serializers.ValidationError("Email already exists.")
            
            if check_contact_no_exists_in_CustomUser(user_contact_no):
                raise serializers.ValidationError("Contact number already exists.")
                
        return attrs
        
      

class PostSerializer(serializers.ModelSerializer):
    user_details = UserSerializerForPost(many=False)
    class Meta:
        model = Relation
        fields = ['user_details', 'designation', 'custom_post_no']
        read_only_fields = ['id']


class UserRegistrationSerializer(serializers.Serializer):
    relation_category = serializers.CharField()      
    number_of_post = serializers.IntegerField()
    posts = PostSerializer(many=True)
    
    def validate(self, attrs):
        
        # verify relation category
        relation_category = attrs.get('relation_category')
        if verify_user_relation_category(relation_category) == False:
            raise serializers.ValidationError({"relation_category": "Invalid relation category."})
        
        # verify number of posts
        posts = attrs.get('posts', [])
        number_of_post = attrs.get('number_of_post')
        if number_of_post != len(posts):
            raise serializers.ValidationError({"posts": f"Number of posts should be {number_of_post}."})
        
        email_in_requests = set()
        contact_no_in_requests = set()
        for index, post in enumerate(posts):
            user_details = post.get('user_details', None)
            
            if user_details:
                user_email = user_details.get('email', None)
                user_contact_no = user_details.get('contact_no', None)
                
                if user_email in email_in_requests:
                    raise serializers.ValidationError({
                            "posts": f"The email '{user_email}' is used more than once in this request (at post {index+1})."
                        })
                email_in_requests.add(user_email)
                
                if user_contact_no in contact_no_in_requests:
                    raise serializers.ValidationError({
                            "posts": f"The contact number '{user_contact_no}' is used more than once in this request (at post {index+1})."
                        })
                contact_no_in_requests.add(user_contact_no)
        
        # for index, post in enumerate(posts):
        #     user_details = post.get('user_details', None)
        #     user_id = post.get("existing_user_id", None)
            
        #     if user_details is not None and user_id is not None:
        #         raise serializers.ValidationError({"posts": f"Either user_details or existing_user_id should be provided for post: {index+1}."})
            
        #     if user_details is None and user_id is None:
        #         raise serializers.ValidationError({"posts": f"Required either user_details or existing_user_idc for post: {index+1}."})
            
            # verify user details
            # if user_details:
            #     user_email = user_details.get('email', None)
            #     user_contact_no = user_details.get('contact_no', None)
                
            #     if check_email_exists(user_email):
            #         raise serializers.ValidationError({"user_details": f"Post: {index+1}, Email already exists."})
            #     if check_contact_no_exists(user_contact_no):
            #         raise serializers.ValidationError({"user_details": f"Post: {index+1}, Contact number already exists."})
                
            #     # verify to user role name
            #     user_role_name = user_details.get('user_role_name', None)
            #     user_role_obj = get_role_obj_by_name(user_role_name)
            #     if user_role_obj is None:
            #         raise serializers.ValidationError({"user_details": f"Post: {index+1}, Invalid to user role name."})
            #     else:
            #         attrs['posts'][index]['user_details'].pop('user_role_name', None)
            #         attrs['posts'][index]['user_details']['user_role_obj'] = user_role_obj
            
        return attrs 

class UserPhotoUploadSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(validators=[validate_image_file])

    class Meta:
        model = CustomUser
        fields = ['photo']


class UserDocumentUploadSerializer(serializers.ModelSerializer):
    adhar_card_file = serializers.FileField(
        required=False, allow_null=True, validators=[validate_image_or_pdf]
    )
    pan_card_file = serializers.FileField(
        required=False, allow_null=True, validators=[validate_image_or_pdf]
    )
    voter_card_file = serializers.FileField(
        required=False, allow_null=True, validators=[validate_image_or_pdf]
    )
    driving_licence_file = serializers.FileField(
        required=False, allow_null=True, validators=[validate_image_or_pdf]
    )
    ration_card_file = serializers.FileField(
        required=False, allow_null=True, validators=[validate_image_or_pdf]
    )
    
    class Meta:
        model = Document
        fields = [
            'adhar_card_file', 
            'pan_card_file', 
            'voter_card_file', 
            'driving_licence_file', 
            'ration_card_file'
        ]

class UserRegistrationOutPutSerializer(serializers.Serializer):
    existing_from_user_id = serializers.CharField()
    posts = serializers.ListField()


class UserRoleAssignAndRemoveSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    role_ids = serializers.ListField(
        child = serializers.IntegerField(),
        allow_empty = False
    )


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole  
        fields = "__all__"