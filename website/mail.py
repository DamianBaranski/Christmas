# -*- coding: utf-8 -*-
#For gmail you have to set app password
#https://stackoverflow.com/questions/73026671/how-do-i-now-since-june-2022-send-an-email-via-gmail-using-a-python-script
 
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from swieta import settings

def send_mail(address, topic, message):
    mail_user = settings.MAIL_LOGIN
    mail_password = settings.MAIL_PASSWORD
    sent_from = mail_user

    print(topic)
    print(sent_from)
    print(address)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = topic
    msg["From"] = sent_from
    msg["To"] = address
    
    part1 = MIMEText(message, "plain", "utf-8")
    msg.attach(part1)

    #print msg.as_string().encode('ascii')
    #mail_text = """From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s""" % (sent_from, ", ".join(address), topic, message)

   # try:
    server = smtplib.SMTP_SSL(settings.MAIL_SMTP_SERVER, settings.MAIL_SMTP_PORT)
    server.ehlo()
    server.login(mail_user, mail_password)
    server.sendmail(sent_from, [address], msg.as_string())
#    server.sendmail(sent_from, [address], mail_text)
    server.close()

    print('Email sent!')
    #except:
    #    print('Something went wrong...')


def user_registration_mail(user_mail, token):
    topic = "Rejestracja na losowanie wigilijne"
    message = "W celu potwierdzenie rejestracji na losowanie wigilijne kiknij link http://localhost:8000/confirm_user/email/"+token+"/\r\nPo kliknęciu w link czekaj na potwierdzenie od admina";
    send_mail(user_mail, topic, message)
    
def admin_registration_mail(admin_mail, user_mail, user_name, token):
    topic = "Rejestracja na losowanie wigilijne"
    message = "Czy potwierdzasz "+user_mail+" "+user_name+" http://localhost:8000/confirm_user/admin/"+token+"/";
    send_mail(admin_mail, topic, message)
    
def acount_activated_mail(user_mail):
    topic = "Rejestracja na losowanie wigilijne"
    message = "Twoje konto jest już aktywne";
    send_mail(user_mail, topic, message)    
    
def wishlist_mail(user_mail, token):
    topic = "List do św Mikołaja"
    message = "Czy potwierdzasz przesłanie listu do swietego Mikołaja: http://localhost:8000/confirm_wishlist/"+token+"/";
    send_mail(user_mail, topic, message)

    
