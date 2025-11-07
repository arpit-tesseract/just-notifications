from .forms import *
from .models import *
from django.contrib import admin
from django.db import transaction
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    list_display = ('email', 'is_super_admin', 'is_superuser')
    list_filter = ('is_staff', 'user_role')

    fieldsets = (
        ('Permissions', {'fields': ('is_super_admin', 'is_superuser', 'is_verified',)}),
        (None, {'fields': ('is_archive', 'archived_at', 'email', 'contact_no', 'password', 'user_role', 'full_name',
                           'pet_name', 'father_name', 'photo', 'date_of_birth',
                           'blood_group', 'marital_status', 'expired_date',
                           'category_of_user', 'allocated_rooms', 'residential_details')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            # password1/password2 are used only during add, not change, so it’s fine here
            'fields': ('email', 'contact_no', 'user_role', 'password1', 'password2',
                       'full_name', 'pet_name', 'father_name', 'photo', 'date_of_birth',
                       'blood_group', 'is_super_admin', 'is_verified', 'is_staff', 'is_superuser'),
        }),
    )
    # @transaction.atomic
    # def delete_queryset(self, request, queryset):
    #     """
    #     Handles bulk deletions safely.
    #     Works with confirmation page and triggers post_delete signal.
    #     """
    #     # Capture IDs before deletion
    #     user_ids = list(queryset.values_list("id", flat=True))

    #     # Delete each object (so post_delete runs)
    #     for obj in queryset:
    #         obj.delete()

    #     # Call super() so admin UI behaves correctly
    #     super().delete_queryset(request, queryset)

    # @transaction.atomic
    # def delete_model(self, request, obj):
    #     """
    #     Handles single-object deletion safely.
    #     """
    #     obj.delete()
    #     super().delete_model(request, obj)
        
    def delete_queryset(self, request, queryset):
        # Loop through users to trigger post_delete logic manually
        for user in queryset:
            user.delete()  # this will trigger post_delete signal

    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()


admin.site.register(UserRole)
# admin.site.register(Designation)
admin.site.register(ResidentialDetail)
# admin.site.register(RoomDetail)
# admin.site.register(RoomMembersDetail)
admin.site.register(Document)
admin.site.register(PersonalDetail)
admin.site.register(ProfessionalDetail)
admin.site.register(Relation)
admin.site.register(ReportCard)

