from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, FileResponse, Http404
from django.urls import reverse
from django.conf import settings as django_settings
from .forms import RegisterForm, WishlistForm
from .models import UserActivationSteps, FileActivationSteps, User, WishlistFile, SiteSettings
import secrets
from christmas_base import settings
from enum import Enum, auto
from django.utils.translation import gettext as _
import os
from django.utils import timezone
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
    # site settings (host, dates, theme) come from website.context_processors.site
    return {'STATUS_ENUM': STATUS_ENUM.__members__}

#used to register new user
def register(request):
    context = getGlobalContext()
 
    if request.method != "POST":
        context['form'] = RegisterForm()
        return render(request, 'website/register.html', context)

    form = RegisterForm(request.POST)
    if not form.is_valid():
        context['form'] = form
        return render(request, 'website/register.html', context)

    mail = form.cleaned_data['mail']
    if User.objects.filter(mail=mail).exists():
        context['status'] = STATUS_ENUM.USER_EXIST
        return render(request, 'website/info.html', context)

    post = form.save(commit=False)
    post.activation_token = secrets.token_hex(16)
    post.activation_step = UserActivationSteps.EMAIL
    post.language = request.LANGUAGE_CODE
    post.save()

    user_registration_mail(mail, post.activation_token, post.language)
    
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
        if settings.ORGANISER_EMAIL:
            admin_registration_mail(settings.ORGANISER_EMAIL, user.first().mail, user.first().name, new_token)
        context['status'] = STATUS_ENUM.EMAIL_CONFIRMED
        context['user_name'] = user.first().name  
        user.update(activation_step=UserActivationSteps.ADMIN, activation_token=new_token)
        return render(request, 'website/info.html', context)

    if action == 'admin' and user[0].activation_step == UserActivationSteps.ADMIN:
        new_token=secrets.token_hex(16)
        acount_activated_mail(user.first().mail, user.first().language)
        user.update(activation_step=UserActivationSteps.READY, activation_token=new_token)
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
        
    wishlistfile.update(activation_step=FileActivationSteps.READY, uploaded_at=timezone.now())
    context['wishlist'] = reverse('letter', args=[wishlistfile.first().wish_file.name])
    context['status'] = STATUS_ENUM.FILE_CONFIRMED
    return render(request, 'website/info.html', context)
    
    
#used to send wishlist to server
def wishlist(request):
    context = getGlobalContext()
    if not SiteSettings.load().letters_enabled:
        messages.info(request, _('Wysyłanie listów do Mikołaja jest w tym roku wyłączone.'))
        return redirect('register')
 
    if request.method != "POST":
        context['form'] = WishlistForm()
        return render(request, 'website/wishlist.html', context)
      
    form = WishlistForm(request.POST, request.FILES)

    # file type/size are validated in WishlistForm.clean_wish_file
    if not form.is_valid():
        context['form'] = form
        return render(request, 'website/wishlist.html', context)

    mail = form.cleaned_data['mail']
    user = User.objects.filter(mail=mail).first()
    if not user or user.activation_step != UserActivationSteps.READY:
        form.add_error('mail', _('Ten adres nie jest zarejestrowany albo konto nie zostało jeszcze potwierdzone.'))
        context['form'] = form
        return render(request, 'website/wishlist.html', context)

    #everything is ok, send mail with confirmation
    post = form.save(commit=False)
    post.activation_token = secrets.token_hex(16)
    post.activation_step = FileActivationSteps.EMAIL
    post.save()
    # emails always use the language the person registered in
    wishlist_mail(mail, post.activation_token, user.language)

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
    context['wishlist'] = reverse('letter', args=[wishlist])
    return render(request, 'website/info.html', context)

#used to display information to user
def info(request):
    return render(request, 'website/info.html', getGlobalContext() )


#used to show an uploaded letter (works the same in development and production)
def letter(request, name):
    if name != os.path.basename(name) or not WishlistFile.objects.filter(wish_file=name).exists():
        raise Http404
    path = os.path.join(django_settings.MEDIA_ROOT, name)
    if not os.path.isfile(path):
        raise Http404
    response = FileResponse(open(path, 'rb'))
    # uploads are untrusted (e.g. SVG with scripts): never let them run as part of the site
    response['Content-Security-Policy'] = 'sandbox'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
