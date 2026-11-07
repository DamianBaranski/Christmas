#!/usr/bin/python
# -*- coding: utf-8 -*-
# Command-line draw. The same can be done from the organiser panel at /admin/.
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "christmas_base.settings")
import django
django.setup()

from website.draw import run_draw, ready_users, load_locks, DrawError

print("Baza osob:", len(ready_users()))
print("Baza blokad:", len(load_locks()))
try:
    run = run_draw()
except DrawError as e:
    raise SystemExit(str(e))
total = run.pairs.count()
sent = run.pairs.filter(sent=True).count()
print("Wyslano {}/{} maili".format(sent, total))
for p in run.pairs.filter(sent=False):
    print("Blad:", p.giver.mail, p.error)
