from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from .import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('', views.UserListView.as_view(), name='users'),
    path('register/', views.RegistrationView.as_view(), name='register'),
    # path('register/upload-documents/<int:user_id>/', views.DocumentUploadView.as_view(), name='upload_documents'),
    path('register/upload-documents/', views.MultiUserDocumentUploadView.as_view(), name='upload_documents'),
    path('register/user-suggestions/', views.UserSuggestionsListView.as_view(), name='suggest_users_lst'),
    path('register/user-suggestions/<int:user_id>/', views.UserSuggestionsListView.as_view(), name='suggest_users_lst'),
    
    path('residential-types-lst/', views.ResidentialTypeListView.as_view(), name='family_types_lst'),
    path('document-types-lst/', views.DocumentTypeListView.as_view(), name='document_types_lst'),
    path('relation-types/', views.RelationTypeView.as_view(), name='relation_types_lst'),
    path('designation-type-lst/', views.DesignationTypeListView.as_view(), name='designation_types_lst'),
    path('business-family-lst/', views.BusinessFamilyListView.as_view(), name='business_family_lst'),
    path('business-family-lst/<int:id>/', views.BusinessFamilyListView.as_view(), name='business_family_lst'),

    path('delete/', views.DeleteUserView.as_view(), name='delete_user'),

    path("family-tree/<int:user_id>/", views.FamilyTreeView.as_view(), name="family_tree"),
    path("family-tree-by-pidhi/<int:user_id>/", views.FamilyTreeByPidhiView.as_view(), name="family_tree_by_pidhi"),
]
