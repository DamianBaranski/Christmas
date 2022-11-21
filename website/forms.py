from django import forms
from .models import User, WishlistFile
    
class RegisterForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('name', 'surname', 'mail')

        labels = {
            'name': 'Imię',
            'surname': 'Nazwisko',
            'mail': 'Email'
        }

class WishlistForm(forms.ModelForm):
    class Meta:
        model = WishlistFile
        fields = ('mail', 'wish_file')

        labels = {
            'mail': 'Email',
            'wish_file': 'Plik'
        }
