from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import RegisterForm, WishlistForm
from .models import UserActivationSteps, FileActivationSteps, User, WishlistFile
import secrets
from swieta import settings
from enum import Enum, auto
import os
import datetime
from .mail import *

class STATUS_ENUM(Enum):
    REGISTER_EMAIL_SENT = auto()
    USER_EXIST = auto()
    INTERNAL_ERROR = auto()
    EMAIL_CONFIRMED = auto()
    ADMIN_CONFIRMED = auto()
    USER_NOT_EXIST = auto()
    WRONG_FILE_EXT = auto()
    WRONG_FILE_SIZE = auto()
    FILE_SENT = auto()
    NO_WISH_LIST = auto()
    WISH_LIST = auto()
    FILE_CONFIRMED = auto()

def getGlobalContext():
    return {'party_host': settings.PARTY_HOST,
            'draw_date': settings.DRAW_DATE,
            'STATUS_ENUM': STATUS_ENUM.__members__,
            }

#used to register new user
def register(request):
    context = getGlobalContext()
 
    if request.method != "POST":
        context['form'] = RegisterForm()
        return render(request, 'website/register.html', context)

    form = RegisterForm(request.POST)
    if not form.is_valid():
        context['status'] = STATUS_ENUM.INTERNAL_ERROR
        return render(request, 'website/info.html', context)

    mail = form.cleaned_data['mail']
    if User.objects.filter(mail=mail).exists():
        context['status'] = STATUS_ENUM.USER_EXIST
        return render(request, 'website/info.html', context)

    post = form.save(commit=False)
    post.activation_token = secrets.token_hex(16)
    post.activation_step = UserActivationSteps.EMAIL
    post.save()
    
    user_registration_mail(mail, post.activation_token)
    
    context = getGlobalContext()
    context['status'] = STATUS_ENUM.REGISTER_EMAIL_SENT
    context['user_name'] = post.name
    return render(request, 'website/info.html', context)


#used to confirm that the user has registered or admin aproved   
def confirm_user(request, action, token):
    context = getGlobalContext()
    user = User.objects.filter(activation_token=token)
    
    if not user or len(user) != 1:
        context['status'] = STATUS_ENUM.INTERNAL_ERROR
        return render(request, 'website/info.html', context)

    if action == 'email' and user[0].activation_step == UserActivationSteps.EMAIL:
        new_token=secrets.token_hex(16)
        admin_registration_mail(settings.ADMINS, user.first().mail, user.first().name, new_token)
        user.update(activation_step=UserActivationSteps.ADMIN, activation_token=new_token)
        context['status'] = STATUS_ENUM.EMAIL_CONFIRMED
        return render(request, 'website/info.html', context)

    if action == 'admin' and user[0].activation_step == UserActivationSteps.ADMIN:
        acount_activated_mail(user.first().mail)
        user.update(activation_step=UserActivationSteps.READY, activation_token='')
        context['status'] = STATUS_ENUM.ADMIN_CONFIRMED
        return render(request, 'website/info.html', context)

    return redirect('register')
    

#used to confirm that the user has submitted the wishlist   
def confirm_wishlist(request, token):
    context = getGlobalContext()
    wishlistfile = WishlistFile.objects.filter(activation_token=token)
    
    if not wishlistfile or len(wishlistfile) != 1:
        context['status'] = STATUS_ENUM.INTERNAL_ERROR
        return render(request, 'website/info.html', context)
        
    wishlistfile.update(activation_step=UserActivationSteps.ADMIN, uploaded_at=datetime.datetime.now())
    context['wishlist'] = settings.MEDIA_URL+wishlistfile.first().wish_file.name
    context['status'] = STATUS_ENUM.FILE_CONFIRMED
    return render(request, 'website/info.html', context)
    
    
#used to send wishlist to server
def wishlist(request):
    context = getGlobalContext()
 
    if request.method != "POST":
        context['form'] = WishlistForm()
        return render(request, 'website/wishlist.html', context)
      
    form = WishlistForm(request.POST, request.FILES)

    if not form.is_valid():     
        context['status'] = STATUS_ENUM.INTERNAL_ERROR
        return render(request, 'website/info.html', context)
        
    #check file type
    ext = os.path.splitext(form.files['wish_file'].name)[1] 
    valid_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.png', '.txt', '.jpeg', '.rtf', '.gif', '.svg']
    if not ext.lower() in valid_extensions:
        context['status'] = STATUS_ENUM.WRONG_FILE_EXT
        return render(request, 'website/info.html', context)
        
    #check file size
    if form.files['wish_file'].size > 3*1024*1024:
        context['status'] = STATUS_ENUM.WRONG_FILE_SIZE
        return render(request, 'website/info.html', context)
 	
    mail = form.cleaned_data['mail']
    print(mail)
    if not User.objects.filter(mail=mail).exists() or User.objects.filter(mail=mail).first().activation_step != UserActivationSteps.READY:
        context['status'] = STATUS_ENUM.USER_NOT_EXIST
        return render(request, 'website/info.html', context)

    #everything is ok, send mail with confirmation
    post = form.save(commit=False)
    post.activation_token = secrets.token_hex(16)
    post.activation_step = FileActivationSteps.EMAIL
    post.save()
    wishlist_mail(mail, post.activation_token)
      
    context['status'] = STATUS_ENUM.FILE_SENT
    return render(request, 'website/info.html', context)

#used to check if wishlist is on server and is confirmed
def checkwishlist(request, token):
    context = getGlobalContext()
    
    if not User.objects.filter(activation_token=token).exists() or User.objects.filter(activation_token=token).first().activation_step != UserActivationSteps.READY:
        context['status'] = STATUS_ENUM.NO_WISH_LIST
        return render(request, 'website/info.html', context)
        
    mail = User.objects.filter(activation_token=token).first().mail
    
    if not WishlistFile.objects.filter(mail=mail).exists():
        context['status'] = STATUS_ENUM.NO_WISH_LIST
        return render(request, 'website/info.html', context)
    
    wishlist = WishlistFile.objects.filter(mail=mail).order_by('-uploaded_at').first().wish_file.name    
    context['status'] = STATUS_ENUM.WISH_LIST
    context['wishlist'] = settings.MEDIA_URL+wishlist
    return render(request, 'website/info.html', context)

#used to display information to user
def info(request):
    return render(request, 'website/info.html', getGlobalContext() )
