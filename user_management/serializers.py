# serializers.py
from .utils import *
from rest_framework import serializers
from .models import *
from .validators import *  
from configuration.serializers import *
from django.apps import apps
      
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
        fields = [
            'religion',
            'sampraday',
            'panth',
            'awastha',
            'varna',
            'caste',
            'subcaste',
            'gotra',
            'subgotra',
            'kul',
            'vansh',
            'family',
            'pidhi',
        ]
        # related_name = 'personaldetail_set'


class ResidentialDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResidentialDetail
        fields = [
                'glob',
                'continent',
                'country',
                'state',
                'district',
                'taluka',
                'city_village',
                'ward',
                'society',
                'block',
                'floor',
                'house',
            ]
        # read_only_fields = ['id','user', 'residential_code', 'residential_type']
        # extra_kwargs = {
        #     'category_of_user': {'required': False},
        # } 
    
    # def validate_room_details(self, value):
    #     if value is None:
    #         return
        
    #     for room_type_id, room_info in value.items():
    #         # room_name = "hall"
    #         try:
    #             room_type_id = int(room_type_id)
    #         except ValueError:
    #             raise serializers.ValidationError(
    #                 f"'{room_type_id}' must be an integer."
    #             )
    #         room_type_obj = get_obj_by_modle_and_id(RoomType, room_type_id)
    #         if room_type_obj is None:
    #             raise serializers.ValidationError(
    #                 f"'{room_type_id}' not found in RoomType table."
    #             )
    #         else:
    #             if room_type_obj.is_used == False:
    #                 room_type_obj.is_used = True
    #                 room_type_obj.save()
                    
    #         if not isinstance(room_info, dict):
    #             raise serializers.ValidationError(
    #                 f"'{room_type_id}' must be an object with 'count', 'room_flash_id' and 'room_type_name' keys."
    #             )
        
    #         # required keys
    #         required_keys = {"count", "room_flash_id"}
    #         missing = required_keys - room_info.keys()
    #         if missing:
    #             raise serializers.ValidationError(
    #                 f"Missing keys in '{room_type_id}': {', '.join(missing)}"
    #             )
            
    #         # type checks
    #         if isinstance(room_info["count"], int):
    #             if room_info["count"] < 1:
    #                 raise serializers.ValidationError(
    #                     f"'count' in '{room_type_id}' must be a positive integer."
    #                 )
    #         else:
    #             raise serializers.ValidationError(
    #                 f"'count' in '{room_type_id}' must be an integer."
    #             )
            

    #         if isinstance(room_info["room_flash_id"], int):
    #             if room_info["room_flash_id"] < 1:
    #                 raise serializers.ValidationError(
    #                     f"'room_flash_id' for '{room_type_id}' must be a positive integer."
    #                 )
                    
    #             room_flash_obj = get_obj_by_modle_and_id(RoomFlash, room_info.get("room_flash_id"))
    #             if room_flash_obj is None:
    #                 raise serializers.ValidationError(
    #                     f"'room_flash_id' for '{room_type_id}' does not exist."
    #                 )
    #             else:
    #                 if room_flash_obj.is_used == False:
    #                     room_flash_obj.is_used = True
    #                     room_flash_obj.save()
                
    #             # store room_flash_obj
    #             # room_info["room_flash_id"] = room_flash_obj
    #         else:
    #             raise serializers.ValidationError(
    #                 f"'room_flash_id' in '{room_type_id}' must be an integer."
    #             )
                
    #     return value
    
    # def validate(self, attrs):
    #     text_fields = [
    #         'society',
    #         'block',
    #         'floor',
    #         'house_no',
    #         # 'total_no_of_rooms'
    #     ]
        

class ProfessionalDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessionalDetail
        fields = [
            'section',
            'profclass',
            'category',
            'subcategory',
            'sector',
            'subsector',
            'department',
            'subdepartment',
            'type',
            'brand',
            'designation',
            'pay_scale',
            'mfg_dt_time',
            'mfg_life',
        ]
        # read_only_fields = ['id','user', 'professional_code', 'residential_details']
    
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
    user_id = serializers.IntegerField(required=True, allow_null=True)
    email = serializers.EmailField(validators=[validate_email])
    contact_no = serializers.CharField(validators=[])
    full_name = serializers.CharField(validators=[validate_full_name])
    father_name = serializers.CharField(validators=[validate_full_name])
    blood_group = serializers.CharField(validators=[validate_blood_group])
    date_of_birth = serializers.DateField(validators=[validate_dob])
    user_role_name = serializers.CharField()
    residential_details = ResidentialDetailSerializer(many=False)
    personal_details = PersonalDetailSerializer(many=False)
    bussiness_details = BussinessDetailSerializer(many=True, required=True, allow_null=True)
    
    allocated_rooms = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=configm.Room.objects.all(),
        required=False
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'user_id', 
            'email', 
            'contact_no', 
            'user_role_name',
            'full_name', 
            'pet_name', 
            'father_name',
            'gender',
            'date_of_birth',
            'blood_group', 
            'marital_status', 
            'is_verified', 
            'expired_date',
            'allocated_rooms',
            'residential_details',
            'personal_details',
            'bussiness_details',
            'category_of_user',
        ]
        # read_only_fields = ['id', 'allocated_rooms']
    
    def get_user_role_name(self, obj):
        return obj.user_role.name

    def validate(self, attrs):
        # verify user role    
        user_role_name = attrs.get('user_role_name', None)
        if user_role_name is None:
            raise serializers.ValidationError({"user_role_name": "User role is required."})
    
        user_role = get_role_obj_by_name(user_role_name)
        if user_role is None:
            raise serializers.ValidationError({"user_role_name": "Invalid user role."})
        
        dob = attrs.get('date_of_birth', None)
        expired_date = attrs.get('expired_date', None)
        
        if dob is not None and expired_date is not None:
            if expired_date < dob:
                raise serializers.ValidationError({"expired_date": "Expired date cannot be less than date of birth."})
            if expired_date > timezone.now().date():
                raise serializers.ValidationError({"expired_date": "Expired date cannot be in the future."})
                
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
        

class UserFilterSerializer(serializers.Serializer):
    residential_details = ResidentialDetailSerializer(many=False, required=True, allow_null=True)
    personal_details = PersonalDetailSerializer(many=False, required=True, allow_null=True)
    bussiness_details = BussinessDetailSerializer(many=True, required=True, allow_null=True)
        

class PostSerializer(serializers.Serializer):
    user_details = UserSerializerForPost(many=False)
    user_designation = serializers.SlugRelatedField(     # Use SlugRelatedField for name-based lookup
        slug_field='name',                          # Input: "Manager" (string) -> Output: Designation Object (or 400 Error)
        queryset=Designation.objects.all()
    )
    relation_between_from_and_to = serializers.PrimaryKeyRelatedField(   # Use PrimaryKeyRelatedField for ID-based lookup
        queryset=Designation.objects.all(),                     # Input: 5 (int) -> Output: Designation Object (or 400 Error)
        required=True, 
        allow_null=False
    )
    post_no = serializers.IntegerField(required=True, allow_null=True)
    

class UserRegistrationSerializer(serializers.Serializer):
    existing_main_user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=True,
        allow_null=True
    )
    existing_main_user_designation = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Designation.objects.all(),
        required=True,
        allow_null=True
    )
    residential_category = serializers.CharField()      
    posts = PostSerializer(many=True)
    
    def validate(self, attrs):
        # verify relation category
        relation_category = attrs.get('residential_category')
        if verify_user_relation_category(relation_category) == False:
            raise serializers.ValidationError({"relation_category": "Invalid relation category."})
        
        if relation_category not in ['current', "Current"]:
            if attrs.get('existing_main_user_id') is None:
                raise serializers.ValidationError({"existing_main_user_id": "Existing main user id null not allowed."})
            
            if attrs.get('existing_main_user_designation') is None:
                raise serializers.ValidationError({"existing_main_user_designation": "Existing main user designation name null not allowed."})
        # else:
        #     attrs['existing_main_user_id'] = None
               
        # verify number of posts
        posts = attrs.get('posts', [])
        if len(posts) == 0:
            raise serializers.ValidationError({"posts": "At least one post is required."})
        
        # verify number of unique emails and contact numbers
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


class UserListSerializer(serializers.ModelSerializer):
    # user_roles = UserRoleSerializer(many=True, read_only=True, source='user_role')
    country = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'photo',
            'email',
            'contact_no',
            'full_name',
            'date_of_birth',
            'is_verified',
            'country',
            'state',
            'city'
        ]
    
    def get_country(self, obj):
        return obj.current_residential_details.country.name if obj.current_residential_details and obj.current_residential_details.country else None

    def get_state(self, obj):
        return obj.current_residential_details.state.name if obj.current_residential_details and obj.current_residential_details.state else None

    def get_city(self, obj):
        return obj.current_residential_details.city_village.name if obj.current_residential_details and obj.current_residential_details.city_village else None


class ResidentialDetailGetSerializer(serializers.ModelSerializer):
    glob = GlobIdNameSerializer()
    continent = ContinentIdNameSerializer()
    country = CountryIdNameSerializer()
    state = StateIdNameSerializer()
    district = DistrictIdNameSerializer()
    taluka = TalukaIdNameSerializer()
    city_village = CityVillageIdNameSerializer()
    ward = WardIdNameSerializer()
    society = SocietyIdNameSerializer()
    block = BlockIdNameSerializer()
    floor = FloorIdNameSerializer()
    house = HouseIdNameSerializer()

    class Meta:
        model = ResidentialDetail
        fields = [
            'glob',
            'continent',
            'country',
            'state',
            'district',
            'taluka',
            'city_village',
            'ward',
            'society',
            'block',
            'floor',
            'house',
            'total_no_of_rooms',
            'residential_type'
        ]    

class PersonalDetailGetSerializer(serializers.ModelSerializer):
    religion = ReligionIdNameSerializer()
    sampraday = SampradayIdNameSerializer()
    panth = PanthIdNameSerializer()
    awastha = AwasthaIdNameSerializer()
    varna = VarnaIdNameSerializer()
    caste = CasteIdNameSerializer()
    subcaste = SubCasteIdNameSerializer()
    gotra = GotraIdNameSerializer()
    subgotra = SubGotraIdNameSerializer()
    kul = KulIdNameSerializer()
    vansh = VanshIdNameSerializer()
    family = FamilyIdNameSerializer()
    # pidhi = PidhiIdNameSerializer()
    class Meta:
        model = PersonalDetail
        fields = [
            'religion',
            'sampraday',
            'panth',
            'awastha',
            'varna',
            'caste',
            'subcaste',
            'gotra',
            'subgotra',
            'kul',
            'vansh',
            'family',
            'pidhi',
        ]


class ProfessionalDetailGetSerializer(serializers.ModelSerializer):
    section = SectionIdNameSerializer()
    profclass = ClassIdNameSerializer()
    category = ProfCategoryIdNameSerializer()
    subcategory = ProfSubCategoryIdNameSerializer()
    sector = SectorIdNameSerializer()
    subsector = SubSectorIdNameSerializer()
    department = DepartmentIdNameSerializer()
    subdepartment = SubDepartmentIdNameSerializer()
    type = TypeIdNameSerializer()
    brand = BrandIdNameSerializer()
    class Meta:
        model = ProfessionalDetail
        fields = [
            'section',
            'profclass',
            'category',
            'subcategory',
            'sector',
            'subsector',
            'department',
            'subdepartment',
            'type',
            'brand',
            'designation',
            'pay_scale',
            'mfg_dt_time',
            'mfg_life',
        ]


class DocumentSerializerForGet(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            'adhar_card_file',
            'pan_card_file',
            'voter_card_file',
            'driving_licence_file',
            'ration_card_file',
        ]


class BussinessDetailsGetSerializer(serializers.ModelSerializer):
    section = SectionIdNameSerializer()
    profclass = ClassIdNameSerializer()
    category = ProfCategoryIdNameSerializer()
    subcategory = ProfSubCategoryIdNameSerializer()
    sector = SectorIdNameSerializer()
    subsector = SubSectorIdNameSerializer()
    department = DepartmentIdNameSerializer()
    subdepartment = SubDepartmentIdNameSerializer()
    type = TypeIdNameSerializer()
    brand = BrandIdNameSerializer()
    residential_details = ResidentialDetailGetSerializer()
    class Meta:
        model = ProfessionalDetail
        fields = [
            'section',
            'profclass',
            'category',
            'subcategory',
            'sector',
            'subsector',
            'department',
            'subdepartment',
            'type',
            'brand',
            'designation',
            'pay_scale',
            'mfg_dt_time',
            'mfg_life',
            'residential_details',
        ]

        
class UserSerializerForGet(serializers.ModelSerializer):
    user_id = serializers.SerializerMethodField()
    user_role_name = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    residential_details = serializers.SerializerMethodField()
    personal_details = serializers.SerializerMethodField()
    bussiness_details = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'user_id',
            'photo',
            'email',
            'contact_no',
            'user_role_name',
            'full_name',
            'pet_name',
            'father_name',
            'gender',
            'date_of_birth',
            'blood_group',
            'marital_status',
            'is_verified',
            'expired_date',
            'allocated_rooms',
            'documents',
            'residential_details',
            'personal_details',
            'bussiness_details',
            'category_of_user',
        ]
    
    def get_user_id(self, obj):
        return obj.id

    def get_residential_details(self, obj):
        target_category = self.context.get("residential_category")
        
        if not target_category:
            return None

        field_mapping = {
            'current': 'current_residential_details',
            'owner': 'owner_residential_details',
            'permanent': 'permanent_residential_details',
            'native': 'native_residential_details',
            'inlaws': 'inlaws_residential_details',
            'maternal': 'maternal_residential_details',
            'business': 'business_residential_details',
        }
        
        # current_residential_details, etc.
        field_name = field_mapping.get(target_category.lower())

        if not field_name:
            return None
        
        # This is equivalent to obj.current_residential_details, etc.
        residential_obj = getattr(obj, field_name, None)
        
        if residential_obj:
            return ResidentialDetailGetSerializer(residential_obj).data
        
        return None
            
    def get_documents(self, obj):
        """
        'obj' is the CustomUser instance.
        """
        try:
            # Get the single Document object related to this user
            document_obj = Document.objects.get(user=obj)
            return DocumentSerializerForGet(document_obj).data
        except Document.DoesNotExist:
            # If the user has no documents, return null
            return None
        except Exception as e:
            return None

    def get_user_role_name(self, obj):
        return obj.user_role.name
    
    def get_personal_details(self, obj):
        try:
            return PersonalDetailGetSerializer(PersonalDetail.objects.get(user=obj)).data
        except:
            return None
    
    def get_bussiness_details(self, obj):
        professional_objs_lst = ProfessionalDetail.objects.filter(user=obj)
        if not professional_objs_lst:
            return []

        professional_details_lst = []
        for professional_detail in professional_objs_lst:
            
            # 1. Serialize the professional details
            prof_data = ProfessionalDetailGetSerializer(professional_detail).data
            
            # 2. Serialize the residential details
            res_data = ResidentialDetailGetSerializer(professional_detail.residential_details).data
            
            # 3. Create the new dictionary with the correct structure
            bussiness_item = {
                "professional_details": prof_data,
                "professional_residential_details": res_data
            }
            
            # 4. Append this new dictionary to the final list
            professional_details_lst.append(bussiness_item)
            
        return professional_details_lst

class BussinessDetailSerializer(serializers.ModelSerializer):
    residential_details = ResidentialDetailSerializer(many=False, required=True, allow_null=True)
    class Meta:
        model = ProfessionalDetail
        fields = [
            'section',
            'profclass',
            'category',
            'subcategory',
            'sector',
            'subsector',
            'department',
            'subdepartment',
            'type',
            'brand',
            'designation',
            'pay_scale',
            'mfg_dt_time',
            'mfg_life',
            'residential_details',
        ]
class BussinessDetailSerializerForFilteration(serializers.ModelSerializer):
    residential_details = ResidentialDetailSerializer(many=False, required=False, allow_null=True)
    class Meta:
        model = ProfessionalDetail
        fields = [
            'section',
            'profclass',
            'category',
            'subcategory',
            'sector',
            'subsector',
            'department',
            'subdepartment',
            'type',
            'brand',
            'designation',
            'pay_scale',
            'mfg_dt_time',
            'mfg_life',
            'residential_details',
        ]
        
        extra_kwargs = {
            "pay_scale": {"required": False, "allow_null": True},
            "mfg_dt_time": {"required": False, "allow_null": True},
            "mfg_life": {"required": False, "allow_null": True},
        }

class UserFilterInputSerializer(serializers.Serializer):
    residential_details = ResidentialDetailSerializer(many=False, required=True, allow_null=True)
    personal_details = PersonalDetailSerializer(many=False, required=True, allow_null=True)
    bussiness_details = BussinessDetailSerializerForFilteration(many=False, required=True, allow_null=True, partial=True)

class ResidentialDetailsForUserSugesionInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResidentialDetail
        fields = [
            'glob',
            'continent',
            'country',
            'state',
            'district',
            'taluka',
            'city_village',
            'ward',
            'society',
            'block',
            'floor',
            'house_no',
        ]  

class UserSuggestionInputSerializer(serializers.Serializer):
    # residential_details = ResidentialDetailsForUserSugesionInputSerializer(required=True, allow_null=True)
    personal_details = PersonalDetailSerializer()
    full_name = serializers.CharField(required=True, allow_null=True)
    father_name = serializers.CharField(required=True, allow_null=True)
    email = serializers.EmailField(required=True, allow_null=True)
    contact_no = serializers.CharField(required=True,allow_null=True)
    gender = serializers.CharField(required=True,allow_null=True)


class UserSuggestionOutputListSerializer(serializers.ModelSerializer):
    user_id = serializers.SerializerMethodField()
    class Meta:
        model = CustomUser
        fields = [
            'user_id',
            'photo',
            'full_name',
            'father_name',
            'email',
            'contact_no',
            'gender',
        ]
    
    def get_user_id(self, obj):
        return obj.id
    
    

class UserSuggestionOutputDetailSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="id")
    user_role = UserRoleSerializer(many=True, read_only=True)
    current_residential_details = ResidentialDetailGetSerializer(many=False)
    personal_details = PersonalDetailGetSerializer(many=False)
    bussiness_details = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    
    def get_documents(self, obj):
        """
        'obj' is the CustomUser instance.
        """
        try:
            # Get the single Document object related to this user
            document_obj = Document.objects.get(user=obj)
            return DocumentSerializerForGet(document_obj).data
        except Document.DoesNotExist:
            # If the user has no documents, return null
            return None
        except Exception as e:
            return None

    # def get_user_role_name(self, obj):
    #     return obj.user_role.name
    
    
    def get_bussiness_details(self, obj):
        professional_objs_lst = ProfessionalDetail.objects.filter(user=obj)
        if not professional_objs_lst:
            return []

        professional_details_lst = []
        for professional_detail in professional_objs_lst:
            
            # 1. Serialize the professional details
            prof_data = ProfessionalDetailGetSerializer(professional_detail).data
            
            # 2. Serialize the residential details
            res_data = ResidentialDetailGetSerializer(professional_detail.residential_details).data
            
            # 3. Create the new dictionary with the correct structure
            bussiness_item = {
                "professional_details": prof_data,
                "professional_residential_details": res_data
            }
            
            # 4. Append this new dictionary to the final list
            professional_details_lst.append(bussiness_item)
            
        return professional_details_lst
    
    class Meta:
        model = CustomUser
        fields = [
            'user_id', 
            'photo',
            'email', 
            'contact_no', 
            'user_role', 
            'full_name', 
            'pet_name', 
            'father_name',
            'gender',
            'date_of_birth',
            'blood_group', 
            'marital_status', 
            'expired_date',
            'current_residential_details',
            'personal_details',
            'bussiness_details',
            'documents',
        ]
    

class ModelAccessSerializer(serializers.Serializer):
    model = serializers.CharField()
    can_create = serializers.BooleanField()
    can_read = serializers.BooleanField()
    can_update = serializers.BooleanField()
    can_delete = serializers.BooleanField()
    
    def validate(self, data):
        """
        Check if the logged-in user has the right to assign these permissions.
        """
        request = self.context['request']
        perms_map = self.context['logged_user_perms_map'] # Got from View
        
        model_name = data.get('model')
        
        # Super Admins bypass validation
        if request.user.check_is_super_admin():
            return data

        # Get the logged-in user's permission for this specific model
        my_perm = perms_map.get(model_name)

        # ERROR LIST
        errors = {}

        # print("my_perm:", my_perm)
        if my_perm:
            # Logic: I can only give what I have
            if data['can_read'] and not my_perm.can_read:
                errors['can_read'] = "You cannot assign Read permission as you do not possess it."
            if data['can_create'] and not my_perm.can_create:
                errors['can_create'] = "You cannot assign Create permission as you do not possess it."
            if data['can_update'] and not my_perm.can_update:
                errors['can_update'] = "You cannot assign Update permission as you do not possess it."
            if data['can_delete'] and not my_perm.can_delete:
                errors['can_delete'] = "You cannot assign Delete permission as you do not possess it."
        else:
            # Logic: No permission record found -> Only Read allowed
            if data['can_create'] or data['can_update'] or data['can_delete']:
                raise serializers.ValidationError(
                    f"You have no rights on model '{model_name}'. You can only assign Read access."
                )

        if errors:
            raise serializers.ValidationError(errors)
        return data
        

class RecordRuleListSerializer(serializers.ModelSerializer):
    model_name = serializers.SerializerMethodField()
    class Meta:
        model = RecordRule
        fields = ['id', 'name', 'model_name']
        
    def get_model_name(self, obj):
        return obj.model.model

class RecordRuleSerializer(serializers.Serializer):
    model = serializers.CharField()
    value = serializers.ListField(child = serializers.IntegerField(), allow_empty = False)
    can_create = serializers.BooleanField()
    can_read = serializers.BooleanField()
    can_update = serializers.BooleanField()
    can_delete = serializers.BooleanField()

    def validate(self, attrs):
        model_name = attrs.get('model')
        model = get_ModelName_obj_by_name(model_name)
        attrs['model'] = model
        return attrs


class ModelIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelName
        fields = ['id', 'model']
        
class RecordRuleGetSerializer(serializers.ModelSerializer):
    model = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()
    class Meta:
        model = RecordRule
        fields = ['model', 'value']
    
    def get_model(self, obj):
        return obj.model.model
    
    def get_location_hierarchy(self, model_name, id_list):
        results = []
        
        if model_name == "Ward":
            select_path = (
                "city_village__taluka__district__state__country__continent__glob"
            )
            
            qs = Ward.objects.filter(id__in=id_list).select_related(select_path)
            
            for obj in qs:
                results.append({
                "glob": GlobIdNameSerializer(obj.city_village.taluka.district.state.country.continent.glob).data,
                "continent": ContinentIdNameSerializer(obj.city_village.taluka.district.state.country.continent).data,
                "country": CountryIdNameSerializer(obj.city_village.taluka.district.state.country).data,
                "state": StateIdNameSerializer(obj.city_village.taluka.district.state).data,
                "district": DistrictIdNameSerializer(obj.city_village.taluka.district).data,
                "taluka": TalukaIdNameSerializer(obj.city_village.taluka).data,
                "city_village": CityVillageIdNameSerializer(obj.city_village).data,
                "ward": WardIdNameSerializer(obj).data
            }) 
        
        
        elif model_name == "CityVillage":
            select_path = (
                "taluka__district__state__country__continent__glob"
            )
            
            qs = CityVillage.objects.filter(id__in=id_list).select_related(select_path)
            
            for obj in qs:
                results.append({
                "glob": GlobIdNameSerializer(obj.taluka.district.state.country.continent.glob).data,
                "continent": ContinentIdNameSerializer(obj.taluka.district.state.country.continent).data,
                "country": CountryIdNameSerializer(obj.taluka.district.state.country).data,
                "state": StateIdNameSerializer(obj.taluka.district.state).data,
                "district": DistrictIdNameSerializer(obj.taluka.district).data,
                "taluka": TalukaIdNameSerializer(obj.taluka).data,
                "city_village": CityVillageIdNameSerializer(obj).data
            })
        
        elif model_name == "Taluka":
            select_path = (
                "district__state__country__continent__glob"
            )
            
            qs = Taluka.objects.filter(id__in=id_list).select_related(select_path)
            
            for obj in qs:
                results.append({
                "glob": GlobIdNameSerializer(obj.district.state.country.continent.glob).data,
                "continent": ContinentIdNameSerializer(obj.district.state.country.continent).data,
                "country": CountryIdNameSerializer(obj.district.state.country).data,
                "state": StateIdNameSerializer(obj.district.state).data,
                "district": DistrictIdNameSerializer(obj.district).data,
                "taluka": TalukaIdNameSerializer(obj).data
            })
        
        
        elif model_name == "District":
            select_path = (
                "state__country__continent__glob"
            )
            
            qs = District.objects.filter(id__in=id_list).select_related(select_path)
            
            for obj in qs:
                results.append({
                "glob": GlobIdNameSerializer(obj.state.country.continent.glob).data,
                "continent": ContinentIdNameSerializer(obj.state.country.continent).data,
                "country": CountryIdNameSerializer(obj.state.country).data,
                "state": StateIdNameSerializer(obj.state).data,
                "district": DistrictIdNameSerializer(obj).data
            })
        
        
        elif model_name == "State":
            select_path = (
                "country__continent__glob"
            )
            
            qs = State.objects.filter(id__in=id_list).select_related(select_path)
            
            for obj in qs:
                results.append({
                "glob": GlobIdNameSerializer(obj.country.continent.glob).data,
                "continent": ContinentIdNameSerializer(obj.country.continent).data,
                "country": CountryIdNameSerializer(obj.country).data,
                "state": StateIdNameSerializer(obj).data
            })
        
        
        elif model_name == "Country":
            select_path = (
                "continent__glob"
            )
            
            qs = Country.objects.filter(id__in=id_list).select_related(select_path)
            
            for obj in qs:
                results.append({
                "glob": GlobIdNameSerializer(obj.continent.glob).data,
                "continent": ContinentIdNameSerializer(obj.continent).data,
                "country": CountryIdNameSerializer(obj).data
            })
        
        
        elif model_name == "Continent":
            select_path = (
                "glob"
            )
            
            qs = Continent.objects.filter(id__in=id_list).select_related(select_path)
            
            for obj in qs:
                results.append({
                "glob": GlobIdNameSerializer(obj.glob).data,
                "continent": ContinentIdNameSerializer(obj).data
            })
        
        elif model_name == "Glob":
            qs = Glob.objects.filter(id__in=id_list)
            
            for obj in qs:
                results.append({
                "glob": GlobIdNameSerializer(obj).data
            })
        
        else:
            raise serializers.ValidationError(f"Invalid model name: {model_name}")
        
        return results
         
    
    def get_value(self, obj):
        model_name = obj.model.model
        result = self.get_location_hierarchy(model_name, obj.domain_filter["id__in"])
        return result


class RecordRuleCreateSerializer(serializers.Serializer):
    model = serializers.CharField()
    values = serializers.ListField(
        child = serializers.IntegerField(),
        required=False, 
        allow_null=True
        )

    def validate(self, attrs):
        # validate model
        model_name = attrs.get('model')
        model = get_ModelName_obj_by_name(model_name)
        if model is None:
            raise serializers.ValidationError(f"Invalid model name: {model_name}")
        attrs['model_obj'] = model
        
        # validate model ids(values)
        django_model = get_django_model_from_obj(model)
        values = attrs.get('values')
        # 'values' can be None (for delete), so only validate if it exists
        if values:
            if not isinstance(values, list):
                raise serializers.ValidationError(f"Expected a list: {values}")
            
            # Validate all IDs in one query ---
            valid_ids_count = django_model.objects.filter(id__in=values).count()
            
            if valid_ids_count != len(values):
                # If counts don't match, an invalid ID was provided
                raise serializers.ValidationError(f"One or more model IDs are invalid for {model_name}.")
        
        return attrs