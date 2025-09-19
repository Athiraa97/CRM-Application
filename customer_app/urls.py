from . import views
from django.urls import path

urlpatterns = [
    path('', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_create, name='customer_add'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    
    path('customers/bulk-upload/', views.customer_bulk_upload, name='customer_bulk_upload'),
    path('customers/download/pdf/', views.download_customers_pdf, name='download_customers_pdf'),
    path("customers/<int:pk>/download/", views.download_customer_pdf_individual, name="download_customer_pdf_individual"),

    path('users/', views.user_list, name='user_list'),
    path('users/add/', views.user_add, name='user_add'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]