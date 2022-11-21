from django import forms
from .models import User, WishlistFile
    
class RegisterForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('name', 'surname', 'mail')

        labels = {
            'name': 'Imię',
            'surname': 'Nazwisko',
            'mail': 'E-mail'
        }

class WishlistForm(forms.ModelForm):
    class Meta:
        model = WishlistFile
        fields = ('mail', 'wish_file')

        labels = {
            'mail': 'E-mail',
            'wish_file': 'Plik'
        }
