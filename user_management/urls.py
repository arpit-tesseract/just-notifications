from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# router.register(r'users', views.CustomUserViewSet, basename='users')

urlpatterns = [
    path('login/', views.LoginWithEmailPasswordView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # used for refresh token
    # path('token/verify/', TokenVerifyView.as_view(), name='token_verify'), # used for verify token
    
    path('register/', views.RegisterationView.as_view(), name='register'),
    path('upload-photo/<int:user_id>', views.UserPhotoUploadView.as_view(), name='upload_photo'),
    path('upload-documents/<int:user_id>', views.UserDocumentUploadView.as_view(), name='upload_documents'),
]
