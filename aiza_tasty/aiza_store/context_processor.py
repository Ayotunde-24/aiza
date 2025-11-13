from .models import Category

def categories_processor(request):
    return {'categories': Category.objects.all()}



def cart_context(request):
    cart = request.session.get("cart", {})
    return {
        "cart_count": sum(cart.values())
    }

def cart_and_wishlist_count(request):
    cart = request.session.get("cart", {})
    wishlist = request.session.get("wishlist", [])
    return {
        "cart_count": sum(cart.values()),
        "wishlist_count": len(wishlist),
    }

