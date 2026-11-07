List do Mikołaja – Secret Santa site
====================================

Setup (first time):
  python3 -m venv venv
  venv/bin/pip install -r requirements.txt
  cp .env.example .env          # then fill in SECRET_KEY, email settings, ...
  venv/bin/python manage.py migrate
  venv/bin/python manage.py createsuperuser

Run for development (set DEBUG=1 in .env):
  venv/bin/python manage.py runserver
Without EMAIL_HOST in .env, emails are printed in the server console.

Organiser panel: /admin/  (Django database admin: /admin/db/)
In the panel you can:
  - set the event details (host, dates, address, gift budget) and the site style,
  - approve people, send reminders,
  - manage exclusions (who must not draw whom),
  - run the draw (or from the command line: venv/bin/python draw.py).

Tests:
  venv/bin/python manage.py test website

Translations (texts are written in Polish; English lives in website/locale/en):
  cd website && ../venv/bin/python ../manage.py makemessages -l en -l pl
  edit locale/*/LC_MESSAGES/django.po, then ../venv/bin/python ../manage.py compilemessages
