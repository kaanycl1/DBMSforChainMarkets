from django.shortcuts import render
from django.http import JsonResponse
from myapp.utility.db_utility import execute_query,execute_sql_file
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db import connection
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny,IsAuthenticated,IsAdminUser
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from myapp.serializers import LoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import BasePermission
from django.contrib.auth import logout
from django.contrib.auth import login as django_login


class IsRegularUser(BasePermission):
    def has_permission(self, request, view):
        # Allow access to regular users who are not admin
        return request.user and not request.user.is_staff
    
class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        # Allow access only to admin users
        return request.user and request.user.is_staff

# Logout Endpoint
@swagger_auto_schema(
    method='POST',
    responses={
        200: openapi.Response(description="Logout successful"),
        400: openapi.Response(description="Error while logging out"),
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    if request.method == 'POST':
        # Logout the user
        try:
            logout(request)  # Django's logout method clears the session
            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='POST',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description="Username for the user"),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description="Password for the user"),
            'email': openapi.Schema(type=openapi.TYPE_STRING, description="Email address of the user")
        },
        required=['username', 'password', 'email']
    ),
    responses={
        201: openapi.Response(description="Registration successful"),
        400: openapi.Response(description="Validation error"),
        500: openapi.Response(description="Internal server error")
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    if request.method == 'POST':
        # Extract user data from the request
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        
        # Simple validation
        if not username or not password or not email:
            return Response({"error": "Username, password, and email are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email
            )
            return Response({"message": "Registration successful", "username": user.username}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# View for user login
@swagger_auto_schema(
    method='POST',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description="Username of the user"),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description="Password of the user")
        },
        required=['username', 'password']
    ),
    responses={
        200: openapi.Response(description="Login successful"),
        401: openapi.Response(description="Invalid credentials")
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    if request.method == 'POST':
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            django_login(request, user)

            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Login successful',
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
            }, status=status.HTTP_200_OK)
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

class CustomerListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch all customers using raw SQL
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM customer")
            customers = cursor.fetchall()

        # Convert query result to a list of dictionaries
        customers_list = [
            {"customer_id": row[0], "name": row[1], "total_spending": row[2]} for row in customers
        ]
        return Response(customers_list)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the customer'),
            },
            required=['name']
        ),
        responses={
            201: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
            400: "Validation error",
        },
    )
    def post(self, request):
        # Get data from request
        data = request.data
        name = data.get("name")

        # Validate input
        if not name:
            raise ValidationError("Name is required.")

        # Insert a new customer using raw SQL
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO customer (name, total_spending) VALUES (%s, 0)",
                [name],
            )
        return Response(
            {
                "message": "Customer created successfully",
                "name": name,
            },
            status=status.HTTP_201_CREATED,
        )


class CustomerDetailView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the customer'),
            },
            required=['name']
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
            400: "Validation error",
            404: "Customer not found",
        },
    )
    def put(self, request, customer_id):
        # Get data from request
        data = request.data
        name = data.get("name")

        # Validate input
        if not name:
            raise ValidationError("Name is required.")

        # Update customer data using raw SQL
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE customer SET name = %s WHERE customer_id = %s",
                [name, customer_id],
            )

        return Response(
            {
                "message": "Customer updated successfully",
                "name": name,
            }
        )

    def delete(self, request, customer_id):
        # Delete a customer using raw SQL
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM customer WHERE customer_id = %s", [customer_id])

        return Response(
            {"message": "Customer deleted successfully"}, status=status.HTTP_204_NO_CONTENT
        )


class EmployeeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch employees with profession and branch names using JOIN
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT e.employee_id, e.name, m.location AS branch_name, p.name AS profession_name, e.manager
                FROM employee e
                JOIN profession p ON e.profession = p.profession_id
                JOIN marketBranch m ON e.branch = m.market_id
            """)
            employees = cursor.fetchall()

        employees_list = [
            {
                "employee_id": row[0],
                "name": row[1],
                "branch_name": row[2],
                "profession_name": row[3],
                "manager": row[4],
            }
            for row in employees
        ]
        return Response(employees_list)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the employee'),
                'branch': openapi.Schema(type=openapi.TYPE_INTEGER, description='Branch ID (Market ID)'),
                'profession': openapi.Schema(type=openapi.TYPE_INTEGER, description='Profession ID'),
                'manager': openapi.Schema(type=openapi.TYPE_INTEGER, description='Manager ID (optional)'),
            },
            required=['name', 'branch', 'profession']
        ),
        responses={201: "Created", 400: "Validation Error"},
    )
    def post(self, request):
        data = request.data
        name = data.get("name")
        branch = data.get("branch")
        profession = data.get("profession")
        manager = data.get("manager")

        # Check if the branch exists in MarketBranch
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM marketBranch WHERE market_id = %s", [branch])
            if not cursor.fetchone():
                raise ValidationError("Invalid branch ID (Market ID).")

        # Check if the profession exists
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM profession WHERE profession_id = %s", [profession])
            if not cursor.fetchone():
                raise ValidationError("Invalid profession ID.")

        # Insert employee
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO employee (name, branch, profession, manager) VALUES (%s, %s, %s, %s)",
                [name, branch, profession, manager],
            )
        return Response({"message": "Employee created successfully"}, status=status.HTTP_201_CREATED)


class EmployeeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the employee'),
                'branch': openapi.Schema(type=openapi.TYPE_INTEGER, description='Branch ID (Market ID)'),
                'profession': openapi.Schema(type=openapi.TYPE_INTEGER, description='Profession ID'),
                'manager': openapi.Schema(type=openapi.TYPE_INTEGER, description='Manager ID'),
            },
            required=['name', 'branch', 'profession']
        ),
        responses={200: "Updated", 400: "Validation error", 404: "Employee not found"},
    )
    def put(self, request, employee_id):
        # Validate input
        data = request.data
        name = data.get("name")
        branch = data.get("branch")
        profession = data.get("profession")
        manager = data.get("manager")

        # Check if the employee exists
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM employee WHERE employee_id = %s", [employee_id])
            if not cursor.fetchone():
                return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if the branch exists
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM marketBranch WHERE market_id = %s", [branch])
            if not cursor.fetchone():
                raise ValidationError("Invalid branch ID (Market ID).")

        # Check if the profession exists
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM profession WHERE profession_id = %s", [profession])
            if not cursor.fetchone():
                raise ValidationError("Invalid profession ID.")

        # Check if the manager exists (optional)
        if manager:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM employee WHERE employee_id = %s", [manager])
                if not cursor.fetchone():
                    raise ValidationError("Invalid manager ID.")

        # Update employee
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE employee SET name = %s, branch = %s, profession = %s, manager = %s WHERE employee_id = %s",
                [name, branch, profession, manager, employee_id],
            )
        return Response({"message": "Employee updated successfully"}, status=status.HTTP_200_OK)

    def delete(self, request, employee_id):
        # Check if the employee exists before deleting
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM employee WHERE employee_id = %s", [employee_id])
            if not cursor.fetchone():
                return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

        # Delete the employee
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM employee WHERE employee_id = %s", [employee_id])

        return Response({"message": "Employee deleted successfully"}, status=status.HTTP_204_NO_CONTENT)




class ProfessionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch all professions using raw SQL
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM profession")
            professions = cursor.fetchall()

        # Convert query result to a list of dictionaries
        professions_list = [
            {"profession_id": row[0], "name": row[1], "salary": row[2]} for row in professions
        ]
        return Response(professions_list)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the profession'),
                'salary': openapi.Schema(type=openapi.TYPE_INTEGER, description='Salary of the profession'),
            },
            required=['name', 'salary']
        ),
        responses={
            201: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                    'salary': openapi.Schema(type=openapi.TYPE_INTEGER),
                },
            ),
            400: "Validation error",
        },
    )
    def post(self, request):
        # Get data from request
        data = request.data
        name = data.get("name")
        salary = data.get("salary")

        # Validate input
        if not name or salary is None:
            raise ValidationError("Both name and salary are required.")

        # Insert a new profession using raw SQL
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO profession (name, salary) VALUES (%s, %s)",
                [name, salary],
            )
        return Response(
            {
                "message": "Profession created successfully",
                "name": name,
                "salary": salary,
            },
            status=status.HTTP_201_CREATED,
        )


class ProfessionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the profession'),
                'salary': openapi.Schema(type=openapi.TYPE_INTEGER, description='Salary of the profession'),
            },
            required=['name', 'salary']
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                    'salary': openapi.Schema(type=openapi.TYPE_INTEGER),
                },
            ),
            400: "Validation error",
            404: "Profession not found",
        },
    )
    def put(self, request, profession_id):
        # Get data from request
        data = request.data
        name = data.get("name")
        salary = data.get("salary")

        # Validate input
        if not name or salary is None:
            raise ValidationError("Both name and salary are required.")

        # Update profession data using raw SQL
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE profession SET name = %s, salary = %s WHERE profession_id = %s",
                [name, salary, profession_id],
            )

        return Response(
            {
                "message": "Profession updated successfully",
                "name": name,
                "salary": salary,
            }
        )

    def delete(self, request, profession_id):
        # Delete a profession using raw SQL
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM profession WHERE profession_id = %s", [profession_id])

        return Response(
            {"message": "Profession deleted successfully"}, status=status.HTTP_204_NO_CONTENT
        )

class MarketBranchListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch all market branches
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM marketBranch")
            branches = cursor.fetchall()

        # Convert query result to a list of dictionaries
        branches_list = [
            {"market_id": row[0], "budget": row[1], "location": row[2]} for row in branches
        ]
        return Response(branches_list)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'budget': openapi.Schema(type=openapi.TYPE_INTEGER, description='Budget of the branch'),
                'location': openapi.Schema(type=openapi.TYPE_STRING, description='Location of the branch'),
            },
            required=['budget', 'location']
        ),
        responses={201: "Created", 400: "Validation Error"},
    )
    def post(self, request):
        data = request.data
        budget = data.get("budget")
        location = data.get("location")

        # Validate input
        if not budget or not location:
            raise ValidationError("Both budget and location are required.")

        # Insert a new market branch
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO marketBranch (budget, location) VALUES (%s, %s)",
                [budget, location],
            )
        return Response(
            {"message": "Market branch created successfully"},
            status=status.HTTP_201_CREATED
        )


class MarketBranchDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'budget': openapi.Schema(type=openapi.TYPE_INTEGER, description='Budget of the branch'),
                'location': openapi.Schema(type=openapi.TYPE_STRING, description='Location of the branch'),
            },
            required=['budget', 'location']
        ),
        responses={200: "Updated", 400: "Validation error", 404: "Market branch not found"},
    )
    def put(self, request, market_id):
        # Validate input
        data = request.data
        budget = data.get("budget")
        location = data.get("location")

        # Check if branch exists
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM marketBranch WHERE market_id = %s", [market_id])
            if not cursor.fetchone():
                return Response({"error": "Market branch not found"}, status=status.HTTP_404_NOT_FOUND)

        # Update branch data
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE marketBranch SET budget = %s, location = %s WHERE market_id = %s",
                [budget, location, market_id],
            )
        return Response(
            {"message": "Market branch updated successfully"},
            status=status.HTTP_200_OK
        )

    def delete(self, request, market_id):
        # Check if the branch exists before deleting
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM marketBranch WHERE market_id = %s", [market_id])
            if not cursor.fetchone():
                return Response({"error": "Market branch not found"}, status=status.HTTP_404_NOT_FOUND)

        # Delete the branch
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM marketBranch WHERE market_id = %s", [market_id])

        return Response(
            {"message": "Market branch deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )

class StockListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch all stock entries with JOIN to marketBranch and product
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT s.stock_id, s.product_id, p.name AS product_name, 
                       s.market_id, m.location AS market_location, 
                       s.expiry_date, s.amount
                FROM stock s
                JOIN marketBranch m ON s.market_id = m.market_id
                JOIN product p ON s.product_id = p.product_id
            """)
            stocks = cursor.fetchall()

        # Convert query result to a list of dictionaries
        stocks_list = [
            {
                "stock_id": row[0],
                "product_id": row[1],
                "product_name": row[2],
                "market_id": row[3],
                "market_location": row[4],
                "expiry_date": row[5],
                "amount": row[6],
            }
            for row in stocks
        ]
        return Response(stocks_list)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Product ID'),
                'market_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Market ID'),
                'expiry_date': openapi.Schema(type=openapi.TYPE_STRING, format='date', description='Expiry date (YYYY-MM-DD)'),
                'amount': openapi.Schema(type=openapi.TYPE_INTEGER, description='Stock amount'),
            },
            required=['product_id', 'market_id', 'expiry_date', 'amount']
        ),
        responses={201: "Created", 400: "Validation Error"},
    )
    def post(self, request):
        data = request.data
        product_id = data.get("product_id")
        market_id = data.get("market_id")
        expiry_date = data.get("expiry_date")
        amount = data.get("amount")

        # Validate product_id and market_id foreign keys
        with connection.cursor() as cursor:
            # Check if product exists
            cursor.execute("SELECT 1 FROM product WHERE product_id = %s", [product_id])
            if not cursor.fetchone():
                raise ValidationError("Invalid product ID.")

            # Check if market exists
            cursor.execute("SELECT 1 FROM marketBranch WHERE market_id = %s", [market_id])
            if not cursor.fetchone():
                raise ValidationError("Invalid market ID.")

        # Insert stock entry
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO stock (product_id, market_id, expiry_date, amount) 
                VALUES (%s, %s, %s, %s)
                """,
                [product_id, market_id, expiry_date, amount],
            )
        return Response({"message": "Stock entry created successfully"}, status=status.HTTP_201_CREATED)


class StockDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Product ID'),
                'market_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Market ID'),
                'expiry_date': openapi.Schema(type=openapi.TYPE_STRING, format='date', description='Expiry date (YYYY-MM-DD)'),
                'amount': openapi.Schema(type=openapi.TYPE_INTEGER, description='Stock amount'),
            },
            required=['product_id', 'market_id', 'expiry_date', 'amount']
        ),
        responses={200: "Updated", 400: "Validation error", 404: "Stock entry not found"},
    )
    def put(self, request, stock_id):
        data = request.data
        product_id = data.get("product_id")
        market_id = data.get("market_id")
        expiry_date = data.get("expiry_date")
        amount = data.get("amount")

        # Validate product_id and market_id
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM product WHERE product_id = %s", [product_id])
            if not cursor.fetchone():
                raise ValidationError("Invalid product ID.")

            cursor.execute("SELECT 1 FROM marketBranch WHERE market_id = %s", [market_id])
            if not cursor.fetchone():
                raise ValidationError("Invalid market ID.")

        # Update stock entry
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE stock SET product_id = %s, market_id = %s, expiry_date = %s, amount = %s
                WHERE stock_id = %s
                """,
                [product_id, market_id, expiry_date, amount, stock_id],
            )
        return Response({"message": "Stock entry updated successfully"}, status=status.HTTP_200_OK)

    def delete(self, request, stock_id):
        # Delete stock entry
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM stock WHERE stock_id = %s", [stock_id])

        return Response({"message": "Stock entry deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class ProductListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch products with category names using JOIN
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT p.product_id, p.name, p.category, c.parent_id, 
                       p.lower_stock_alert, p.shelf_life, p.price
                FROM product p
                JOIN category c ON p.category = c.category_id
            """)
            products = cursor.fetchall()

        products_list = [
            {
                "product_id": row[0],
                "name": row[1],
                "price": row[6],
                "category_id": row[2],
                "parent_id": row[3],
                "lower_stock_alert": row[4],
                "shelf_life": row[5],
            }
            for row in products
        ]
        return Response(products_list)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Product name'),
                'price': openapi.Schema(type=openapi.TYPE_INTEGER, description='Price'),
                'category': openapi.Schema(type=openapi.TYPE_INTEGER, description='Category ID'),
                'lower_stock_alert': openapi.Schema(type=openapi.TYPE_INTEGER, description='Stock alert level'),
                'shelf_life': openapi.Schema(type=openapi.TYPE_INTEGER, description='Shelf life in days'),
            },
            required=['name', 'category', 'price', 'shelf_life']
        ),
        responses={201: "Created", 400: "Validation Error"},
    )
    def post(self, request):
        data = request.data
        name = data.get("name")
        category = data.get("category")
        price = data.get("price")
        lower_stock_alert = data.get("lower_stock_alert", 0)  # Default value
        shelf_life = data.get("shelf_life")

        # Validate category ID
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM category WHERE category_id = %s", [category])
            if not cursor.fetchone():
                raise ValidationError("Invalid category ID.")

        # Insert product
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO product (name,  price, category, lower_stock_alert, shelf_life)
                VALUES (%s, %s, %s, %s, %s)
                """,
                [name, price, category, lower_stock_alert, shelf_life],
            )
        return Response({"message": "Product created successfully"}, status=status.HTTP_201_CREATED)


class ProductDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Product name'),
                'price': openapi.Schema(type=openapi.TYPE_INTEGER, description='Price'),
                'category': openapi.Schema(type=openapi.TYPE_INTEGER, description='Category ID'),
                'lower_stock_alert': openapi.Schema(type=openapi.TYPE_INTEGER, description='Stock alert level'),
                'shelf_life': openapi.Schema(type=openapi.TYPE_INTEGER, description='Shelf life in days'),
            },
            required=['name', 'category', 'shelf_life']
        ),
        responses={200: "Updated", 400: "Validation error", 404: "Product not found"},
    )
    def put(self, request, product_id):
        data = request.data
        name = data.get("name")
        price = data.get("price")
        category = data.get("category")
        lower_stock_alert = data.get("lower_stock_alert", 0)  # Default value
        shelf_life = data.get("shelf_life")

        # Validate category ID
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM category WHERE category_id = %s", [category])
            if not cursor.fetchone():
                raise ValidationError("Invalid category ID.")

        # Update product
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE product 
                SET name = %s, price = %s, category = %s, lower_stock_alert = %s, shelf_life = %s
                WHERE product_id = %s
                """,
                [name, price, category, lower_stock_alert, shelf_life, product_id],
            )
        return Response({"message": "Product updated successfully"}, status=status.HTTP_200_OK)

    def delete(self, request, product_id):
        # Delete product entry
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM product WHERE product_id = %s", [product_id])

        return Response({"message": "Product deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class CategoryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch all categories
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM category")
            categories = cursor.fetchall()

        categories_list = [
            {"category_id": row[0], "parent_id": row[1]} for row in categories
        ]
        return Response(categories_list)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'parent_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Parent category ID'),
            },
            required=[]
        ),
        responses={201: "Created", 400: "Validation Error"},
    )
    def post(self, request):
        data = request.data
        parent_id = data.get("parent_id")

        # Insert new category
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO category (parent_id) VALUES (%s)",
                [parent_id],
            )
        return Response({"message": "Category created successfully"}, status=status.HTTP_201_CREATED)


class CategoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'parent_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Parent category ID'),
            },
            required=[]
        ),
        responses={
            200: "Updated Successfully",
            400: "Validation Error",
            404: "Category not found",
        },
    )
    def put(self, request, category_id):
        data = request.data
        parent_id = data.get("parent_id")

        # Validate input
        if parent_id:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM category WHERE category_id = %s", [parent_id])
                if not cursor.fetchone():
                    raise ValidationError("Invalid parent_id.")

        # Update category
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE category SET parent_id = %s WHERE category_id = %s",
                [parent_id, category_id],
            )

        return Response({"message": "Category updated successfully"}, status=status.HTTP_200_OK)

    def delete(self, request, category_id):
        # Delete category
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM category WHERE category_id = %s", [category_id])

        return Response({"message": "Category deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class PromotionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch all promotions with category names using JOIN
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT p.promotion_id, c.category_id, p.percentage, p.start_date, p.end_date
                FROM promotion p
                JOIN category c ON p.category_id = c.category_id
            """)
            promotions = cursor.fetchall()

        promotions_list = [
            {"promotion_id": row[0], "category_id": row[1], "percentage": row[2],
             "start_date": row[3], "end_date": row[4]} for row in promotions
        ]
        return Response(promotions_list)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'category_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Category ID'),
                'percentage': openapi.Schema(type=openapi.TYPE_INTEGER, description='Discount percentage'),
                'start_date': openapi.Schema(type=openapi.FORMAT_DATE, description='Promotion start date'),
                'end_date': openapi.Schema(type=openapi.FORMAT_DATE, description='Promotion end date'),
            },
            required=['category_id', 'percentage', 'start_date']
        ),
        responses={201: "Created", 400: "Validation Error"},
    )
    def post(self, request):
        data = request.data
        category_id = data.get("category_id")
        percentage = data.get("percentage", 0)
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        # Validate category_id
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM category WHERE category_id = %s", [category_id])
            if not cursor.fetchone():
                raise ValidationError("Invalid category ID.")

        # Insert promotion
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO promotion (category_id, percentage, start_date, end_date) VALUES (%s, %s, %s, %s)",
                [category_id, percentage, start_date, end_date],
            )
        return Response({"message": "Promotion created successfully"}, status=status.HTTP_201_CREATED)


class PromotionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'category_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Category ID'),
                'percentage': openapi.Schema(type=openapi.TYPE_INTEGER, description='Discount percentage'),
                'start_date': openapi.Schema(type=openapi.FORMAT_DATE, description='Promotion start date'),
                'end_date': openapi.Schema(type=openapi.FORMAT_DATE, description='Promotion end date'),
            },
            required=['category_id', 'percentage', 'start_date']
        ),
        responses={200: "Updated", 400: "Validation Error", 404: "Not Found"},
    )
    def put(self, request, promotion_id):
        data = request.data
        category_id = data.get("category_id")
        percentage = data.get("percentage", 0)
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        # Validate category_id
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM category WHERE category_id = %s", [category_id])
            if not cursor.fetchone():
                raise ValidationError("Invalid category ID.")

        # Update promotion
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE promotion SET category_id = %s, percentage = %s, start_date = %s, end_date = %s WHERE promotion_id = %s",
                [category_id, percentage, start_date, end_date, promotion_id],
            )
        return Response({"message": "Promotion updated successfully"}, status=status.HTTP_200_OK)

    def delete(self, request, promotion_id):
        # Delete promotion
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM promotion WHERE promotion_id = %s", [promotion_id])

        return Response({"message": "Promotion deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class TransactionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch transactions with product and customer details using JOIN
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT t.transaction_id, c.name AS customer_name, p.name AS product_name, 
                       t.order_date, t.amount
                FROM transaction t
                JOIN customer c ON t.customer_id = c.customer_id
                JOIN product p ON t.product_id = p.product_id
            """)
            transactions = cursor.fetchall()

        transactions_list = [
            {"transaction_id": row[0], "customer_name": row[1], "product_name": row[2],
             "order_date": row[3], "amount": row[4]} for row in transactions
        ]
        return Response(transactions_list)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'customer_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Customer ID'),
                'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Product ID'),
                'branch_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Branch ID'),
                'order_date': openapi.Schema(type=openapi.FORMAT_DATE, description='Order Date'),
                'amount': openapi.Schema(type=openapi.TYPE_INTEGER, description='Quantity'),
            },
            required=['customer_id', 'product_id', 'branch_id']
        ),
        responses={201: "Created", 400: "Validation Error"},
    )
    def post(self, request):
        data = request.data
        customer_id = data.get("customer_id")
        product_id = data.get("product_id")
        branch_id = data.get("branch_id")
        order_date = data.get("order_date")
        amount = data.get("amount", 1)

        # Validate Customer ID
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM customer WHERE customer_id = %s", [customer_id])
            if not cursor.fetchone():
                raise ValidationError("Invalid customer ID.")

        # Validate Product ID
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM product WHERE product_id = %s", [product_id])
            if not cursor.fetchone():
                raise ValidationError("Invalid product ID.")

        # Validate Branch ID
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM marketbranch WHERE market_id = %s", [branch_id])
            if not cursor.fetchone():
                raise ValidationError("Invalid branch ID.")

        # Insert transaction
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO transaction (customer_id, product_id, branch_id, order_date, amount) VALUES (%s, %s, %s, %s, %s)",
                [customer_id, product_id, branch_id, order_date, amount],
            )

        # Update stock
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE stock SET amount = amount - %s WHERE product_id = %s AND market_id = %s;",
                [amount, product_id, branch_id],
            )

        return Response({"message": "Transaction created successfully"}, status=status.HTTP_201_CREATED)


class TransactionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'customer_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Customer ID'),
                'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Product ID'),
                'branch_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Branch ID'),
                'order_date': openapi.Schema(type=openapi.FORMAT_DATE, description='Order Date'),
                'amount': openapi.Schema(type=openapi.TYPE_INTEGER, description='Quantity'),
            },
            required=['customer_id', 'product_id', 'branch_id']
        ),
        responses={200: "Updated", 400: "Validation Error", 404: "Not Found"},
    )
    def put(self, request, transaction_id):
        data = request.data
        customer_id = data.get("customer_id")
        product_id = data.get("product_id")
        branch_id = data.get("branch_id")
        order_date = data.get("order_date")
        amount = data.get("amount", 1)

        # Validate Customer ID
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM customer WHERE customer_id = %s", [customer_id])
            if not cursor.fetchone():
                raise ValidationError("Invalid customer ID.")

        # Validate Product ID
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM product WHERE product_id = %s", [product_id])
            if not cursor.fetchone():
                raise ValidationError("Invalid product ID.")

        # Validate Branch ID
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM marketbranch WHERE market_id = %s", [branch_id])
            if not cursor.fetchone():
                raise ValidationError("Invalid branch ID.")

        # Update transaction
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE transaction SET customer_id = %s, product_id = %s, branch_id = %s, order_date = %s, amount = %s WHERE transaction_id = %s",
                [customer_id, product_id, branch_id, order_date, amount, transaction_id],
            )
        return Response({"message": "Transaction updated successfully"}, status=status.HTTP_200_OK)


    def delete(self, request, transaction_id):
        # Delete transaction
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM transaction WHERE transaction_id = %s", [transaction_id])

        return Response({"message": "Transaction deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

def create_tables(request):
    file_path = os.path.join('myapp', 'sql', 'create_tables.sql')
    execute_sql_file(file_path)
    return JsonResponse({"message": "8 Created tables successfully"}, status=200)

class GetCustomerTransactions(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, customer_id):

        # Validate the input
        if not customer_id:
            raise ValidationError("customer_id is required.")

        # Fetch transactions with product information for the given customer
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    t.transaction_id,
                    t.customer_id,
                    t.product_id,
                    p.name AS product_name,
                    p.category,
                    p.lower_stock_alert,
                    p.shelf_life,
                    p.price,
                    t.order_date,
                    t.amount
                FROM 
                    transaction t
                INNER JOIN 
                    product p 
                ON 
                    t.product_id = p.product_id
                WHERE 
                    t.customer_id = %s
                """,
                [customer_id],
            )
            transactions = cursor.fetchall()

        # If no transactions are found, return 404
        if not transactions:
            return Response(
                {"message": "No transactions found for the specified customer."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Convert query result to a list of dictionaries
        transactions_list = [
            {
                "transaction_id": row[0],
                "customer_id": row[1],
                "product_id": row[2],
                "product_name": row[3],
                "category": row[4],
                "lower_stock_alert": row[5],
                "shelf_life": row[6],
                "price": row[7],
                "order_date": row[8],
                "amount": row[9],
            }
            for row in transactions
        ]

        return Response(transactions_list, status=status.HTTP_200_OK)

class GetEmployeesInBranch(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, market_id):
        # Validate the input
        if not market_id:
            raise ValidationError("market_id is required.")

        # SQL query to fetch employees working in the specific market branch along with their managers
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    e.employee_id,
                    e.name AS employee_name,
                    p.name AS profession_name,
                    p.salary,
                    mb.location AS market_location,
                    m.name AS manager_name
                FROM employee e
                LEFT JOIN employee m ON e.manager = m.employee_id
                JOIN marketbranch mb ON e.branch = mb.market_id
                JOIN profession p ON e.profession = p.profession_id
                WHERE e.branch = %s
            """, [market_id])

            employees = cursor.fetchall()

        # If no employees are found, return 404
        if not employees:
            return Response(
                {"message": "No employees found for the specified market branch."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Convert query result to a list of dictionaries
        employee_list = [
            {
                "employee_id": row[0],
                "employee_name": row[1],
                "profession_name": row[2],
                "salary": row[3],
                "market_location": row[4],
                "manager_name": row[5],                
            }
            for row in employees
        ]

        return Response(employee_list, status=status.HTTP_200_OK)
    
class CustomerTransactionDateRangeView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('start_date', openapi.IN_QUERY, 
                              description="Start date of the transaction range (YYYY-MM-DD)", 
                              type=openapi.TYPE_STRING),
            openapi.Parameter('end_date', openapi.IN_QUERY, 
                              description="End date of the transaction range (YYYY-MM-DD)", 
                              type=openapi.TYPE_STRING)
        ]
    )
    def get(self, request):
        # Get start_date and end_date from query parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Validate that both start_date and end_date are provided
        if not start_date or not end_date:
            return Response(
                {"message": "Both start_date and end_date are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # SQL query to fetch customers who made transactions in the given date range
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT c.customer_id, c.name
                FROM customer c
                WHERE c.customer_id IN (
                    SELECT DISTINCT t.customer_id
                    FROM transaction t
                    WHERE t.order_date BETWEEN %s AND %s
                )
            """, [start_date, end_date])

            customers = cursor.fetchall()

        # If no customers are found, return 404
        if not customers:
            return Response(
                {"message": "No customers found for the specified date range."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Convert query result to a list of dictionaries
        customer_list = [
            {"customer_id": row[0], "name": row[1]} for row in customers
        ]

        return Response(customer_list)
    
class LowStockProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, market_id):
        # Validate the market_id parameter
        if not market_id:
            return Response(
                {"error": "market_id parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # SQL query to fetch products with low stock
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT p.product_id, p.name, s.amount AS stock_amount, p.lower_stock_alert
                FROM product p
                JOIN stock s ON p.product_id = s.product_id
                WHERE s.market_id = %s AND s.amount <= p.lower_stock_alert
            """, [market_id])

            # Fetch the results
            products = cursor.fetchall()

        # If no products are found, return 404
        if not products:
            return Response(
                {"message": "No low-stock products found for the specified market branch."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Convert the query results to a list of dictionaries
        product_list = [
            {
                "product_id": row[0],
                "name": row[1],
                "stock_amount": row[2],
                "lower_stock_alert": row[3]
            }
            for row in products
        ]

        return Response(product_list, status=status.HTTP_200_OK)
    
class ProductsWithPromotionsView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'category_id', openapi.IN_QUERY, description="Category ID to check promotions", 
                type=openapi.TYPE_INTEGER, required=True
            ),
            openapi.Parameter(
                'date', openapi.IN_QUERY, description="Date to check promotions (YYYY-MM-DD)", 
                type=openapi.TYPE_STRING, required=True
            )
        ],
        responses={200: "Success", 400: "Validation Error", 404: "No promotions found"}
    )
    def get(self, request):
        # Get the category_id from query parameters
        category_id = request.GET.get("category_id")
        if not category_id:
            return Response(
                {"error": "category_id parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate the category_id as an integer
        try:
            category_id = int(category_id)
        except ValueError:
            return Response(
                {"error": "category_id must be an integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the date from query parameters
        date = request.GET.get("date")
        if not date:
            return Response(
                {"error": "date parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # SQL query to fetch products with active promotions and calculate the discounted price
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    p.product_id, 
                    p.name, 
                    p.price, 
                    pr.percentage, 
                    pr.start_date, 
                    pr.end_date, 
                    (p.price - (p.price * pr.percentage / 100)) AS discounted_price
                FROM product p
                JOIN promotion pr ON p.category = pr.category_id
                WHERE p.category = %s AND %s BETWEEN pr.start_date AND pr.end_date
            """, [category_id, date])

            # Fetch the results
            products = cursor.fetchall()

        # If no products are found, return 404
        if not products:
            return Response(
                {"message": "No active promotions found for the specified category on the given date."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Convert the query results to a list of dictionaries
        product_list = [
            {
                "product_id": row[0],
                "name": row[1],
                "price": row[2],
                "percentage": row[3],
                "discounted_price": row[6],
                "start_date": row[4],
                "end_date": row[5],
            }
            for row in products
        ]

        return Response(product_list, status=status.HTTP_200_OK)



    
class BranchTotalSalaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Query to calculate total salary for each branch
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT e.branch, SUM(p.salary) AS total_salary
                FROM employee e
                JOIN profession p ON e.profession = p.profession_id
                GROUP BY e.branch ORDER BY SUM(p.salary) DESC;
            """)
            branch_salaries = cursor.fetchall()

        # Format the results
        salary_by_branch = []
        for branch_salary in branch_salaries:
            salary_by_branch.append({
                "branch_id": branch_salary[0],
                "total_salary": branch_salary[1],
            })

        return Response({"salary_by_branch": salary_by_branch})
    
class TopBudgetBranchesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, n):
        
        # Validate 'x'
        if not n or int(n) <= 0:
            raise ValidationError("The 'x' parameter must be a positive integer.")
        
        n = int(n)

        # Query to get branches with top 'x' budgets
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT market_id, location, budget
                FROM marketbranch
                ORDER BY budget DESC
                LIMIT %s;
            """, [n])
            branches = cursor.fetchall()

        # Convert query result to a list of dictionaries
        branches_list = [
            {"market_id": row[0], "location": row[1], "budget": row[2]} for row in branches
        ]

        return Response({"branches": branches_list})

class CategoryProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, category_id):
        # Query to recursively fetch category IDs
        with connection.cursor() as cursor:
            cursor.execute("""
                WITH RECURSIVE category_hierarchy AS (
                    -- Base case: Start with the given parent category
                    SELECT category_id, parent_id
                    FROM category
                    WHERE parent_id = %s OR category_id = %s

                    UNION ALL

                    -- Recursive case: Add child categories of the current category
                    SELECT c.category_id, c.parent_id
                    FROM category c
                    INNER JOIN category_hierarchy ch ON c.parent_id = ch.category_id
                    WHERE c.category_id != c.parent_id  -- Prevent recursion when parent_id equals category_id
                )
                SELECT p.product_id, p.name, p.price, p.category AS category_id
                FROM product p
                WHERE p.category IN (
                    SELECT category_id FROM category_hierarchy
                );
            """, [category_id,category_id])
            products = cursor.fetchall()

        # Format the results
        product_list = []
        for product in products:
            product_list.append({
                "product_id": product[0],
                "name": product[1],
                "price": product[2],
                "category_id": product[3],
            })

        # Return the results as a response
        return Response({"products": product_list})
    
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import connection

class UpdateTotalSpendingView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        # Update the total spending for each customer based on their transactions and discounts
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE customer c
                JOIN (
                    SELECT
                        t.customer_id,
                        SUM(
                            (p.price - (p.price * COALESCE(pr.percentage, 0) / 100)) * t.amount
                        ) AS total_spending
                    FROM
                        transaction t
                    JOIN product p ON t.product_id = p.product_id
                    LEFT JOIN promotion pr ON p.category = pr.category_id
                        AND t.order_date BETWEEN pr.start_date AND pr.end_date
                    GROUP BY
                        t.customer_id
                ) AS discounted_spending ON c.customer_id = discounted_spending.customer_id
                SET c.total_spending = discounted_spending.total_spending;
            """)

        return Response({"message": "Total spending updated for all customers"})