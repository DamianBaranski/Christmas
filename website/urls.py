from django.urls import path

from . import views

urlpatterns = [
    path('', views.register, name='register'),
    path('register/', views.register, name='register'),
    path('info/', views.info, name='info'),
    path('wishlist/', views.wishlist, name='wishlist'),    
    path('confirm_user/<str:action>/<str:token>/', views.confirm_user, name='confirm_user'),
    path('confirm_wishlist/<str:token>/', views.confirm_wishlist, name='confirm_wishlist'),    
    path('checkwishlist/<str:token>/', views.checkwishlist, name='checkwishlist'),
    


]
