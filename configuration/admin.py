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

