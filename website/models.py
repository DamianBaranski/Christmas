from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from enum import Enum
import uuid
import os

def get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename_start = filename.replace('.'+ext,'')
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return filename

class UserActivationSteps(Enum):
    EMAIL = "WAIT_FOR_EMAIL"
    ADMIN = "WAIT_FOR_ADMIN"
    READY = "READY"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.value == other.value
        else:
            return str(self) == str(other)

class FileActivationSteps(Enum):
    EMAIL = "WAIT_FOR_EMAIL"
    READY = "READY"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.value == other.value
        else:
            return str(self) == str(other)

class User(models.Model):
    name = models.CharField(max_length=200)
    surname = models.CharField(max_length=200)
    mail = models.EmailField(max_length = 254)
    activation_token = models.CharField(max_length=32)
    activation_step = models.CharField(max_length=50, blank=False, default=None, choices=[(tag, tag.value) for tag in UserActivationSteps])
    # language the person registered in; their emails are sent in it
    language = models.CharField(max_length=10, choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE)

    def __str__(self):
        return str("{} {} {}").format(self.name, self.surname, self.mail)
        
class WishlistFile(models.Model):
    mail = models.EmailField(max_length = 254)
    wish_file = models.FileField(upload_to=get_file_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    activation_token = models.CharField(max_length=32)
    activation_step = models.CharField(max_length=50, blank=False, default=None, choices=[(tag, tag.value) for tag in FileActivationSteps])


class SiteSettings(models.Model):
    """Single-row table with settings editable from the organiser panel."""
    THEME_WINTER = 'winter'
    THEME_COZY = 'cozy'
    THEME_DAY = 'day'
    THEME_CHOICES = [
        (THEME_WINTER, _('Zimowa noc')),
        (THEME_COZY, _('Przytulny kominek')),
        (THEME_DAY, _('Śnieżny dzień')),
    ]

    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default=THEME_WINTER)

    # event & draw details, editable in the organiser panel
    party_host = models.CharField(_('Gospodarz (w dopełniaczu, np. „Agnieszki”)'), max_length=100, default='Agnieszki')
    draw_at = models.DateTimeField(_('Data losowania'), null=True, blank=True)
    gift_budget = models.CharField(_('Budżet na prezent'), max_length=50, default='50 zł')
    site_url = models.URLField(_('Adres strony (do linków w mailach)'), default='https://swieta.ebaranski.pl')
    event_at = models.DateTimeField(_('Data i godzina wigilii'), null=True, blank=True)
    event_address = models.CharField(_('Adres'), max_length=200, blank=True)
    event_details = models.TextField(_('Dodatkowe informacje'), blank=True,
                                     help_text=_('Np. strój, co przynieść, parking.'))

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return 'Ustawienia strony'


class DrawRun(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'Losowanie {:%Y-%m-%d %H:%M}'.format(self.created_at)


class DrawPair(models.Model):
    run = models.ForeignKey(DrawRun, on_delete=models.CASCADE, related_name='pairs')
    giver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    sent = models.BooleanField(default=False)
    error = models.TextField(blank=True)

    def __str__(self):
        return '{} -> {}'.format(self.giver, self.receiver)


class Exclusion(models.Model):
    """'giver' must not draw 'receiver' (e.g. partners, people who live together)."""
    giver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')

    class Meta:
        unique_together = ('giver', 'receiver')

    def __str__(self):
        return '{} nie losuje {}'.format(self.giver, self.receiver)
