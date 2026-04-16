from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import (
    UserRole, UserManager, UserResidentialDetails, User, UserProfile,
    DocumentType, UserDocument, UserProfessionalDetails, UserPersonalDetails,
    ResidentialType, Family, FamilyMember, RelationType, FamilyResident, UserRelations
)

@admin.register(UserRole)
class UserRoleAdmin(SimpleHistoryAdmin):
    list_display = ('display_name', 'name', 'parent', 'is_active')
    search_fields = ('name', 'display_name')
    list_filter = ('is_active',)


@admin.register(UserResidentialDetails)
class UserResidentialDetailsAdmin(SimpleHistoryAdmin):
    # JSON fields are hard to list, so we display the ID and audit fields
    list_display = ('id', 'created_at', 'updated_at') 


@admin.register(User)
class UserAdmin(SimpleHistoryAdmin):
    list_display = ('full_name', 'contact_no', 'is_staff', 'is_superuser', 'is_verified', 'created_at')
    search_fields = ('full_name', 'contact_no', 'email')
    list_filter = ('is_staff', 'is_superuser', 'is_verified', 'roles')
    
    # CRITICAL: Prevents admins from accidentally overwriting hashed passwords with plain text
    readonly_fields = ('password', 'last_login')


@admin.register(UserProfile)
class UserProfileAdmin(SimpleHistoryAdmin):
    list_display = ('user', 'gender', 'blood_group', 'marital_status', 'dob')
    search_fields = ('user__full_name', 'user__contact_no', 'pet_name', 'father_name')
    list_filter = ('gender', 'blood_group', 'marital_status')


@admin.register(DocumentType)
class DocumentTypeAdmin(SimpleHistoryAdmin):
    list_display = ('display_name', 'name', 'is_required', 'is_active')
    search_fields = ('name', 'display_name')
    list_filter = ('is_required', 'is_active')


@admin.register(UserDocument)
class UserDocumentAdmin(SimpleHistoryAdmin):
    list_display = ('user', 'document_type', 'document_no', 'created_at')
    search_fields = ('user__full_name', 'user__contact_no', 'document_no')
    list_filter = ('document_type',)


@admin.register(UserProfessionalDetails)
class UserProfessionalDetailsAdmin(SimpleHistoryAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__full_name', 'user__contact_no')


@admin.register(UserPersonalDetails)
class UserPersonalDetailsAdmin(SimpleHistoryAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__full_name', 'user__contact_no')


@admin.register(ResidentialType)
class ResidentialTypeAdmin(SimpleHistoryAdmin):
    list_display = ('display_name', 'name', 'is_active')
    search_fields = ('name', 'display_name')
    list_filter = ('is_active',)


@admin.register(Family)
class FamilyAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'name', 'created_at')


@admin.register(FamilyMember)
class FamilyMemberAdmin(SimpleHistoryAdmin):
    list_display = ('family', 'user', 'self_relation_type', 'is_main_user', 'created_at')
    search_fields = ('user__full_name', 'user__contact_no')
    list_filter = ('family', 'is_main_user')


@admin.register(FamilyResident)
class FamilyResidentAdmin(SimpleHistoryAdmin):
    list_display = ('family', 'residential_details', 'residential_type', 'created_at')
    list_filter = ('family', 'residential_type')


@admin.register(RelationType)
class RelationTypeAdmin(SimpleHistoryAdmin):
    list_display = ('display_name', 'name', 'is_active')
    search_fields = ('name', 'display_name')
    list_filter = ('is_active',)


@admin.register(UserRelations)
class UserRelationsAdmin(SimpleHistoryAdmin):
    list_display = ('from_user', 'relation_type', 'to_user', 'created_at')