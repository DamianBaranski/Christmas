from django.db import models
from enum import Enum


class ActivationSteps(Enum):
    EMAIL = "WAIT_FOR_EMAIL"
    ADMIN = "WAIT_FOR_ADMIN"
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
    activation_token = models.CharField(max_length=20)
    activation_step = models.CharField(max_length=50, blank=False, default=None, choices=[(tag, tag.value) for tag in ActivationSteps])

    def __str__(self):
        return str("{} {} {}").format(self.name, self.surname, self.mail)
