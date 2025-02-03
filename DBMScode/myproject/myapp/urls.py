from django.urls import path
from myapp import views
from myapp.views import CustomerListView, CustomerDetailView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
# Customer Endpoints
    path('customers/', views.CustomerListView.as_view(), name='customer-list'),
    path('customers/<int:customer_id>/', views.CustomerDetailView.as_view(), name='customer-detail'),

    # Employee Endpoints
    path('employees/', views.EmployeeListView.as_view(), name='employee-list'),
    path('employees/<int:employee_id>/', views.EmployeeDetailView.as_view(), name='employee-detail'),

    path('professions/', views.ProfessionListView.as_view(), name='profession-list'),
    path('professions/<int:profession_id>/', views.ProfessionDetailView.as_view(), name='profession-detail'),

    path('marketbranches/', views.MarketBranchListView.as_view(), name='marketbranch-list'),
    path('marketbranches/<int:market_id>/', views.MarketBranchDetailView.as_view(), name='marketbranch-detail'),

    path('stocks/', views.StockListView.as_view(), name='stock-list'),
    path('stocks/<int:stock_id>/', views.StockDetailView.as_view(), name='stock-detail'),

    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/<int:product_id>/', views.ProductDetailView.as_view(), name='product-detail'),

    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<int:category_id>/', views.CategoryDetailView.as_view(), name='category-detail'),

    path('promotions/', views.PromotionListView.as_view(), name='promotion-list'),
    path('promotions/<int:promotion_id>/', views.PromotionDetailView.as_view(), name='promotion-detail'),

    path('transactions/', views.TransactionListView.as_view(), name='transaction-list'),
    path('transactions/<int:transaction_id>/', views.TransactionDetailView.as_view(), name='transaction-detail'),

    path('_queries/customer_transactions/<int:customer_id>/', views.GetCustomerTransactions.as_view(), name='get_customer_t'),
    path('_queries/employees_in_branch/<int:market_id>/', views.GetEmployeesInBranch.as_view(), name='get_employee_b'),
    path('_queries/customers-purchased-between-dates', views.CustomerTransactionDateRangeView.as_view(), name='customer-transaction-date-range'),
    path('_queries/low-stock-products/<int:market_id>/', views.LowStockProductsView.as_view(), name='low-stocks-in-branch'),
    path('_queries/products-with-promotions', views.ProductsWithPromotionsView.as_view(), name='products_with_promotions'),
    path('_queries/total-salaries', views.BranchTotalSalaryView.as_view(), name='branch-total-salary'),
    path('_queries/top-budget/<int:n>/', views.TopBudgetBranchesView.as_view(), name='top-budget-branches'),
    path('_queries/products-under-category/<int:category_id>/', views.CategoryProductsView.as_view(), name='product-category'),
    path('_queries/calculate-total-spendings', views.UpdateTotalSpendingView.as_view(), name='total-spending'),

    # Table Creation
    path('create-tables/', views.create_tables, name='create_tables'),
    path('register/',views.register,name='register'),
    path('login/',views.login,name='login'),
    path('logout/',views.logout_view,name='logout'),

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
