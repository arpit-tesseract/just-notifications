from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import *
from .serializers import *
from rest_framework.decorators import action

import logging
level_logger = logging.getLogger("Levels")

class DimensionListView(APIView):
    def get(self, request):
        dimensions = Dimension.objects.filter(is_active=True)
        serializer = DimensionIdNameSerializer(dimensions, many=True)
        return Response(serializer.data)

class LevelViewSet(viewsets.ModelViewSet):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return LevelSerializer
        return LevelDetailSerializer

    def perform_destroy(self, instance):
        try:
            with transaction.atomic():
                level_logger.info(f"Try to delete(archived) level {instance.name}")
                qs = Level.objects.select_for_update().filter(
                    dimension=instance.dimension,
                    is_archived=False
                )
                
                # update children
                child = qs.filter(parent=instance).first()
                if child:
                    child.parent = instance.parent
                    child.save(update_fields=['parent'])
                
                # CLOSE THE GAP (Shift everyone up)
                qs.filter(sort_order__gt=instance.sort_order).update(sort_order=F('sort_order') - 1)

                # ACTUAL DELETE
                instance.is_archived = True
                instance.save(update_fields=['is_archived'])
                
        except Exception as e:
            level_logger.exception("Failed to delete level:", e)
            return Response({"error": "Failed to delete level"}, status=status.HTTP_400_BAD_REQUEST)
                
        return super().perform_destroy(instance)

class LevelListView(APIView):
    def get(self, request):
        dimension_id = request.query_params.get('dimension_id', "").strip()
        if not dimension_id:
            return Response({"error": "Query paramter 'dimension_id' cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        if not dimension_id.isdigit():
            return Response({"error": "Query paramter 'dimension_id' must be an integer."}, status=status.HTTP_400_BAD_REQUEST)
        
        levels = Level.objects.filter(
            dimension_id=dimension_id,
            is_archived=False
        )
        serializer = LevelIdNameSerializer(levels, many=True)
        return Response(serializer.data)


class NodeViewSet(viewsets.ModelViewSet):
    queryset = Node.objects.select_related("dimension", "level", "parent")
    serializer_class = NodeSerializer
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return NodeSerializer
        return NodeIdNameSerializer
    
    @action(detail=True, methods=['get'])
    def ancestors(self, request, pk=None):
        """
        GET /api/nodes/{id}/ancestors/
        Returns the breadcrumb path (Root -> ... -> Parent -> Self).
        """
        node = self.get_object()
        # Fetch ancestors using the Closure Table (sorted by depth/distance)
        ancestors = Node.objects.filter(
            descendant_closures__descendant=node
        ).order_by('-descendant_closures__depth') # '-depth' gives Root first
        
        serializer = self.get_serializer(ancestors, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def descendants(self, request, pk=None):
        """
        GET /api/nodes/{id}/descendants/
        Returns the entire subtree (Children, Grandchildren, etc.).
        """
        node = self.get_object()
        descendants = Node.objects.filter(
            ancestor_closures__ancestor=node
        ).order_by('ancestor_closures__depth')
        
        serializer = self.get_serializer(descendants, many=True)
        return Response(serializer.data)

    
    def perform_update(self, serializer):
        """
        Handle 'Moving' a node (Changing its parent).
        If the parent changes, we must rebuild the hierarchy paths in NodeClosure.
        """
        old_instance = self.get_object()
        new_parent = serializer.validated_data.get('parent')

        # Check if the parent is actually being changed
        if 'parent' in serializer.validated_data and old_instance.parent != new_parent:
            with transaction.atomic():
                instance = serializer.save()
                
                # 1. Delete ALL old paths where this node was a descendant
                #    (This removes it from the old parent's tree)
                NodeClosure.objects.filter(descendant=instance).delete()
                
                # 2. Re-create the Self-Reference (Depth 0)
                NodeClosure.objects.create(
                    dimension=instance.dimension,
                    ancestor=instance,
                    descendant=instance,
                    depth=0
                )

                # 3. If a new parent is assigned, copy the new parent's ancestors
                if new_parent:
                    parents_closures = NodeClosure.objects.filter(descendant=new_parent)
                    new_closures = []
                    for closure in parents_closures:
                        new_closures.append(NodeClosure(
                            dimension=instance.dimension,
                            ancestor=closure.ancestor, 
                            descendant=instance,       
                            depth=closure.depth + 1
                        ))
                    NodeClosure.objects.bulk_create(new_closures)
                
                # NOTE: If this node has children, their paths are now broken.
                # A full 'Subtree Move' logic is complex. For this version, 
                # we assume you are moving leaf nodes or handling children separately.
        else:
            # Standard update (Name change, etc.)
            serializer.save()