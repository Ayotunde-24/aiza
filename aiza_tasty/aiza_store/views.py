from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from .models import Product, Category, Order, OrderItem
from django.contrib.auth.forms import UserCreationForm
from django.contrib.admin.views.decorators import staff_member_required
from django import forms
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q
import csv
from django.http import HttpResponse

# ---------- HOME ----------
from django.db.models import Q

def home(request):
    query = request.GET.get('q')  # Get search term from the form
    categories = Category.objects.all()

    # 🔍 If user is searching
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(category__name__icontains=query)
        )
        context = {
            'query': query,
            'search_results': products,
            'categories': categories,
        }
        return render(request, 'aiza_store/search_results.html', context)

    # 🏠 Default homepage display
    category_products = {}
    for category in categories:
        # Only take first 3 products per category
        category_products[category] = Product.objects.filter(category=category)[:3]

    # 🧁 Featured products (latest 4)
    featured_products = Product.objects.order_by('-id')[:4]

    return render(request, "aiza_store/home.html", {
        "categories": categories,
        "category_products": category_products,
        "featured_products": featured_products,
    })


# ---------- SIGNUP ----------
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # or wherever you want to send them after signup
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


# ---------- CATEGORY ----------
def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category).order_by("-id")

    paginator = Paginator(products, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "aiza_store/category.html", {
        "category": category,
        "page_obj": page_obj,
    })


# ---------- CART ----------
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get("cart", {})
    product_id_str = str(product_id)
    cart[product_id_str] = cart.get(product_id_str, 0) + 1
    request.session["cart"] = cart

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": True, "cart_count": sum(cart.values())})
    return redirect("cart_view")


def cart_view(request):
    cart = request.session.get("cart", {})
    products = Product.objects.filter(id__in=cart.keys())

    cart_items, total = [], 0
    for product in products:
        qty = cart[str(product.id)]
        subtotal = product.price * qty
        total += subtotal
        cart_items.append({
            "product": product,
            "quantity": qty,
            "subtotal": subtotal,
        })

    return render(request, "aiza_store/cart.html", {
        "cart_items": cart_items,
        "total": total,
    })


def remove_from_cart(request, product_id):
    cart = request.session.get("cart", {})
    product_id_str = str(product_id)
    if product_id_str in cart:
        del cart[product_id_str]
        request.session["cart"] = cart
    return redirect("cart_view")


def update_cart(request, product_id):
    if request.method == "POST":
        cart = request.session.get("cart", {})
        product_id_str = str(product_id)
        new_qty = int(request.POST.get("quantity", 1))

        if new_qty > 0:
            cart[product_id_str] = new_qty
        else:
            cart.pop(product_id_str, None)

        request.session["cart"] = cart

        products = Product.objects.filter(id__in=cart.keys())
        total, subtotal = 0, 0
        for product in products:
            qty = cart[str(product.id)]
            total += product.price * qty
            if str(product.id) == product_id_str:
                subtotal = product.price * qty

        return JsonResponse({
            "success": True,
            "subtotal": float(subtotal),
            "total": float(total),
            "total_items": sum(cart.values()),
        })
    return JsonResponse({"success": False}, status=400)


# Wishlist
def wishlist_view(request):
    wishlist = request.session.get("wishlist", [])
    products = Product.objects.filter(id__in=wishlist)
    return render(request, "aiza_store/wishlist.html", {
        "products": products
    })

def add_to_wishlist(request, product_id):
    wishlist = request.session.get("wishlist", [])
    product_id_str = str(product_id)

    if product_id_str not in wishlist:
        wishlist.append(product_id_str)
    else:
        wishlist.remove(product_id_str)  # toggle off if already in

    request.session["wishlist"] = wishlist
    return JsonResponse({
        "success": True,
        "wishlist_count": len(wishlist),
        "status": "added" if product_id_str in wishlist else "removed"
    })

# ---------- CHECKOUT ----------
def checkout(request):
    cart = request.session.get("cart", {})
    products = Product.objects.filter(id__in=cart.keys())

    if request.method == "POST":
        name = request.POST["name"]
        email = request.POST["email"]
        phone = request.POST["phone"]
        address = request.POST["address"]

        order = Order.objects.create(
            name=name, email=email, phone=phone, address=address, total_price=0
        )

        total = 0
        for product in products:
            qty = cart[str(product.id)]
            subtotal = product.price * qty
            total += subtotal
            OrderItem.objects.create(
                order=order, product=product, quantity=qty, price=product.price
            )

        order.total_price = total
        order.save()
        request.session["cart"] = {}

        subject = f"Order Confirmation - Aiza Tasty Pastries (#{order.id})"
        message = f"""
Hello {name},

Thank you for your order at Aiza Tasty Pastries 🎂

Order ID: {order.id}
Total: ${order.total_price}

We will contact you soon to confirm delivery.

Best regards,
Aiza Tasty Pastries
"""
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
        return render(request, "aiza_store/order_success.html", {"order": order})

    return render(request, "aiza_store/checkout.html", {
        "products": products,
        "cart": cart,
    })

# ---------- ADMIN DASHBOARD ---------
# Forms
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'image', 'category']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']


@staff_member_required
def admin_dashboard(request):
    products = Product.objects.all().order_by('-id')
    categories = Category.objects.all().order_by('name')
    orders = Order.objects.all().order_by('-created_at')

    product_form = ProductForm(request.POST or None, request.FILES or None)
    category_form = CategoryForm(request.POST or None)

    if 'add_product' in request.POST and product_form.is_valid():
        product_form.save()
        return redirect('admin_dashboard')

    if 'add_category' in request.POST and category_form.is_valid():
        category_form.save()
        return redirect('admin_dashboard')

    if request.GET.get('delete_product'):
        Product.objects.filter(id=request.GET.get('delete_product')).delete()
        return redirect('admin_dashboard')

    if request.GET.get('delete_category'):
        Category.objects.filter(id=request.GET.get('delete_category')).delete()
        return redirect('admin_dashboard')

    return render(request, 'aiza_store/admin_dashboard.html', {
        'product_form': product_form,
        'category_form': category_form,
        'products': products,
        'categories': categories,
        'orders': orders
    })


# ✅ Edit product view
@staff_member_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = ProductForm(instance=product)
    return render(request, 'aiza_store/edit_product.html', {'form': form, 'product': product})


# ✅ Edit category view
@staff_member_required
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'aiza_store/edit_category.html', {'form': form, 'category': category})


# Secure product deletion
@staff_member_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect('admin_dashboard')


# Product search/filter
@staff_member_required
def search_products(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(name__icontains=query)
    return render(request, 'aiza_store/admin_dashboard.html', {'products': products, 'query': query})

# Order management
@staff_member_required
def manage_orders(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'aiza_store/manage_orders.html', {'orders': orders})

# User management
@staff_member_required
def manage_users(request):
    users = User.objects.all()
    return render(request, 'aiza_store/manage_users.html', {'users': users})

# Dashboard analytics
@staff_member_required
def dashboard_analytics(request):
    total_sales = Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_orders = Order.objects.count()
    top_products = Product.objects.annotate(order_count=Count('orderitem')).order_by('-order_count')[:5]
    return render(request, 'aiza_store/dashboard_analytics.html', {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'top_products': top_products
    })

# Bulk actions (delete multiple products)
@staff_member_required
def bulk_delete_products(request):
    if request.method == 'POST':
        ids = request.POST.getlist('product_ids')
        Product.objects.filter(id__in=ids).delete()
    return redirect('admin_dashboard')

# Image gallery (list all product images)
@staff_member_required
def image_gallery(request):
    products = Product.objects.exclude(image='')
    return render(request, 'aiza_store/image_gallery.html', {'products': products})

# Admin notifications (example: new orders)
@staff_member_required
def admin_notifications(request):
    new_orders = Order.objects.filter(status='new').count()
    return JsonResponse({'new_orders': new_orders})

# Data export (CSV)
@staff_member_required
def export_products_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Price', 'Category'])
    for p in Product.objects.all():
        writer.writerow([p.id, p.name, p.price, p.category.name])
    return response

# Custom permissions (example: only superusers can delete users)
@staff_member_required
def delete_user(request, user_id):
    if request.user.is_superuser:
        User.objects.filter(id=user_id).delete()
    return redirect('manage_users')

