from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.db.models import Q
from common.pagination import CommonPagination
from .models import AttributeTemplate, Unit, AttributeOption, ProductVariantAttributeValue
from .serializers import (
    AttributeTemplateSerializer,
    AttributeTemplateListSerializer,
    AttributeTemplateDropdownSerializer
)

class AttributeTemplateAPIView(APIView):
    def get(self, request, pk=None):
        if pk:
            template = get_object_or_404(AttributeTemplate, pk=pk)
            serializer = AttributeTemplateSerializer(template)
            return Response(serializer.data)
        else:
            queryset = AttributeTemplate.objects.prefetch_related('units', 'options').order_by('-created_at')
            
            # Searching
            search_query = request.query_params.get('search', None)
            if search_query:
                queryset = queryset.filter(
                    Q(name__icontains=search_query) | Q(display_name__icontains=search_query)
                )
                
            # Filtering
            is_active = request.query_params.get('is_active', None)
            if is_active is not None:
                is_active_bool = is_active.lower() in ['true', '1', 't', 'y', 'yes']
                queryset = queryset.filter(is_active=is_active_bool)
                
            input_type = request.query_params.get('input_type', None)
            if input_type:
                queryset = queryset.filter(input_type=input_type)
                
            # Pagination
            paginator = CommonPagination()
            paginated_queryset = paginator.paginate_queryset(queryset, request)
            serializer = AttributeTemplateListSerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)


    def post(self, request):
        serializer = AttributeTemplateSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                validated_data = serializer.validated_data
                units_data = validated_data.pop('units', [])
                options_data = validated_data.pop('options', [])
                input_type = validated_data.get('input_type')
                
                if input_type == 'raw_input':
                    options_data = [] # Ignore options for raw input
                
                template = AttributeTemplate.objects.create(**validated_data)
                
                # Create nested Units and map by name
                created_units_map = {}
                for unit_data in units_data:
                    u = Unit.objects.create(attribute_template=template, **unit_data)
                    created_units_map[u.name] = u
                    
                # Create nested Options
                for option_data in options_data:
                    unit_id = option_data.pop('unit_id', None)
                    unit_name = option_data.pop('unit_name', None)
                    
                    unit_obj = None
                    if unit_id:
                        unit_obj = Unit.objects.filter(id=unit_id, attribute_template=template).first()
                    elif unit_name and unit_name in created_units_map:
                        unit_obj = created_units_map[unit_name]
                        
                    AttributeOption.objects.create(attribute_template=template, unit=unit_obj, **option_data)
                    
            return Response(AttributeTemplateSerializer(template).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        template = get_object_or_404(AttributeTemplate, pk=pk)
        serializer = AttributeTemplateSerializer(template, data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                validated_data = serializer.validated_data
                units_data = validated_data.pop('units', None)
                options_data = validated_data.pop('options', None)
                input_type = validated_data.get('input_type', template.input_type)
                
                # Update main instance
                for attr, value in validated_data.items():
                    setattr(template, attr, value)
                template.save()
                
                created_units_map = {}
                # Sync Nested Units
                if units_data is not None:
                    existing_units = {u.id: u for u in template.units.all()}
                    for unit_data in units_data:
                        unit_id = unit_data.pop('id', None)
                        if unit_id and unit_id in existing_units:
                            unit = existing_units.pop(unit_id)
                            for attr, value in unit_data.items():
                                setattr(unit, attr, value)
                            unit.save()
                            created_units_map[unit.name] = unit
                        else:
                            u = Unit.objects.create(attribute_template=template, **unit_data)
                            created_units_map[u.name] = u
                            
                    # Remove omitted units
                    for unit in existing_units.values():
                        if not ProductVariantAttributeValue.objects.filter(unit=unit).exists():
                            unit.delete()
                        else:
                            unit.is_active = False
                            unit.save()
                            
                # Sync Nested Options
                if input_type == 'raw_input':
                    # Must remove all existing options if type switched to raw_input
                    existing_options = {o.id: o for o in template.options.all()}
                    for option in existing_options.values():
                        if not ProductVariantAttributeValue.objects.filter(attribute_option=option).exists():
                            option.delete()
                        else:
                            option.is_active = False
                            option.save()
                elif options_data is not None:
                    existing_options = {o.id: o for o in template.options.all()}
                    for option_data in options_data:
                        option_id = option_data.pop('id', None)
                        unit_id = option_data.pop('unit_id', None)
                        unit_name = option_data.pop('unit_name', None)
                        
                        unit_obj = None
                        if unit_id:
                            unit_obj = Unit.objects.filter(id=unit_id, attribute_template=template).first()
                        elif unit_name and unit_name in created_units_map:
                            unit_obj = created_units_map[unit_name]
                            
                        if option_id and option_id in existing_options:
                            option = existing_options.pop(option_id)
                            for attr, value in option_data.items():
                                setattr(option, attr, value)
                            option.unit = unit_obj
                            option.save()
                        else:
                            AttributeOption.objects.create(attribute_template=template, unit=unit_obj, **option_data)
                            
                    # Remove omitted options
                    for option in existing_options.values():
                        if not ProductVariantAttributeValue.objects.filter(attribute_option=option).exists():
                            option.delete()
                        else:
                            option.is_active = False
                            option.save()
                        
            return Response(AttributeTemplateSerializer(template).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        template = get_object_or_404(AttributeTemplate, pk=pk)
        if ProductVariantAttributeValue.objects.filter(attribute_template=template).exists():
            return Response(
                {"error": "Cannot delete this template because it is already used in a merchant product."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        template.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class AttributeTemplateDropdownAPIView(APIView):
    def get(self, request):
        queryset = AttributeTemplate.objects.filter(is_active=True).order_by('-created_at')
        
        # Searching
        search_query = request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | Q(display_name__icontains=search_query)
            )
            
        # Pagination (chunks of 10)
        paginator = CommonPagination()
        paginator.page_size = 10
        
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = AttributeTemplateDropdownSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)