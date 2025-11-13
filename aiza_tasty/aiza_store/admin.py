from django.contrib import admin
from .models import Category, Product, Order, OrderItem

# Register your models here.
class OrderItemInline(admin.TabularInline):  # show order items inside Order
    model = OrderItem
    extra = 0


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone', 'total_price', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'email', 'phone')
    inlines = [OrderItemInline]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category')
    list_filter = ('category',)
    search_fields = ('name',)
    
admin.site.register(Category)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
