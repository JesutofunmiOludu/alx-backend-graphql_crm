from django.db import models
from django.core.validators import MinValueValidator

# Create your models here.

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0.01)] # Price must be positive
    )
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)]) # Stock must be non-negative

    def __str__(self):
        return self.name

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, related_name='orders')
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Order {self.id} by {self.customer.name}"

    def calculate_total(self):
        """Calculates the total amount based on associated products."""
        total = self.products.aggregate(models.Sum('price'))['price__sum']
        return total if total is not None else 0.00