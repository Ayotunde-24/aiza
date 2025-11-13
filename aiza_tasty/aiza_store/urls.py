from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
urlpatterns = [
    path("", views.home, name="home"),
    path("category/<int:category_id>/", views.category_products, name="category_products"),
    path("add-to-cart/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/", views.cart_view, name="cart_view"),
    path("cart/remove/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("cart/update/<int:product_id>/", views.update_cart, name="update_cart"),
    path("checkout/", views.checkout, name="checkout"),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('accounts/', include('django.contrib.auth.urls')),  
    path('accounts/signup/', views.signup, name='signup'),
    path('myadmin/', views.admin_dashboard, name='admin_dashboard'),
    path('myadmin/edit/<int:product_id>/', views.edit_product, name='edit_product'),
     path('edit-category/<int:category_id>/', views.edit_category, name='edit_category'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('myadmin/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('myadmin/search/', views.search_products, name='search_products'),
    path('myadmin/orders/', views.manage_orders, name='manage_orders'),
    path('myadmin/users/', views.manage_users, name='manage_users'),
    path('myadmin/analytics/', views.dashboard_analytics, name='dashboard_analytics'),
    path('myadmin/bulk_delete/', views.bulk_delete_products, name='bulk_delete_products'),
    path('myadmin/gallery/', views.image_gallery, name='image_gallery'),
    path('myadmin/notifications/', views.admin_notifications, name='admin_notifications'),
    path('myadmin/export/', views.export_products_csv, name='export_products_csv'),
    path('myadmin/delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
]
from django.conf import settings