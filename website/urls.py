from django.urls import path

from . import views, panel

urlpatterns = [
    path('', views.register, name='register'),
    path('register/', views.register, name='register'),
    path('info/', views.info, name='info'),
    path('wishlist/', views.wishlist, name='wishlist'),    
    path('confirm_user/<str:action>/<str:token>/', views.confirm_user, name='confirm_user'),
    path('confirm_wishlist/<str:token>/', views.confirm_wishlist, name='confirm_wishlist'),    
    path('checkwishlist/<str:token>/', views.checkwishlist, name='checkwishlist'),
    path('letters/<str:name>/', views.letter, name='letter'),

    # organiser panel (Django's database admin lives at /admin/db/)
    path('admin/', panel.panel, name='panel'),
    path('admin/theme/', panel.set_theme, name='panel_theme'),
    path('admin/event/', panel.save_event, name='panel_event'),
    path('admin/remind/confirm/', panel.remind_confirm, name='panel_remind_confirm'),
    path('admin/remind/letter/', panel.remind_letter, name='panel_remind_letter'),
    path('admin/approve/<int:pk>/', panel.approve_user, name='panel_approve'),
    path('admin/draw/', panel.run_draw, name='panel_draw'),
    path('admin/resend/', panel.resend_failed, name='panel_resend'),
    path('admin/exclusions/add/', panel.add_exclusion, name='panel_exclusion_add'),
    path('admin/exclusions/<int:pk>/delete/', panel.delete_exclusion, name='panel_exclusion_delete'),
    


]
