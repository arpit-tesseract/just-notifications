from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.db.models import Q
from common.pagination import CommonPagination
from .models import (
    AttributeTemplate, Unit, AttributeOption, ProductVariantAttributeValue,
    ProductTemplate, ProductTemplateAttribute, Product, ProductNodeMapping
)
from .serializers import (
    AttributeTemplateSerializer,
    AttributeTemplateListSerializer,
    AttributeTemplateDropdownSerializer,
    ProductTemplateInputSerializer,
    ProductTemplateOutputSerializer,
    ProductTemplateListSerializer,
    ProductTemplateDropdownSerializer
)

class AttributeTemplateAPIView(APIView):
    def get(self, request, pk=None):
        if pk:
            template = get_object_or_404(AttributeTemplate, pk=pk)
            serializer = AttributeTemplateListSerializer(template)
            return Response(serializer.data)
        else:
            queryset = AttributeTemplate.objects.prefetch_related('units', 'options').order_by('-created_at')
            
            search_query = request.query_params.get('search', None)
            if search_query:
                queryset = queryset.filter(
                    Q(name__icontains=search_query) | Q(display_name__icontains=search_query)
                )
                
            is_active = request.query_params.get('is_active', None)
            if is_active is not None:
                is_active_bool = is_active.lower() in ['true', '1', 't', 'y', 'yes']
                queryset = queryset.filter(is_active=is_active_bool)
                
            input_type = request.query_params.get('input_type', None)
            if input_type:
                queryset = queryset.filter(input_type=input_type)
                
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
                    options_data = []
                
                template = AttributeTemplate.objects.create(**validated_data)
                
                created_units_map = {}
                for unit_data in units_data:
                    u = Unit.objects.create(attribute_template=template, **unit_data)
                    created_units_map[u.name] = u
                    
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
                
                for attr, value in validated_data.items():
                    setattr(template, attr, value)
                template.save()
                
                created_units_map = {}
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
                            
                    for unit in existing_units.values():
                        if not ProductVariantAttributeValue.objects.filter(unit=unit).exists():
                            unit.delete()
                        else:
                            unit.is_active = False
                            unit.save()
                            
                if input_type == 'raw_input':
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
        
        search_query = request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | Q(display_name__icontains=search_query)
            )
            
        paginator = CommonPagination()
        paginator.page_size = 10
        
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = AttributeTemplateDropdownSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)


class ProductTemplateAPIView(APIView):
    def get(self, request, pk=None):
        if pk:
            template = get_object_or_404(ProductTemplate, pk=pk)
            serializer = ProductTemplateOutputSerializer(template)
            return Response(serializer.data)
        else:
            queryset = ProductTemplate.objects.prefetch_related('attribute_templates__attribute_template').order_by('-created_at')
            
            search_query = request.query_params.get('search', None)
            if search_query:
                queryset = queryset.filter(
                    Q(name__icontains=search_query) | Q(display_name__icontains=search_query)
                )
                
            is_active = request.query_params.get('is_active', None)
            if is_active is not None:
                is_active_bool = is_active.lower() in ['true', '1', 't', 'y', 'yes']
                queryset = queryset.filter(is_active=is_active_bool)
                
            paginator = CommonPagination()
            paginated_queryset = paginator.paginate_queryset(queryset, request)
            serializer = ProductTemplateListSerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = ProductTemplateInputSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                validated_data = serializer.validated_data
                attributes_data = validated_data.pop('attributes', [])
                professional_details = validated_data.pop('professional_details', {})
                
                template = ProductTemplate.objects.create(**validated_data)
                
                for attr_data in attributes_data:
                    attribute_template_id = attr_data.pop('attribute_template_id', None)
                    attr_template = AttributeTemplate.objects.filter(id=attribute_template_id).first()
                    if attr_template:
                        ProductTemplateAttribute.objects.create(
                            product_template=template, 
                            attribute_template=attr_template,
                            **attr_data
                        )
                        
                if professional_details:
                    for level_id, node_id in professional_details.items():
                        if level_id and node_id:
                            ProductNodeMapping.objects.create(
                                product_template=template,
                                level_id=int(level_id),
                                node_id=int(node_id)
                            )
                        
            return Response(ProductTemplateOutputSerializer(template).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        template = get_object_or_404(ProductTemplate, pk=pk)
        serializer = ProductTemplateInputSerializer(template, data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                validated_data = serializer.validated_data
                attributes_data = validated_data.pop('attributes', None)
                professional_details = validated_data.pop('professional_details', None)
                
                for attr, value in validated_data.items():
                    setattr(template, attr, value)
                template.save()
                
                if attributes_data is not None:
                    existing_attrs = {a.attribute_template_id: a for a in template.attribute_templates.all()}
                    for attr_data in attributes_data:
                        attribute_template_id = attr_data.pop('attribute_template_id', None)
                        
                        if attribute_template_id and attribute_template_id in existing_attrs:
                            attr_obj = existing_attrs.pop(attribute_template_id)
                            for attr_k, value in attr_data.items():
                                setattr(attr_obj, attr_k, value)
                            attr_obj.save()
                        else:
                            attr_template = AttributeTemplate.objects.filter(id=attribute_template_id).first()
                            if attr_template:
                                ProductTemplateAttribute.objects.create(
                                    product_template=template,
                                    attribute_template=attr_template,
                                    **attr_data
                                )
                                
                    for attr_obj in existing_attrs.values():
                        in_use = ProductVariantAttributeValue.objects.filter(
                            product_variant__product__product_template=template,
                            attribute_template=attr_obj.attribute_template
                        ).exists()
                        
                        if not in_use:
                            attr_obj.delete()
                        else:
                            attr_obj.is_active = False
                            attr_obj.save()
                            
                if professional_details is not None:
                    ProductNodeMapping.objects.filter(product_template=template).delete()
                    for level_id, node_id in professional_details.items():
                        if level_id and node_id:
                            ProductNodeMapping.objects.create(
                                product_template=template,
                                level_id=int(level_id),
                                node_id=int(node_id)
                            )
                            
            return Response(ProductTemplateOutputSerializer(template).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        template = get_object_or_404(ProductTemplate, pk=pk)
        if Product.all_objects.filter(product_template=template).exists():
            return Response(
                {"error": "Cannot delete this product template because it is actively used in one or more products."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        template.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ProductTemplateDropdownAPIView(APIView):
    def get(self, request):
        queryset = ProductTemplate.objects.filter(is_active=True).order_by('-created_at')
        
        search_query = request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | Q(display_name__icontains=search_query)
            )
            
        paginator = CommonPagination()
        paginator.page_size = 10
        
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = ProductTemplateDropdownSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)
