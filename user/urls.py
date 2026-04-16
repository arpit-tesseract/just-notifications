from django.urls import path
from .import views

urlpatterns = [
    path('', views.UserListView.as_view(), name='users'),
    path('register/', views.RegistrationView.as_view(), name='register'),
    # path('register/upload-documents/<int:user_id>/', views.DocumentUploadView.as_view(), name='upload_documents'),
    path('register/upload-documents/', views.MultiUserDocumentUploadView.as_view(), name='upload_documents'),
    path('register/user-suggestions/', views.UserSuggestionsListView.as_view(), name='suggest_users_lst'),
    path('register/user-suggestions/<int:user_id>/', views.UserSuggestionsListView.as_view(), name='suggest_users_lst'),
    
    path('residential-types-lst/', views.ResidentialTypeListView.as_view(), name='family_types_lst'),
    path('document-types-lst/', views.DocumentTypeListView.as_view(), name='document_types_lst'),
    path('relation-type-lst/', views.RelationTypeListView.as_view(), name='relation_types_lst'),
]
