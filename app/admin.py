from django.contrib import admin
from .models import Contact, Color, RAM, Size
from .models import Customer,Product,Cart,OrderPlaced


admin.site.register(Contact)
admin.site.register(Color)
admin.site.register(RAM)
admin.site.register(Size)

@admin.register(Customer)
class CustomerModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'name', 'locality', 'city', 'zipcode', 'state']


@admin.register(Product)  
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'selling_price', 
    'discounted_price', 'description', 'brand', 'category', 'product_image','color', 'ram', 'size',]

@admin.register(Cart)
class CartModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'product', 'quantity'] 

@admin.register(OrderPlaced)
class OrderPlacedModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'customer', 'product',
    'quantity', 'ordered_date', 'status', 'amount_total', 'payment_status', 'payment_id' ]   
 
          
