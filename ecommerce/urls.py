from django.urls import path
from .views import (
    AttributeTemplateAPIView, AttributeTemplateDropdownAPIView,
    ProductTemplateAPIView, ProductTemplateDropdownAPIView
)

urlpatterns = [
    # Attribute Template Endpoints
    path('attribute-templates/dropdown/', AttributeTemplateDropdownAPIView.as_view(), name='attribute-template-dropdown'),
    path('attribute-templates/', AttributeTemplateAPIView.as_view(), name='attribute-template-list'),
    path('attribute-templates/<int:pk>/', AttributeTemplateAPIView.as_view(), name='attribute-template-detail'),
    
    # Product Template Endpoints
    path('product-templates/dropdown/', ProductTemplateDropdownAPIView.as_view(), name='product-template-dropdown'),
    path('product-templates/', ProductTemplateAPIView.as_view(), name='product-template-list'),
    path('product-templates/<int:pk>/', ProductTemplateAPIView.as_view(), name='product-template-detail'),
]
