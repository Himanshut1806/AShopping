from django.db import models
from django.contrib.auth.models import User
# from django.core.validators import MaxValueValidator, MinValueValidator

STATE_CHOICES = (
('Andaman and Nicobar Islands','Andaman and Nicobar Islands'),
('Andhra Pradesh','Andhra Pradesh'),
('Arunachal Pradesh','Arunachal Pradesh'),
('Assam','Assam'),
('Bihar','Bihar'),
('Chandigarh','Chandigarh'),
('Chhattisgarh','Chhattisgarh'),
('Dadra and Nagar Haveli','Dadra and Nagar Haveli'),
('Daman and Diu','Daman and Diu'),
('Delhi','Delhi'),
('Goa','Goa'),
('Gujrat','Gujarat'),
('Haryana','Haryana'),
('Himachal Pradesh','Himachal Pradesh'),
('Jammu and Kashmir','Jammu and Kashmir'),
('Jharkhand','Jharkhand'),
('Karnataka','Karnataka'),
('Kerala','Kerala'),
('Lakshadweep','Lakshadweep'),
('Madhya Pradesh','Madhya Pradesh'),
('Meghalaya','Meghalaya'),
('Maharashtra','Maharashtra'),
('Manipur','Manipur'),
('Mizoram','Mizoram'),
('Nagaland','Nagaland'),
('Odisha','Odisha'),
('Puducherry','Puducherry'),
('Punjab','Punjab'),
('Rajasthan','Rajasthan'),
('Sikkim','Sikkim'),
('Tamil Nadu','Tamil Nadu'),
('Tripura','Tripura'), 
('Telangana','Telangana'),
('Uttar Pradesh','Uttar Pradesh'),
('Uttarakhand','Uttarakhand'),
('West Bengal','West Bengal'),
)


class Customer(models.Model):
    user = models.ForeignKey(User, on_delete= models.CASCADE)
    name = models.CharField(max_length=200)
    locality = models.CharField(max_length=200)
    city = models.CharField(max_length=50)
    zipcode = models.IntegerField()
    state = models.CharField(choices=STATE_CHOICES, max_length=50)

    def __str__(self):
        return str(self.id)
    
CATEGORY_CHOICES = (
    ('M','Mobile'),
    ('L','Laptop'),
    ('TW','TopWear'),
    ('BW','BottomWear'),
)

class RAM(models.Model):
    size = models.CharField(max_length=50)

    def __str__(self):
        return self.size

class Color(models.Model):
    name=models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Size(models.Model):
    size=models.CharField(max_length=50)

    def __str__(self):
        return self.size  


class Product(models.Model):
    title = models.CharField(max_length=100)
    selling_price = models.FloatField()
    discounted_price = models.FloatField()
    description = models.TextField()
    brand = models.CharField(max_length=100)
    category = models.CharField(choices = CATEGORY_CHOICES, max_length=2)
    product_image = models.ImageField(upload_to='productimg')
    ram = models.ForeignKey(RAM, on_delete=models.CASCADE, blank=True, null=True)
    color = models.ForeignKey(Color, on_delete=models.CASCADE, blank=True, null=True)
    size = models.ForeignKey(Size, on_delete=models.CASCADE, blank=True, null=True)


    def __str__(self):
        return self.title
    
class Cart(models.Model): 
    user = models.ForeignKey(User, on_delete=models.CASCADE)    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)    
    quantity = models.PositiveIntegerField(default=1)
      
    def __str__(self):
        return f"{self.user.username} - {self.product.title} ({self.quantity})"

    @property
    def total_cost(self):
        return self.quantity * self.product.discounted_price    

STATUS_CHOICES = (
    ('Accepted','Accepted'),
    ('Packed','Packed'),
    ('On The Way','On The Way'),
    ('Delivered','Delivered'),
    ('Cancel','Cancel'),
)    

class OrderPlaced(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    ordered_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    amount_total = models.IntegerField(null=True, blank=True)
    payment_status = models.CharField(max_length=50, null=True, blank=True)
    payment_id = models.CharField(max_length=100, null=True, blank=True)

    @property
    def total_cost(self):
        return self.quantity * self.product.discounted_price
 
class Contact(models.Model):
    sno= models.AutoField(primary_key=True) 
    name= models.CharField(max_length=255) 
    phone= models.CharField(max_length=13) 
    email= models.CharField(max_length=100) 
    content= models.TextField() 
    timeStamp= models.DateTimeField(auto_now_add=True, blank=True)

    def __str__(self):
        return 'Message from ' + self.name + ' - ' + self.email
    