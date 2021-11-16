from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import RegisterForm
from .models import ActivationSteps, User
import secrets
from swieta import settings
from enum import Enum, auto

class STATUS_ENUM(Enum):
    REGISTER_EMAIL_SENT = auto()
    USER_EXIST = auto()
    INTERNAL_ERROR = auto()
    EMAIL_CONFIRMED = auto()
    ADMIN_CONFIRMED = auto()


def getGlobalContext():
    return {'party_host': settings.PARTY_HOST,
            'draw_date': settings.DRAW_DATE,
            'STATUS_ENUM': STATUS_ENUM.__members__,
            }

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

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
    post.activation_step = ActivationSteps.EMAIL
    post.save()
    #send mail
    context = getGlobalContext()
    context['status'] = STATUS_ENUM.REGISTER_EMAIL_SENT
    context['user_name'] = post.name
    return render(request, 'website/info.html', context)

def confirm(request, action, token):
    context = getGlobalContext()
    user = User.objects.filter(activation_token=token)
    
    if not user or len(user) != 1:
        context['status'] = STATUS_ENUM.INTERNAL_ERROR
        return render(request, 'website/info.html', context)

    if action == 'email' and user[0].activation_step == ActivationSteps.EMAIL:
        #send mail
        user.update(activation_step=ActivationSteps.ADMIN, activation_token=secrets.token_hex(16))
        context['status'] = STATUS_ENUM.EMAIL_CONFIRMED
        return render(request, 'website/info.html', context)

    if action == 'admin' and user[0].activation_step == ActivationSteps.ADMIN:
        #send mail
        user.update(activation_step=ActivationSteps.READY, activation_token='')
        context['status'] = STATUS_ENUM.ADMIN_CONFIRMED
        return render(request, 'website/info.html', context)

    return redirect('register')


def info(request):
    return render(request, 'website/info.html', getGlobalContext() )
