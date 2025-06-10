from django.urls import path
from app import views
from .views import logout_view
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .forms import *

urlpatterns = [
    path('', views.ProductView.as_view(), name="home"),
    path('product-detail/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('add-to-cart/', views.add_to_cart, name='add-to-cart'),
    path('cart/', views.show_cart, name='showcart'),
    path('pluscart/', views.plus_cart, name='pluscart'),
    path('minuscart/', views.minus_cart, name='minuscart'),
    path('removecart/', views.remove_cart, name='removecart'),
    path('buy/<int:product_id>/', views.buy_now, name='buy-now'), 
    path('checkout/', views.checkout, name='checkout'),
    path('contact/', views.contact, name='contact'), 
    path('address/', views.address, name='address'),     
    path('address/delete/<int:id>/', views.delete_address, name='delete-address'),
    path('add-address/', views.add_address, name='add-address'),
    path('orders/', views.orders, name='orders'),
    path('logout/', logout_view, name='logout'),
    path('mobile/', views.mobile, name='mobile'),
    path('search/', views.search, name='search'),
    path('laptop/', views.laptop, name='laptop'),
    path('topwear/', views.topwear, name='topwear'),
    path('bottomwear/', views.bottomwear, name='bottomwear'),
    path('create-checkout-session/', views.create_checkout_session, name='create-checkout-session'),
    path('payment-success/', views.payment_successful, name='payment-success'),
    path('payment-failed/', views.payment_failed, name='payment-failed'),
    path('paymentdone/', views.payment_done, name='paymentdone'),
    path('mobile/<slug:data>', views.mobile, name='mobiledata'),
    path('laptop/<slug:data>', views.laptop, name='laptopdata'),
    path('topwear/<slug:data>', views.topwear, name='topweardata'),
    path('bottomwear/<slug:data>', views.bottomwear, name='bottomweardata'),
    path('registration/', views.CustomerRegistrationView.as_view(), name="customerregistration"),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='app/login.html', authentication_form = LoginForm), name= 'Login'),
    path('passwordchange/',auth_views.PasswordChangeView.as_view(template_name='app/passwordchange.html',form_class=MyPasswordChangeForm, success_url='/passwordchangedone/'), name='passwordchange'),
    path('passwordchangedone/',auth_views.PasswordChangeDoneView.as_view(template_name='app/passwordchangedone.html'),name='passwordchangedone'), 
    path('password-reset/',auth_views.PasswordResetView.as_view(template_name= 'app/password_reset.html', form_class= MyPasswordResetForm), name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name= 'app/password_reset_confirm.html', form_class= MySetPasswordForm), name='password_reset_confirm'),
    path('password-reset-complete/',auth_views.PasswordResetCompleteView.as_view(template_name= 'app/password_reset_complete.html'), name='password_reset_complete'),
    path('password-reset/done/',auth_views.PasswordResetDoneView.as_view(template_name= 'app/password_reset_done.html'), name='password_reset_done'),
]+ static(settings.MEDIA_URL, document_root= settings.MEDIA_ROOT)
