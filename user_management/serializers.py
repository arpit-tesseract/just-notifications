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
                'house_no',
                'total_no_of_rooms',
                'room_details',
            ]
        # read_only_fields = ['id','user', 'residential_code', 'residential_type']
        # extra_kwargs = {
        #     'category_of_user': {'required': False},
        # } 
    
    def validate_room_details(self, value):
        for room_type_id, room_info in value.items():
            # room_name = "hall"
            try:
                room_type_id = int(room_type_id)
            except ValueError:
                raise serializers.ValidationError(
                    f"'{room_type_id}' must be an integer."
                )
            room_type_obj = get_obj_by_modle_and_id(RoomType, room_type_id)
            if room_type_obj is None:
                raise serializers.ValidationError(
                    f"'{room_type_id}' not found in RoomType table."
                )
            else:
                if room_type_obj.is_used == False:
                    room_type_obj.is_used = True
                    room_type_obj.save()
                    
            if not isinstance(room_info, dict):
                raise serializers.ValidationError(
                    f"'{room_type_id}' must be an object with 'count', 'room_flash_id' and 'room_type_name' keys."
                )
        
            # required keys
            required_keys = {"count", "room_flash_id"}
            missing = required_keys - room_info.keys()
            if missing:
                raise serializers.ValidationError(
                    f"Missing keys in '{room_type_id}': {', '.join(missing)}"
                )
            
            # type checks
            if isinstance(room_info["count"], int):
                if room_info["count"] < 1:
                    raise serializers.ValidationError(
                        f"'count' in '{room_type_id}' must be a positive integer."
                    )
            else:
                raise serializers.ValidationError(
                    f"'count' in '{room_type_id}' must be an integer."
                )
            

            if isinstance(room_info["room_flash_id"], int):
                if room_info["room_flash_id"] < 1:
                    raise serializers.ValidationError(
                        f"'room_flash_id' for '{room_type_id}' must be a positive integer."
                    )
                    
                room_flash_obj = get_obj_by_modle_and_id(RoomFlash, room_info.get("room_flash_id"))
                if room_flash_obj is None:
                    raise serializers.ValidationError(
                        f"'room_flash_id' for '{room_type_id}' does not exist."
                    )
                else:
                    if room_flash_obj.is_used == False:
                        room_flash_obj.is_used = True
                        room_flash_obj.save()
                
                # store room_flash_obj
                # room_info["room_flash_id"] = room_flash_obj
            else:
                raise serializers.ValidationError(
                    f"'room_flash_id' in '{room_type_id}' must be an integer."
                )
                
        return value
    
    def validate(self, attrs):
        text_fields = [
            'society',
            'block',
            'floor',
            'house_no',
            # 'total_no_of_rooms'
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
        fields = [
            'user_id', 
            'email', 
            'contact_no', 
            'user_role', 
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
        
      

class PostSerializer(serializers.ModelSerializer):
    user_details = UserSerializerForPost(many=False)
    class Meta:
        model = Relation
        fields = ['user_details', 'designation', 'post_no']
        read_only_fields = ['id']


class UserRegistrationSerializer(serializers.Serializer):
    # residential_details = ResidentialDetailSerializer(many=False)
    relation_category = serializers.CharField()      
    number_of_post = serializers.IntegerField()
    posts = PostSerializer(many=True)
    
    def validate(self, attrs):
        # residential_details = attrs.get('residential_details', None)
        # room_details = residential_details.get('room_details', None)
        # if room_details is None or room_details == {}:
        #     raise serializers.ValidationError({"room_details": "Room details is required."})
        
        # for key, val in room_details.items():
        #     if val is None or val == "" or val <= 0:
        #         raise serializers.ValidationError({"room_details": f"Room details is required."})
           
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
        return obj.residential_details.country.name if obj.residential_details and obj.residential_details.country else None

    def get_state(self, obj):
        return obj.residential_details.state.name if obj.residential_details and obj.residential_details.state else None

    def get_city(self, obj):
        return obj.residential_details.city_village.name if obj.residential_details and obj.residential_details.city_village else None


class ResidentialDetailGetSerializer(serializers.ModelSerializer):
    glob = GlobIdNameSerializer()
    continent = ContinentIdNameSerializer()
    country = CountryIdNameSerializer()
    state = StateIdNameSerializer()
    district = DistrictIdNameSerializer()
    taluka = TalukaIdNameSerializer()
    city_village = CityVillageIdNameSerializer()
    ward = WardIdNameSerializer()

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
            'total_no_of_rooms',
            'room_details',
        ]    

class PersonalDetailGetSerializer(serializers.ModelSerializer):
    religion = ReligionIdNameSerializer()
    sampraday = SampradayIdNameSerializer()
    panth = PanthIdNameSerializer()
    varna = VarnaIdNameSerializer()
    caste = CasteIdNameSerializer()
    subcaste = SubCasteIdNameSerializer()
    gotra = GotraIdNameSerializer()
    subgotra = SubGotraIdNameSerializer()
    kul = KulIdNameSerializer()
    vansh = VanshIdNameSerializer()
    family = FamilyIdNameSerializer()
    pidhi = PidhiIdNameSerializer()
    class Meta:
        model = PersonalDetail
        fields = [
            'religion',
            'sampraday',
            'panth',
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
        
class UserSerializerForGet(serializers.ModelSerializer):
    user_id = serializers.SerializerMethodField()
    # user_role_name = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    personal_details = serializers.SerializerMethodField()
    bussiness_details = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'user_id',
            'photo',
            'email',
            'contact_no',
            # 'user_role_name',
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
            'personal_details',
            'bussiness_details',
            'category_of_user',
        ]
    
    def get_user_id(self, obj):
        return obj.id

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


class ModelAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelAccess
        fields = ['model', 'can_read', 'can_create', 'can_update', 'can_delete']
        


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
        fields = ['model', 'value', 'can_create', 'can_read', 'can_update', 'can_delete']
    
    def get_model(self, obj):
        return obj.model.model
    
    def get_location_hierarchy(self, model_name, id_list):
        results = []
        
        if model_name == "Ward":
            select_path = (
                "city_village__taluka__district__state__country__continent__glob"
            )
            
            qs = Ward.objects.filter(id__in=id_list).select_related(select_path)
            print("queryset:", qs)
            
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
            print("queryset:", qs)
            
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
            print("queryset:", qs)
            
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
            print("queryset:", qs)
            
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
            print("queryset:", qs)
            
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
            print("queryset:", qs)
            
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
            print("queryset:", qs)
            
            for obj in qs:
                results.append({
                "glob": GlobIdNameSerializer(obj.glob).data,
                "continent": ContinentIdNameSerializer(obj).data
            })
        
        elif model_name == "Glob":
            qs = Glob.objects.filter(id__in=id_list)
            print("queryset:", qs)
            
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
    values = serializers.DictField(child=serializers.DictField())

    def validate(self, attrs):
        model_name = attrs.get('model')
        model = get_ModelName_obj_by_name(model_name)
        if model is None:
            raise serializers.ValidationError(f"Invalid model name: {model_name}")
        attrs['model'] = model
        return attrs