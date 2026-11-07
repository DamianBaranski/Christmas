import os

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import User, WishlistFile, SiteSettings

VALID_EXTENSIONS = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.txt', '.rtf']
MAX_FILE_SIZE = 3 * 1024 * 1024


class RegisterForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('name', 'surname', 'mail')

        labels = {
            'name': _('Imię'),
            'surname': _('Nazwisko'),
            'mail': _('E-mail')
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': _('np. Jan'), 'autocomplete': 'given-name'}),
            'surname': forms.TextInput(attrs={'placeholder': _('np. Kowalski'), 'autocomplete': 'family-name'}),
            'mail': forms.EmailInput(attrs={'placeholder': 'jan@example.com', 'autocomplete': 'email'}),
        }
        error_messages = {
            'name': {'required': _('Podaj imię.')},
            'surname': {'required': _('Podaj nazwisko.')},
            'mail': {'required': _('Podaj adres e-mail.'), 'invalid': _('Podaj poprawny adres e-mail.')},
        }


class WishlistForm(forms.ModelForm):
    class Meta:
        model = WishlistFile
        fields = ('mail', 'wish_file')

        labels = {
            'mail': _('E-mail'),
            'wish_file': _('Plik z listem')
        }
        help_texts = {
            'mail': _('Adres użyty przy rejestracji.'),
            'wish_file': _('pdf, doc, docx, rtf, txt, jpg, png, gif, svg — maks. 3 MB.'),
        }
        widgets = {
            'mail': forms.EmailInput(attrs={'placeholder': 'jan@example.com', 'autocomplete': 'email'}),
            'wish_file': forms.ClearableFileInput(attrs={'accept': ','.join(VALID_EXTENSIONS)}),
        }
        error_messages = {
            'mail': {'required': _('Podaj adres e-mail.'), 'invalid': _('Podaj poprawny adres e-mail.')},
            'wish_file': {'required': _('Wybierz plik z listem.')},
        }

    def clean_wish_file(self):
        f = self.cleaned_data['wish_file']
        ext = os.path.splitext(f.name)[1].lower()
        if ext not in VALID_EXTENSIONS:
            raise forms.ValidationError(
                _('Nieobsługiwany format pliku. Akceptowane: pdf, doc, docx, rtf, txt, jpg, jpeg, png, gif, svg.'))
        if f.size > MAX_FILE_SIZE:
            raise forms.ValidationError(_('Plik jest za duży — maksymalny rozmiar to 3 MB.'))
        return f


class EventSettingsForm(forms.ModelForm):
    """Event & draw details edited in the organiser panel."""

    class Meta:
        model = SiteSettings
        fields = ('party_host', 'intro_pl', 'intro_en', 'event_at', 'event_address', 'event_details',
                  'draw_at', 'gift_budget', 'site_url')
        widgets = {
            'intro_pl': forms.Textarea(attrs={'rows': 4}),
            'intro_en': forms.Textarea(attrs={'rows': 4}),
            'event_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'draw_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'event_details': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # show the default text as a hint, so it's clear what appears when the field is empty
        for lang in ('pl', 'en'):
            self.fields['intro_' + lang].widget.attrs['placeholder'] = self.instance.default_intro(lang)
