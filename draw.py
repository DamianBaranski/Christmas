#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "christmas_base.settings")
import django
django.setup()

from website.models import UserActivationSteps, User
from website.mail import *
from random import shuffle  #shuffle list
import numpy as np          #for list of locks 



def send_draw_mail(person, random_person):
  subject = 'Wyniki losowania'
  message =  person.name+", \n\nŚwięty Mikołaj nie da rady samemu obdarować wszystkich, "
  message += "musisz mu pomoc. \nZrób prezent dla "+random_person.name+" "+random_person.surname+" do kwoty 50 zł, ";
  message += "Pod tym adresem możesz sprawdzić czy wylosowana osoba przesłała list: https://swieta.ebaranski.pl/checkwishlist/"+random_person.activation_token+"/";
  message += "\nJeśli Ty jeszcze nie przesłałeś listu to możesz zrobić to tu: https://swieta.ebaranski.pl/wishlist/";
  message += "\n\nPozdrawiam\nŚwięty Mikołaj\n\n\n";

  send_mail(person.mail, subject, message)


users = list(User.objects.filter(activation_step=UserActivationSteps.READY))
shuffle(users)

locks=np.genfromtxt('blokady.txt', delimiter=" ", dtype=None, encoding='utf-8');
ok = False

print("Baza osob:", len(users))
print("Baza blokad:", len(locks))
while ok==False:
  ok=True;
  shuffle(users)    #randomize list of users
  for lock in locks:
    for index in range(0,len(users)-1):
      if(lock[0]==users[index].mail and lock[1]==users[index+1].mail): 
        ok=False;

    if(lock[0]==users[len(users)-1].mail and lock[1]==users[0].mail): 
      ok=0;

#wyswietlam emaile
for index in range(0,len(users)-1):
  send_draw_mail(users[index], users[index+1]);
send_draw_mail(users[len(users)-1], users[0]);

#for index in range(0,len(users)-1):
#  print(users[index].name+" "+users[index].surname+"->"+users[index+1].name+" "+users[index+1].surname);
#print(users[len(users)-1].name+" "+users[len(users)-1].surname+"->"+users[0].name+" "+users[0].surname);

