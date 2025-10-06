from .forms import *
from .models import *
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Register your models here.
class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    list_display = ('email', 'is_super_admin', 'is_staff')
    list_filter = ('is_staff', 'user_role')
    fieldsets = (
        ('Permissions', {'fields': ('is_staff', 'is_superuser','is_super_admin', 'is_verified',)}),
        (None, {'fields': ('email','contact_no', 'password', 'user_role', 'full_name', 'pet_name', 'father_name', 'photo', 'date_of_birth', 'blood_group')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email','contact_no', 'user_role', 'password1', 'password2','full_name', 'pet_name', 'father_name', 'photo', 'date_of_birth', 'blood_group', 'is_super_admin', 'is_verified', 'is_staff', 'is_superuser')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()

admin.site.register(CustomUser, CustomUserAdmin)

admin.site.register(UserRole)
# admin.site.register(Designation)
admin.site.register(ResidentialDetail)
admin.site.register(RoomDetail)
admin.site.register(RoomMembersDetail)
admin.site.register(Document)
admin.site.register(PersonalDetail)
admin.site.register(ProfessionalDetail)
admin.site.register(Relation)
admin.site.register(ReportCard)

