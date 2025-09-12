from .forms import *
from .models import *
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Register your models here.
class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    list_display = ('email', 'user_role', 'is_staff')
    list_filter = ('is_staff', 'user_role')
    fieldsets = (
        ('Permissions', {'fields': ('is_staff', 'is_superuser','is_system_user', 'is_verified',)}),
        (None, {'fields': ('email', 'password', 'designation', 'user_role', 'date_of_birth', 'category_of_user')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'user_role', 'designation', 'password1', 'password2', 'is_staff', 'is_superuser')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()

admin.site.register(CustomUser, CustomUserAdmin)

admin.site.register(UserRole)
admin.site.register(Designation)
admin.site.register(Address)
admin.site.register(RoomDetail)
admin.site.register(RoomMembersDetail)
admin.site.register(PersonalTable)
admin.site.register(Relation)
admin.site.register(ProfessionalDetail)
admin.site.register(ReportCard)
admin.site.register(ResidentialDetail)

