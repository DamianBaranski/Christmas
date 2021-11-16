from django import forms

from .models import User

class RegisterForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('name', 'surname', 'mail')

        labels = {
            'name': 'Imię',
            'surname': 'Nazwisko',
            'mail': 'Email'
        }
