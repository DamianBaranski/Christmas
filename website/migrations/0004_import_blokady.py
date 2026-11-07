"""One-time import of exclusions from the old blokady.txt file."""
import os

from django.conf import settings
from django.db import migrations


def import_file(apps, schema_editor):
    path = os.path.join(settings.BASE_DIR, 'blokady.txt')
    if not os.path.exists(path):
        return
    User = apps.get_model('website', 'User')
    Exclusion = apps.get_model('website', 'Exclusion')
    with open(path, encoding='utf-8') as f:
        for line in f:
            parts = line.split()
            if len(parts) < 2 or parts[0].startswith('#'):
                continue
            giver = User.objects.filter(mail__iexact=parts[0]).first()
            receiver = User.objects.filter(mail__iexact=parts[1]).first()
            if giver and receiver and giver.pk != receiver.pk:
                Exclusion.objects.get_or_create(giver=giver, receiver=receiver)
            else:
                print('\n  blokady.txt: pominięto "{} {}" (brak takiego użytkownika)'.format(parts[0], parts[1]))


class Migration(migrations.Migration):
    dependencies = [('website', '0003_exclusion')]
    operations = [migrations.RunPython(import_file, migrations.RunPython.noop)]
