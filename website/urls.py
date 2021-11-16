from django.urls import path

from . import views

urlpatterns = [
    path('', views.register, name='register'),
    path('register/', views.register, name='register'),
    path('info/', views.info, name='info'),
    path('confirm/<str:action>/<str:token>/', views.confirm, name='confirm'),


]
