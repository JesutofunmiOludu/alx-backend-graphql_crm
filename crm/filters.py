import django_filters
from django_filters import rest_framework as filters
from .models import Customer, Product, Order

class PhonePatternFilter(django_filters.FilterSet):
    """Custom filter to check if the phone number starts with a specific pattern."""
    def filter(self, queryset, name, value):
        if not value:
            return queryset
        # Filters where the phone field starts with the provided value (case-sensitive)
        return queryset.filter(phone__startswith=value)

class CustomerFilter(django_filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')
    email = filters.CharFilter(lookup_expr='icontains')
    created_at = filters.DateFromToRangeFilter() # Includes __gte and __lte lookups
    
    # Challenge: Custom phone pattern filter
    phone_pattern = PhonePatternFilter(field_name='phone')

    class Meta:
        model = Customer
        fields = ['name', 'email', 'created_at', 'phone'] # 'phone' is included for standard lookups if needed


# --- ProductFilter ---

class ProductFilter(django_filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')
    price = filters.RangeFilter() # Includes price__gte and price__lte lookups
    stock = filters.RangeFilter() # Includes stock__gte and stock__lte lookups

    # Challenge: Filter for low stock (e.g., stock < 10)
    low_stock = filters.NumberFilter(field_name='stock', lookup_expr='lt') # lookup_expr='lt' means less than

    class Meta:
        model = Product
        fields = ['name', 'price', 'stock']


# --- OrderFilter ---

class OrderFilter(django_filters.FilterSet):
    total_amount = filters.RangeFilter()
    order_date = filters.DateFromToRangeFilter()
    
    # Filter orders by related Customer's name (customer__name__icontains)
    customer_name = filters.CharFilter(field_name='customer__name', lookup_expr='icontains')
    
    # Filter orders by related Product's name (products__name__icontains)
    product_name = filters.CharFilter(field_name='products__name', lookup_expr='icontains')
    
    # Challenge: Filter orders that include a specific product ID (products__id__exact)
    product_id = filters.CharFilter(field_name='products__id', lookup_expr='exact')

    class Meta:
        model = Order
        fields = ['total_amount', 'order_date', 'customer_name', 'product_name', 'product_id']