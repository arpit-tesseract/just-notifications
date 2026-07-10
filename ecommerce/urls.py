from django.urls import path
from .views import AttributeTemplateAPIView, AttributeTemplateDropdownAPIView

urlpatterns = [
    path('attribute-templates/dropdown/', AttributeTemplateDropdownAPIView.as_view(), name='attribute-template-dropdown'),
    path('attribute-templates/', AttributeTemplateAPIView.as_view(), name='attribute-template-list'),
    path('attribute-templates/<int:pk>/', AttributeTemplateAPIView.as_view(), name='attribute-template-detail'),
]
