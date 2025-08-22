from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(CustomUser)
admin.site.register(Address)
admin.site.register(RoomDetail)
admin.site.register(RoomMembersDetail)
admin.site.register(PersonalTable)
admin.site.register(Relation)
admin.site.register(ProfessionalDetail)
admin.site.register(ReportCard)
admin.site.register(ResidentialDetail)