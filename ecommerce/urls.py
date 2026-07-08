from django.urls import include, path
from rest_framework.routers import DefaultRouter

from ecommerce import views

router = DefaultRouter()
# Admin master config
router.register(r'unit-types', views.UnitTypeViewSet)
router.register(r'units', views.UnitViewSet)
router.register(r'attributes', views.AttributeViewSet)
router.register(r'attribute-options', views.AttributeOptionViewSet)
router.register(r'templates', views.ProductTemplateViewSet)
router.register(r'template-attributes', views.TemplateAttributeViewSet)
# Merchant catalog
router.register(r'products', views.ProductViewSet)
router.register(r'product-images', views.ProductImageViewSet)
# Storefront
router.register(r'store-settings', views.MerchantStoreSettingViewSet)
router.register(r'promotions', views.ProductPromotionViewSet)
router.register(r'reviews', views.ProductReviewViewSet)
# Orders
router.register(r'my-orders', views.BuyerOrderViewSet, basename='my-orders')
router.register(r'admin-orders', views.AdminOrderViewSet, basename='admin-orders')
router.register(r'vendor-orders', views.VendorOrderViewSet, basename='vendor-orders')
router.register(r'my-deliveries', views.AgentDeliveryViewSet, basename='my-deliveries')

urlpatterns = [
    path('', include(router.urls)),

    # Dropdowns
    path('unit-types/dropdown/', views.UnitTypeDropdownView.as_view()),
    path('templates/dropdown/', views.ProductTemplateDropdownView.as_view()),

    # Inventory
    path('variants/<int:pk>/stock/', views.VariantStockView.as_view(), name='variant-stock'),

    # Storefront (buyer)
    path('feed/', views.FeedView.as_view(), name='feed'),
    path('feed/products/<int:pk>/', views.PublicProductDetailView.as_view(), name='public-product'),
    path('wishlist/', views.WishlistView.as_view(), name='wishlist'),

    # Cart & checkout
    path('cart/', views.CartView.as_view(), name='cart'),
    path('orders/place/', views.PlaceOrderView.as_view(), name='place-order'),
]
