from django.contrib import admin
from .models import *
from simple_history.admin import SimpleHistoryAdmin
# Register your models here.

@admin.register(Dimension)
class DimensionAdmin(SimpleHistoryAdmin):
    list_display = ['name', 'is_active', 'created_at', 'updated_at']
    
@admin.register(Level)
class LevelAdmin(SimpleHistoryAdmin):
    list_display = ['dimension', 'name', 'parent', 'single_mode', 'is_mandatory', 'sort_order', 'is_deleted', 'created_at', 'updated_at']
    list_filter = ['is_deleted', 'is_mandatory', 'dimension', 'parent']
    sortable_by = ['sort_order']
    
    def get_queryset(self, request):
        return self.model.all_objects.all()
    
@admin.register(Node)
class NodeAdmin(SimpleHistoryAdmin):
    list_display = ['dimension', 'level', 'parent', 'name', 'code', 'is_deleted', 'created_at', 'updated_at']
    list_filter = ['is_deleted', 'dimension', 'level']
    
    def get_queryset(self, request):
        return self.model.all_objects.all()

@admin.register(NodeAlias)
class NodeAliasAdmin(SimpleHistoryAdmin):
    list_display = ['node', 'name']

@admin.register(NodeEventLog)
class NodeEventLogAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'source_node', 'target_node', 'effective_date', 'performed_by', 'created_at']
    list_filter = ['event_type', 'effective_date']
    search_fields = ['source_node__name', 'target_node__name']

@admin.register(NodeClosure)
class NodeClosureAdmin(admin.ModelAdmin):
    list_display = ['ancestor', 'descendant', 'depth']
    list_filter = ['ancestor__level', 'ancestor__level__dimension__name']


@admin.register(NodeRelationship)
class NodeRelationshipAdmin(SimpleHistoryAdmin):
    list_display = ['territory', 'relationship_type', 'controller', 'is_deleted']
    def get_queryset(self, request):
        return self.model.all_objects.all()

# admin.site.register(SampleFile)
# admin.site.register(Glob)
# admin.site.register(Continent)
# admin.site.register(Country)
# admin.site.register(State)
# admin.site.register(District)
# admin.site.register(Taluka)
# admin.site.register(CityVillage)
# admin.site.register(Ward)
# admin.site.register(Society)
# admin.site.register(Block)
# admin.site.register(Floor)
# admin.site.register(House)
# admin.site.register(Room)


# admin.site.register(Religion)
# admin.site.register(Sampraday)
# admin.site.register(Panth)
# admin.site.register(Awastha)
# admin.site.register(Varna)
# admin.site.register(Caste)
# admin.site.register(SubCaste)
# admin.site.register(Gotra)
# admin.site.register(SubGotra)
# admin.site.register(Kul)
# admin.site.register(Vansh)
# admin.site.register(Family)
# admin.site.register(Pidhi)
# admin.site.register(Calibration)


# admin.site.register(Section)
# admin.site.register(Class)
# admin.site.register(ProfCategory)
# admin.site.register(ProfSubCategory)
# admin.site.register(Sector)
# admin.site.register(SubSector)
# admin.site.register(Department)
# admin.site.register(SubDepartment)
# admin.site.register(Type)
# admin.site.register(Brand)
# admin.site.register(Product)

# admin.site.register(Designation)

# admin.site.register(WardFlash)
# admin.site.register(SocietyFlash)
# admin.site.register(BlockFlash)
# admin.site.register(FloorFlash)
# admin.site.register(HouseFlash)
# admin.site.register(RoomFlash)
# admin.site.register(RoomType)

# admin.site.register(ModelName)
# admin.site.register(ModelAccess)
# admin.site.register(RecordRule)

# admin.site.register(PermissionModule)
# admin.site.register(PermissionAction)