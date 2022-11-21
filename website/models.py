from django.db import models
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

    def __str__(self):
        return str("{} {} {}").format(self.name, self.surname, self.mail)
        
class WishlistFile(models.Model):
    mail = models.EmailField(max_length = 254)
    wish_file = models.FileField(upload_to=get_file_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    activation_token = models.CharField(max_length=32)
    activation_step = models.CharField(max_length=50, blank=False, default=None, choices=[(tag, tag.value) for tag in FileActivationSteps])
