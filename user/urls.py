from django.urls import path
from .import views

urlpatterns = [
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('family-types-lst/', views.FamilyTypeListView.as_view(), name='family_types_lst'),
    path('document-types-lst/', views.DocumentTypeListView.as_view(), name='document_types_lst'),
    # path('register/upload-documents/<int:user_id>/', views.DocumentUploadView.as_view(), name='upload_documents'),
    path('register/upload-documents/', views.MultiUserDocumentUploadView.as_view(), name='upload_documents'),
]
