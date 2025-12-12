import graphene
from graphene_django.types import DjangoObjectType
from django.db import transaction, IntegrityError
from django.core.validators import validate_email, RegexValidator
from django.core.exceptions import ValidationError
from graphene_django.filter import DjangoFilterConnectionField
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter
# --- 1. Graphene Object Types ---

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ('id', 'name', 'email', 'phone', 'created_at')

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'stock')

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ('id', 'customer', 'products', 'total_amount', 'order_date')

# --- 2. Custom Validators ---

# Custom phone validator using a basic regex for common formats
phone_validator = RegexValidator(
    regex=r'^\+?\d{1,3}[- ]?(\d{3}[- ]?\d{3}[- ]?\d{4}|\(\d{3}\)[- ]?\d{3}[- ]?\d{4}|\d{10,15})$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)

# --- 3. Mutations ---

# Input for single customer creation
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)

# 3a. CreateCustomer Mutation
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    @staticmethod
    def mutate(root, info, input=None):
        name = input.name
        email = input.email
        phone = input.phone

        try:
            # Basic validation
            validate_email(email)
            if phone:
                phone_validator(phone)

            # Check for unique email
            if Customer.objects.filter(email=email).exists():
                raise ValidationError("Email already exists.", code='duplicate')

            customer = Customer.objects.create(name=name, email=email, phone=phone)
            message = f"Customer '{name}' created successfully."
            return CreateCustomer(customer=customer, message=message)

        except ValidationError as e:
            # Handle Django's built-in validation errors
            # Custom message for integrity error (duplicate email)
            if 'duplicate' in e.code_list:
                error_message = f"Validation Error: Email '{email}' already exists."
            else:
                error_message = f"Validation Error: {e.message}"
            
            # Raise the error so Graphene handles the exception and returns a proper GraphQL error
            raise Exception(error_message)

# 3b. BulkCreateCustomers Mutation
class BulkCustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(BulkCustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @staticmethod
    def mutate(root, info, input=None):
        created_customers = []
        validation_errors = []
        customers_to_create = []
        emails_to_check = [c.email for c in input]

        # Pre-check all emails in a single query
        existing_emails = set(Customer.objects.filter(email__in=emails_to_check).values_list('email', flat=True))

        for customer_data in input:
            name = customer_data.name
            email = customer_data.email
            phone = customer_data.phone
            
            error_message = None

            try:
                # 1. Validate email format
                validate_email(email)
                
                # 2. Validate uniqueness
                if email in existing_emails:
                    error_message = f"Record for '{name}' failed: Email '{email}' already exists."
                
                # 3. Validate phone format
                if phone:
                    phone_validator(phone)
                
                # If no errors, add to the batch
                if not error_message:
                    customers_to_create.append(Customer(name=name, email=email, phone=phone))

            except ValidationError as e:
                # Catch format errors (email/phone)
                error_message = f"Record for '{name}' failed: {e.message}"
            
            if error_message:
                validation_errors.append(error_message)


        if customers_to_create:
            # Create all valid customers in a single transaction (partial success)
            try:
                with transaction.atomic():
                    # bulk_create is fast but doesn't call save() or signal pre_save/post_save
                    created_customers = Customer.objects.bulk_create(customers_to_create)
            except Exception as e:
                 # Catch database-level errors
                 validation_errors.append(f"Database error during bulk creation: {e}")


        return BulkCreateCustomers(customers=created_customers, errors=validation_errors)


# Input for product creation
class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int(required=False, default_value=0)

# 3c. CreateProduct Mutation
class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)

    @staticmethod
    def mutate(root, info, input=None):
        price = input.price
        stock = input.stock

        # Validate price (must be positive) and stock (must be non-negative)
        if price <= 0:
            raise Exception("Validation Error: Price must be a positive number.")
        if stock < 0:
            raise Exception("Validation Error: Stock cannot be negative.")

        product = Product.objects.create(
            name=input.name,
            price=price,
            stock=stock
        )
        return CreateProduct(product=product)

# Input for order creation
class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)

# 3d. CreateOrder Mutation
class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)

    @staticmethod
    @transaction.atomic # Ensure atomicity: entire operation succeeds or fails
    def mutate(root, info, input=None):
        customer_id = input.customer_id
        product_ids = input.product_ids

        if not product_ids:
            raise Exception("Validation Error: Order must contain at least one product.")

        # 1. Validate Customer
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise Exception(f"Validation Error: Customer with ID '{customer_id}' not found.")

        # 2. Validate Products
        products = Product.objects.filter(pk__in=product_ids)
        if products.count() != len(product_ids):
            # Find the invalid IDs for a helpful message
            valid_ids = set(p.id for p in products)
            invalid_ids = [pid for pid in product_ids if int(pid) not in valid_ids]
            raise Exception(f"Validation Error: Invalid product ID(s) found: {', '.join(map(str, invalid_ids))}")

        # 3. Create Order
        order = Order.objects.create(customer=customer)
        
        # 4. Associate Products
        order.products.set(products)

        # 5. Calculate and save total_amount
        total_amount = order.calculate_total()
        order.total_amount = total_amount
        order.save()

        return CreateOrder(order=order)


# --- 4. Root Schema Definitions ---

class Query(graphene.ObjectType):
    # Keep the initial 'hello' query
    hello = graphene.String()
    def resolve_hello(root, info):
        return "Hello, GraphQL!"

    # Add query fields for testing (optional but highly recommended)
    customer = graphene.Field(CustomerType, id=graphene.ID())
    all_customers = graphene.List(CustomerType)

    def resolve_customer(root, info, id):
        try:
            return Customer.objects.get(pk=id)
        except Customer.DoesNotExist:
            return None

    def resolve_all_customers(root, info):
        return Customer.objects.all()


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

class CustomerNode(DjangoObjectType):
    class Meta:
        model = Customer
        # Use the ID field as the unique identifier for Relay
        interfaces = (graphene.relay.Node,) 
        fields = ('id', 'name', 'email', 'phone', 'created_at')

class ProductNode(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (graphene.relay.Node,)
        fields = ('id', 'name', 'price', 'stock')

class OrderNode(DjangoObjectType):
    class Meta:
        model = Order
        interfaces = (graphene.relay.Node,)
        fields = ('id', 'customer', 'products', 'total_amount', 'order_date')

# --- 2. Root Query (Updated with DjangoFilterConnectionField) ---

class Query(graphene.ObjectType):
    # Keep the initial 'hello' query
    hello = graphene.String()
    def resolve_hello(root, info):
        return "Hello, GraphQL!"

    # Use DjangoFilterConnectionField for filtering, pagination, and sorting
    # all_customers
    all_customers = DjangoFilterConnectionField(
        CustomerNode,
        filterset_class=CustomerFilter,
        # Allow sorting by name, email, phone, created_at
        order_by=graphene.List(graphene.String) 
    )

    # all_products
    all_products = DjangoFilterConnectionField(
        ProductNode,
        filterset_class=ProductFilter,
        # Allow sorting by name, price, stock
        order_by=graphene.List(graphene.String)
    )

    # all_orders
    all_orders = DjangoFilterConnectionField(
        OrderNode,
        filterset_class=OrderFilter,
        # Allow sorting by total_amount, order_date
        order_by=graphene.List(graphene.String)
    )