from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# router.register(r'users', views.CustomUserViewSet, basename='users')

urlpatterns = [
    # path('', include(router.urls)),
    # path('', views.UserDetailView.as_view(), name='user_details'),
    # path('<int:user_id>/', views.UserDetailView.as_view(), name='user_details'),
    
    path('login/', views.LoginWithEmailPasswordView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # used for refresh token
    # path('token/verify/', TokenVerifyView.as_view(), name='token_verify'), # used for verify token
    
    path('', views.RegisterationView.as_view(), name='register'),
    path('<int:user_id>/', views.RegisterationView.as_view(), name='register'),
    path('upload-photo/<int:user_id>', views.UserPhotoUploadView.as_view(), name='upload_photo'),
    path('upload-documents/<int:user_id>', views.UserDocumentUploadView.as_view(), name='upload_documents'),
    path('suggest-users/', views.UserSuggestionsView.as_view(), name='suggest_users'),
    
    # path('', views.CustomUserViewSet.as_view(), name='users'),
    path('user-lst/', views.UserListView.as_view(), name='user_lst'),
    
    path('roles/', views.GetUserRoleView.as_view(), name='user_roles'),
    path('roles/<int:user_id>/', views.GetUserRoleView.as_view(), name='user_roles'),
    path('role-lst/', views.UserRoleListView.as_view(), name='user_roles'),
    path('assign-roles/', views.UserRoleAssignView.as_view(), name='assign_roles'),
    path('remove-roles/', views.UserRoleRemoveView.as_view(), name='remove_roles'),
    
    path('model-access-rights/', views.ModelAccessView.as_view(), name='model_access'),
    path('model-access-rights/<int:user_id>/', views.ModelAccessView.as_view(), name='model_access'),
    
    path('record-rules/', views.RecordRuleView.as_view(), name='record_rules'),
    path('record-rule-lst/', views.RecordRuleListView.as_view(), name='record_rules'),
]
