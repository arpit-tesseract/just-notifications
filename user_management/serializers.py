# serializers.py
from .utils import verify_user_relation_category, get_role_obj_by_name, get_obj_by_modle_and_id, check_email_exists, check_contact_no_exists, clean_str
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
        fields = ['category_of_user', 'glob', 'continent', 'country', 'state', 'district', 'taluka', 'city_village', 'ward', 'society', 'block', 'floor', 'house_no', 'no_of_rooms']
        read_only_fields = ['id','user', 'residential_code']
    
    def validate(self, attrs):
        text_fields = [
            'society',
            'block',
            'floor',
            'house_no',
            'no_of_rooms'
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
        fields = ['id', 'email', 'contact_no', 'user_role', 'user_role_name','full_name', 'pet_name', 'father_name', 'date_of_birth', 'blood_group', 'is_verified', 'residential_details', 'personal_details', 'bussiness_details']
        read_only_fields = ['id']
      


class RelationSerializer(serializers.ModelSerializer):
    to_user_details = UserSerializerForPost(many=False, required=False, allow_null=True)
    existing_to_user_id = serializers.IntegerField(required=False, allow_null=True)
    custom_post_no = serializers.FloatField(required=False, allow_null=True)
    class Meta:
        model = Relation
        fields = ['to_user_details', 'existing_to_user_id', 'designation', 'custom_post_no']
        read_only_fields = ['id']
          

class UserRegistrationSerializer(serializers.Serializer):
    relation_category = serializers.CharField()
    from_user_details = UserSerializerForPost(many=False, required=False, allow_null=True) # from user == main user, 
    existing_from_user_id = serializers.IntegerField(required=False, allow_null=True)       
    number_of_post = serializers.IntegerField()
    posts = RelationSerializer(many=True)
    
    def validate(self, attrs):
        # verify relation category
        relation_category = attrs.get('relation_category')
        if verify_user_relation_category(relation_category) == False:
            raise serializers.ValidationError({"relation_category": "Invalid relation category."})
        
        from_user_details = attrs.get('from_user_details', None)
        from_user_id = attrs.get("existing_from_user_id", None)
        
        if from_user_details is not None and from_user_id is not None:
            raise serializers.ValidationError({"error": f"Either from_user_details or existing_from_user_id should be provided."})
        
        if from_user_details is None and from_user_id is None:
            raise serializers.ValidationError({"error": f"Required either from_user_details or existing_from_user_id."})
            
        if from_user_details:
            from_user_email = from_user_details.get('email', None)
            from_user_contact_no = from_user_details.get('contact_no', None)
            # verify from user
            if check_email_exists(from_user_email):
                raise serializers.ValidationError({"from_user_details": "Email already exists."})
            if check_contact_no_exists(from_user_contact_no):
                raise serializers.ValidationError({"from_user_details": "Contact number already exists."})
            
            # verify from user role name
            from_user_role_name = from_user_details.get('user_role_name', None)
            from_user_role_obj = get_role_obj_by_name(from_user_role_name)
            if from_user_role_obj is None:
                raise serializers.ValidationError({"from_user_details": "Invalid from user role name."})
            else:
                attrs['from_user_details'].pop('user_role_name', None)
                attrs['from_user_details']['user_role_obj'] = from_user_role_obj

        # verify existing from user id
        if from_user_id:
            from_user_obj = get_obj_by_modle_and_id(CustomUser, from_user_id)
            if from_user_obj is None:
                raise serializers.ValidationError({"existing_from_user_id": "Invalid from user id."})
            attrs['existing_from_user_id'] = from_user_obj
            from_user_email = from_user_obj.email
            from_user_contact_no = from_user_obj.contact_no
        
        
        # verify number of posts
        posts = attrs.get('posts', [])
        number_of_post = attrs.get('number_of_post')
        if number_of_post != len(posts):
            raise serializers.ValidationError({"posts": f"Number of posts should be {number_of_post}."})
        
        for index, post in enumerate(posts):
            to_user_details = post.get('to_user_details', None)
            to_user_id = post.get("existing_to_user_id", None)
            
            if to_user_details is not None and to_user_id is not None:
                raise serializers.ValidationError({"posts": f"Either to_user_details or existing_to_user_id should be provided for post: {index+1}."})
            
            if to_user_details is None and to_user_id is None:
                raise serializers.ValidationError({"posts": f"Required either to_user_details or existing_to_user_idc for post: {index+1}."})
            
            
            if to_user_details:
                to_user_email = to_user_details.get('email', None)
                to_user_contact_no = to_user_details.get('contact_no', None)
                
                if to_user_email == from_user_email:
                    raise serializers.ValidationError({"to_user_details": f"Post: {index+1}, From and To user email cannot be same."})
                if to_user_contact_no == from_user_contact_no:
                    raise serializers.ValidationError({"to_user_details": f"Post: {index+1}, From and To user contact no cannot be same."})
                
                if check_email_exists(to_user_email):
                    raise serializers.ValidationError({"to_user_details": f"Post: {index+1}, Email already exists."})
                if check_contact_no_exists(to_user_contact_no):
                    raise serializers.ValidationError({"to_user_details": f"Post: {index+1}, Contact number already exists."})
                
                # verify to user role name
                to_user_role_name = to_user_details.get('user_role_name', None)
                to_user_role_obj = get_role_obj_by_name(to_user_role_name)
                if to_user_role_obj is None:
                    raise serializers.ValidationError({"to_user_details": f"Post: {index+1}, Invalid to user role name."})
                else:
                    attrs['posts'][index]['to_user_details'].pop('user_role_name', None)
                    attrs['posts'][index]['to_user_details']['user_role_obj'] = to_user_role_obj
            
            if from_user_id is not None and to_user_id is not None:
                # verify from and to user
                if from_user_id == to_user_id:
                    raise serializers.ValidationError({"posts": f"Post: {index+1}, From and To user cannot be same."})
            
            # verify existing to user id
            if to_user_id:
                to_user_obj = get_obj_by_modle_and_id(CustomUser, to_user_id)
                if to_user_obj is None:
                    raise serializers.ValidationError({"existing_to_user_id": f"Post: {index+1}, Invalid to user id."})
                attrs['existing_to_user_id'] = to_user_obj
            
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