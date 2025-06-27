from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import logout
from .models import Customer, Product, Cart, OrderPlaced, Color, RAM, Size
from .forms import CustomerRegistrationForm, CustomerProfileForm, CustomerAddressForm
from django.contrib import messages
from django.db.models import Q
from app.models import Contact
from django.urls import reverse
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.conf import settings
import stripe , json 
stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def create_checkout_session(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    YOUR_DOMAIN = 'http://localhost:8000/'
    try:
        address_id = request.GET.get('address_id') or request.POST.get('address_id')
        product_id = request.GET.get('product_id') or request.POST.get('product_id')
        quantity = request.GET.get('quantity') or request.POST.get('quantity')
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            quantity = 1

        line_items = []
        if product_id:
            product = get_object_or_404(Product, id=product_id)
            image_url = request.build_absolute_uri(product.product_image.url) if product.product_image else ""
            line_items.append({
                'price_data': {
                    'currency': 'inr',
                    'unit_amount': int(product.discounted_price * 100),
                    'product_data': {
                        'name': product.title,
                        'images': [image_url] if image_url else [],
                    },
                },
                'quantity': quantity,
            })
            request.session['buy_now'] = {
                'product_id': product_id,
                'quantity': quantity,
            }    
        else:
            cart_items = Cart.objects.filter(user=request.user)
            for item in cart_items:
                product = item.product
                image_url = request.build_absolute_uri(product.product_image.url) if getattr(product, 'product_image', None) else ""
                line_items.append({
                    'price_data': {
                        'currency': 'inr',
                        'unit_amount': int(product.discounted_price * 100),
                        'product_data': {
                            'name': product.title,
                            'images': [image_url] if image_url else [],
                        },
                    },
                    'quantity': item.quantity,
                })
            request.session['buy_now'] = None

        shipping_amount = 70 * 100 
        line_items.append({
            'price_data': {
                'currency': 'inr',
                'unit_amount': shipping_amount,
                'product_data': {'name': 'Shipping Charge'},
            },
            'quantity': 1,
        })

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            metadata={
                'user_id': str(request.user.id),
                'address_id': str(address_id) if address_id else '',
                'product_id': str(product_id) if product_id else '',
                'quantity': str(quantity) if product_id else '',
            },
            mode='payment',
            success_url=YOUR_DOMAIN + 'payment-success/?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=YOUR_DOMAIN + reverse('payment-failed'),
        )
        return JsonResponse({'sessionId': checkout_session.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
@login_required
def payment_successful(request):
    user = request.user
    session_id = request.GET.get('session_id')
    if not session_id:
        return render(request, 'app/payment-failed.html', {'error': 'No session_id provided.'})

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        return render(request, 'app/payment-failed.html', {'error': str(e)})

    amount_total = session.get('amount_total')
    payment_status = session.get('payment_status')
    payment_id = session.get('payment_intent')

    customer = Customer.objects.filter(user=user).first()
    orders = []
    buy_now_info = request.session.get('buy_now')   

    if buy_now_info:
        product_id = buy_now_info.get('product_id')
        quantity = buy_now_info.get('quantity', 1)
        product = get_object_or_404(Product, id=product_id)
        try:
            quantity = int(quantity)
            if quantity < 1:
                quantity = 1
        except (TypeError, ValueError):
            quantity = 1

        order = OrderPlaced.objects.create(user=user,customer=customer,product=product,quantity=quantity,status='Accepted',
        amount_total=amount_total,payment_status=payment_status,payment_id=payment_id)
        orders.append(order)                  #Adds the newly created order to the orders list 
        request.session['buy_now'] = None
    else:
        cart_items = Cart.objects.filter(user=user)
        for item in cart_items:
            order = OrderPlaced.objects.create(user=user,customer=customer,product=item.product,quantity=item.quantity,status='Accepted',
            amount_total=amount_total,payment_status=payment_status,payment_id=payment_id)
            orders.append(order)
        cart_items.delete()

    return render(request, 'app/payment-success.html', {'orders': orders})    

@login_required(login_url='Login')
def buy_now(request):
    product_id = request.GET.get('product_id')
    quantity = request.GET.get('quantity', 1)
    try:
        quantity = int(quantity)
        if quantity < 1:
            quantity = 1
    except (ValueError, TypeError):
        quantity = 1
    if not product_id:
        return redirect('product-list')
    checkout_url = f"{reverse('checkout')}?product_id={product_id}&quantity={quantity}"
    return redirect(checkout_url)

@login_required
def checkout(request):
    user = request.user
    addresses = Customer.objects.filter(user=user)
    product_id = request.GET.get('product_id')
    quantity = int(request.GET.get('quantity', 1))
    cart_items = []
    is_buy_now = False

    if product_id:
        product = get_object_or_404(Product, id=product_id)
        total_cost = quantity * product.discounted_price
        cart_items = [{
            'product': product,
            'quantity': quantity,
            'total_cost': total_cost,
        }]
        amount = total_cost
        is_buy_now = True
    else:
        cart_qs = Cart.objects.filter(user=user)
        amount = 0
        for item in cart_qs:
            total_cost = item.quantity * item.product.discounted_price
            cart_items.append({
                'product': item.product,
                'quantity': item.quantity,
                'total_cost': total_cost,
            })
            amount += total_cost

    shipping_amount = 70.0
    totalamount = amount + shipping_amount

    context = {
        'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLISHABLE_KEY,
        'add': addresses,
        'totalamount': totalamount,
        'cart_items': cart_items,
        'is_buy_now': is_buy_now,
        'product_id': product_id,
        'quantity': quantity,
    }
    return render(request, 'app/checkout.html', context)


@login_required
def payment_failed(request):
    return render(request, 'app/payment-failed.html')

class ProductView(View):
    def get(self, request): 
        topwears = Product.objects.filter(category='TW')
        bottomwears = Product.objects.filter(category='BW')
        mobiles = Product.objects.filter(category='M')
        laptops = Product.objects.filter(category='L')
        return render(request, 'app/home.html', {'topwears': topwears, 'bottomwears': bottomwears, 'mobiles': mobiles, 'laptops':laptops})

class ProductDetailView(View):
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        colors = Color.objects.all()
        rams = RAM.objects.all()
        sizes = Size.objects.all()
        if request.user.is_authenticated:
            item_already_in_cart = Cart.objects.filter(Q(product=product.id) & Q(user=request.user)).exists()
        else:
            item_already_in_cart = False 
        return render(request,'app/productdetail.html',{'product': product, 'item_already_in_cart': item_already_in_cart, 'colors': colors, 'rams': rams, 'sizes': sizes})

@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    def get(self, request):
        profile = Customer.objects.filter(user=request.user).first()
        form = CustomerProfileForm(instance=profile)
        return render(request, 'app/profile.html', {'form': form, 'active': 'btn-primary'})

    def post(self, request):
        profile = Customer.objects.filter(user=request.user).first()
        form = CustomerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Congratulations! Profile updated successfully.')
            return redirect('profile')
        messages.error(request, 'Please correct the errors below.')
        return render(request, 'app/profile.html', {'form': form, 'active': 'btn-primary'})
    
class CustomerRegistrationView(View):
    def get(self, request):
        form = CustomerRegistrationForm()
        return render(request, 'app/customerregistration.html', {'form': form})

    def post(self, request):
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            messages.success(request, 'Congratulations!! Registered Successfully')
            form.save()
            return redirect('Login')
        return render(request, 'app/customerregistration.html', {'form': form})    

@login_required(login_url='Login')
def add_to_cart(request):
    product_id = request.POST.get('prod_id') or request.GET.get('prod_id')
    quantity = int(request.POST.get('quantity') or request.GET.get('quantity') or 1)
    
    if not product_id:
        return redirect('home')

    product = get_object_or_404(Product, id=product_id)
    cart_item, created = Cart.objects.get_or_create(
        user=request.user, 
        product=product,
        defaults={'quantity': quantity}
    )
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    return redirect('showcart') 
   

@login_required(login_url='Login')   
def show_cart(request):
    user = request.user
    carts = Cart.objects.filter(user=user)
    amount = 0.0 
    shipping_amount = 70.0
    totalamount = 0.0

    if carts.exists():
        for cart in carts:
            tempamount = cart.quantity * cart.product.discounted_price
            amount += tempamount
        totalamount = amount + shipping_amount
        return render(request, 'app/addtocart.html', {
            'carts': carts,
            'totalamount': totalamount,
            'amount': amount,
            'shipping_cost': shipping_amount
        })
    return render(request, 'app/emptycart.html') 

def plus_cart(request):
    if request.method == 'GET':
        prod_id = request.GET['prod_id']
        c = Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
        c.quantity+=1
        c.save()
        amount = 0.0
        shipping_amount = 70.0
        cart_product = [p for p in Cart.objects.all() if p.user == request.user]
        for p in cart_product:
            tempamount = (p.quantity * p.product.discounted_price)
            amount += tempamount

        data = {
            'quantity': c.quantity,
            'amount': amount,
            'totalamount':amount + shipping_amount
            }
        return JsonResponse(data)
    
def minus_cart(request):
    if request.method == 'GET':
        prod_id = request.GET['prod_id']
        c = Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
        c.quantity-=1
        c.save()
        amount = 0.0
        shipping_amount = 70.0
        cart_product = [p for p in Cart.objects.all() if p.user == request.user ]
        for p in cart_product:
            tempamount = (p.quantity * p.product.discounted_price)
            amount += tempamount

        data = {
            'quantity': c.quantity,
            'amount': amount,
            'totalamount':amount + shipping_amount
            }
        return JsonResponse(data) 

def remove_cart(request):
    if request.method == 'GET':
        prod_id = request.GET['prod_id']
        c = Cart.objects.get(Q(product_id=prod_id) & Q(user=request.user))
        c.delete()
        amount = 0.0
        shipping_amount = 70.0
        cart_product = Cart.objects.filter(user=request.user)
        for p in cart_product:
            tempamount = (p.quantity * p.product.discounted_price)
            amount += tempamount

        data = {
            'amount': amount,
            'totalamount': amount + shipping_amount
        }
        return JsonResponse(data)


@login_required(login_url='Login')
def address(request):
    add = Customer.objects.filter(user=request.user)
    return render(request, 'app/address.html', {
        'add': add,
        'active': 'btn-primary'
    })

@login_required(login_url='Login')
def add_address(request):
    if request.method == 'POST':
        form = CustomerAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, 'Address added successfully!')
            return redirect('address')
    else:
        form = CustomerAddressForm()
    return render(request, 'app/add_address.html', {
        'form': form,
        'active': 'btn-secondary'
    })

def delete_address(request, id):
    address = get_object_or_404(Customer, id=id, user=request.user)
    address.delete()
    messages.success(request, 'Address deleted successfully!')
    return redirect('address')

@login_required(login_url='Login')
def orders(request):
    op = OrderPlaced.objects.filter(user=request.user)
    return render(request, 'app/orders.html', {'order_placed':op})


def mobile(request):
    mobiles = Product.objects.filter(category='M')
    brand = request.GET.get('brand')
    color = request.GET.get('color')
    ram = request.GET.get('ram')
    price = request.GET.get('price')

    if brand and brand != 'Both':
        mobiles = mobiles.filter(brand=brand)
    elif brand == 'Both':
        mobiles = mobiles.filter(Q(brand='Samsung') | Q(brand='One Plus'))
    if color:
        mobiles = mobiles.filter(color__id=color)
    if ram:
        mobiles = mobiles.filter(ram__id=ram)
    if price == 'below5000':
        mobiles = mobiles.filter(discounted_price__lt=5000)
    elif price == '500to60000':
        mobiles = mobiles.filter(discounted_price__gte=500, discounted_price__lte=60000)
    elif price == 'above10000':
        mobiles = mobiles.filter(discounted_price__gt=10000)

    colors = Color.objects.all()
    rams = RAM.objects.all()
    context = {'mobiles': mobiles,'colors': colors,'rams': rams}
    return render(request, 'app/mobile.html', context)

def laptop(request):
    laptops = Product.objects.filter(category='L')
    brand = request.GET.get('brand')
    color = request.GET.get('color')
    ram = request.GET.get('ram')
    price = request.GET.get('price')

    if brand and brand != 'Both':
        laptops = laptops.filter(brand=brand)
    elif brand == 'Both':
        laptops = laptops.filter(Q(brand='Dell') | Q(brand='HP'))
    if color:
        laptops = laptops.filter(color__id=color)
    if ram:
        laptops = laptops.filter(ram__id=ram)
    if price == 'below50000':
        laptops = laptops.filter(discounted_price__lt=50000)
    elif price == '20000to80000':
        laptops = laptops.filter(discounted_price__gte=20000, discounted_price__lte=80000)
    elif price == 'above100000':
        laptops = laptops.filter(discounted_price__gt=100000)

    colors = Color.objects.all()
    rams = RAM.objects.all()
    context = {'laptops': laptops,'colors': colors,'rams': rams}
    return render(request, 'app/laptop.html', context)

def topwear(request):
    topwears = Product.objects.filter(category='TW')
    brand = request.GET.get('brand')
    color = request.GET.get('color')
    size = request.GET.get('size')
    price = request.GET.get('price')

    if brand and brand != 'Both':
        topwears = topwears.filter(brand=brand)
    elif brand == 'Both':
        topwears = topwears.filter(Q(brand='US Polo') | Q(brand='Roadster'))
    if color:
        topwears = topwears.filter(color__id=color)
    if size:
        topwears = topwears.filter(size__id=size)
    if price == 'below500':
        topwears = topwears.filter(discounted_price__lt=500)
    elif price == '500to5000':
        topwears = topwears.filter(discounted_price__gte=500, discounted_price__lte=5000)
    elif price == 'above1000':
        topwears = topwears.filter(discounted_price__gt=1000)

    colors = Color.objects.all()
    sizes = Size.objects.all()
    context = {'topwears': topwears,'colors': colors,'sizes': sizes}
    return render(request, 'app/topwear.html', context)


def bottomwear(request):
    bottomwears = Product.objects.filter(category='BW')
    brand = request.GET.get('brand')
    color = request.GET.get('color')
    size = request.GET.get('size')
    price = request.GET.get('price')

    if brand and brand != 'Both':
        bottomwears = bottomwears.filter(brand=brand)
    elif brand == 'Both':
        bottomwears = bottomwears.filter(Q(brand='Denim') | Q(brand='US Polo'))
    if color:
        bottomwears = bottomwears.filter(color__id=color)
    if size:
        bottomwears = bottomwears.filter(size__id=size)
    if price == 'below500':
        bottomwears = bottomwears.filter(discounted_price__lt=500)
    elif price == '500to5000':
        bottomwears = bottomwears.filter(discounted_price__gte=500, discounted_price__lte=5000)
    elif price == 'above1000':
        bottomwears = bottomwears.filter(discounted_price__gt=1000)

    colors = Color.objects.all()
    sizes = Size.objects.all()
    context = {'bottomwears': bottomwears,'colors': colors,'sizes': sizes}
    return render(request, 'app/bottomwear.html', context) 

def contact(request):
    if request.method=='POST':
        name= request.POST['name']
        email= request.POST['email']
        phone= request.POST['phone']
        content= request.POST['content']
        print(name, email, phone, content)
        contact= Contact(name=name, email=email, phone=phone, content=content)
        contact.save()
        return redirect("/contact/")
    return render(request, 'app/contact.html')

def logout_view(request):
    logout(request)
    return redirect('/') 

@login_required(login_url='Login')
def payment_done(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            custid = data.get('custid')
            user = request.user
            customer = get_object_or_404(Customer, id=custid, user=user)
            cart_items = Cart.objects.filter(user=user)
            if not cart_items.exists():
                return JsonResponse({'error': 'Cart is empty.'}, status=400)

            for c in cart_items:
                OrderPlaced.objects.create(
                    user=user,
                    customer=customer,
                    product=c.product,
                    quantity=c.quantity
                )
                c.delete()
            return JsonResponse({'message': 'Order placed successfully.'})
        except (json.JSONDecodeError, KeyError):
            return HttpResponseBadRequest('Invalid data')
    else:
        return HttpResponseBadRequest('Invalid request method')

def search(request):
    query = request.GET.get('query', '')
    products = []
    if query:
        products = Product.objects.filter(title__icontains=query) | Product.objects.filter(description__icontains=query)
        products = products.distinct()
    params = {'products': products, 'query': query}
    return render(request, 'app/search.html', params)


