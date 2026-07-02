from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from .import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/send-otp-contact-no/',views.LoginOTPView.as_view(), name='send-otp'),
    path('login/verify-otp-contact-no/',views.LoginPhoneOTPView.as_view(), name='verify-otp'),

    path('', views.UserListView.as_view(), name='users'),
    path('register/', views.RegistrationView.as_view(), name='register'),
    # path('register/upload-documents/<int:user_id>/', views.DocumentUploadView.as_view(), name='upload_documents'),
    path('register/upload-documents/', views.MultiUserDocumentUploadView.as_view(), name='upload_documents'),
    path('register/user-suggestions/dropdown/', views.UserSuggestionsListView.as_view(), name='suggest_users_lst'),
    path('register/user-suggestions/<int:user_id>/dropdown/', views.UserSuggestionsListView.as_view(), name='suggest_users_lst'),
    
    path('residential-types/dropdown/', views.ResidentialTypeListView.as_view(), name='family_types_dropdown'),
    path('document-types/dropdown/', views.DocumentTypeListView.as_view(), name='document_types_dropdown'),
    path('relation-types/dropdown/', views.RelationTypeView.as_view(), name='relation_types_dropdown'),
    path('designation-types/dropdown/', views.DesignationTypeListView.as_view(), name='designation_types_dropdown'),
    path('business-familes/dropdown/', views.BusinessFamilyListView.as_view(), name='business_familes_dropdown'),
    path('business-familes/<int:id>/', views.BusinessFamilyListView.as_view(), name='business_familes_dropdown'),

    path('delete/', views.DeleteUserView.as_view(), name='delete_user'),

    path("family-tree/<int:user_id>/", views.FamilyTreeView.as_view(), name="family_tree"),
    path("family-tree-by-pidhi/<int:user_id>/", views.FamilyTreeByPidhiView.as_view(), name="family_tree_by_pidhi"),

    path('roles/dropdown/', views.UserRoleListView.as_view(), name='roles'),
    path('business/register/', views.BusinessRegisterView.as_view(), name='business_register'),
    path('business/member-suggestions/', views.BusinessMemberSuggestionView.as_view(), name='business_member_suggestions'),
    path('admin/register/', views.AdminRegistrationView.as_view(), name='admin_register'),
]
