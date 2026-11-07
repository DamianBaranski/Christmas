# Deploying List do Mikołaja

This guide assumes a Linux server (e.g. Ubuntu/Debian) with **gunicorn** running the
Django app and **nginx** in front of it serving HTTPS and static files. Paths below use
`/srv/christmas` and the domain `swieta.ebaranski.pl` — adjust them to your setup.

---

## 1. First-time installation

### 1.1 Get the code and install dependencies

```bash
sudo apt install python3-venv nginx            # if not installed yet
sudo git clone git@github.com:DamianBaranski/Christmas.git /srv/christmas
cd /srv/christmas
python3 -m venv venv
venv/bin/pip install -r requirements.txt gunicorn
```

### 1.2 Configure `.env`

All secrets and server-specific settings live in `.env` (never committed to git).

```bash
cp .env.example .env
nano .env
```

| Setting | Value |
|---|---|
| `SECRET_KEY` | **Required.** Generate: `python3 -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DEBUG` | `0` on the server |
| `ALLOWED_HOSTS` | `swieta.ebaranski.pl` |
| `CSRF_TRUSTED_ORIGINS` | `https://swieta.ebaranski.pl` |
| `ORGANISER_EMAIL` | Your address — receives "approve this person?" emails |
| `EMAIL_HOST`, `EMAIL_PORT` | e.g. `smtp.gmail.com`, `465` |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Mailbox login. For Gmail use an **app password** (<https://support.google.com/accounts/answer/185833>) |
| `DEFAULT_FROM_EMAIL` | Sender address shown in emails (usually the same mailbox) |

> ⚠️ The old Gmail password and Django secret key were committed to git in the past.
> Create a **new** Gmail app password and a **new** `SECRET_KEY` — don't reuse the old ones.

Protect the file: `chmod 600 .env`

### 1.3 Database, static files, organiser account

```bash
venv/bin/python manage.py migrate
venv/bin/python manage.py collectstatic --noinput
venv/bin/python manage.py createsuperuser
```

- `migrate` also imports exclusions from `blokady.txt` (once). Run it while the real
  `blokady.txt` is in place; lines with unknown emails are skipped and printed.
- `collectstatic` copies CSS, JS and images into `static/` for nginx.
- The account from `createsuperuser` logs in to the organiser panel at `/admin/`.

Make sure the web server user can write the database and uploads:

```bash
mkdir -p media
sudo chown -R www-data:www-data db.sqlite3 media     # db.sqlite3 exists after migrate
sudo chown www-data:www-data .                       # SQLite needs to write its journal next to the db
```

### 1.4 gunicorn as a systemd service

`/etc/systemd/system/christmas.service`:

```ini
[Unit]
Description=List do Mikolaja (gunicorn)
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/srv/christmas
ExecStart=/srv/christmas/venv/bin/gunicorn christmas_base.wsgi:application \
          --bind 127.0.0.1:8001 --workers 2 --timeout 120
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

`--timeout 120` gives the draw time to send all emails in one request.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now christmas
sudo systemctl status christmas
```

### 1.5 nginx

`/etc/nginx/sites-available/christmas`:

```nginx
server {
    server_name swieta.ebaranski.pl;
    client_max_body_size 5M;          # letters are limited to 3 MB by the app

    location /static/ {
        alias /srv/christmas/static/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Do **not** add a `location` for `/wishlist/` or `/media/`: uploaded letters are served by
the app itself at `/letters/<file>/` (with safety headers). An old rule mapping
`/wishlist/` to the media folder would hide the letter form.

```bash
sudo ln -s /etc/nginx/sites-available/christmas /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo apt install certbot python3-certbot-nginx && sudo certbot --nginx -d swieta.ebaranski.pl   # HTTPS
```

### 1.6 Set up the event

Open `https://swieta.ebaranski.pl/admin/`, log in, and in the panel:

1. **Wydarzenie** — host, Christmas Eve date & address, draw date (starts the countdown),
   gift budget, site address (used for links in emails).
2. **Styl strony** — pick one of the four styles (use "Podgląd" to preview).
3. **Blokady** — check the imported exclusions.

Send yourself a test registration to make sure emails arrive.

---

## 2. Updating to a new version

```bash
cd /srv/christmas
sudo -u www-data cp db.sqlite3 db.sqlite3.bak-$(date +%F)   # backup first
git pull
venv/bin/pip install -r requirements.txt
venv/bin/python manage.py migrate
venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart christmas
```

Translations are committed already compiled (`website/locale/*/LC_MESSAGES/django.mo`),
so the server doesn't need gettext.

---

## 3. Running the draw

From the panel (`/admin/` → **Losowanie**): tick the confirmation and click the button.
Results are stored; emails that fail can be resent with **"Wyślij ponownie nieudane"**.

Or from the server's command line:

```bash
cd /srv/christmas && sudo -u www-data venv/bin/python draw.py
```

---

## 4. Backups

Everything important is in two places — back them up regularly, especially before the draw:

- `db.sqlite3` — participants, exclusions, settings, draw results
- `media/` — uploaded letters

---

## 5. Troubleshooting

| Problem | Check |
|---|---|
| Site doesn't start, `Set SECRET_KEY in .env` | `.env` missing or `SECRET_KEY` empty |
| `Bad Request (400)` | Domain missing from `ALLOWED_HOSTS` |
| `CSRF verification failed` on forms | `CSRF_TRUSTED_ORIGINS` must contain `https://your-domain` |
| Page without styles | Run `collectstatic`; check the nginx `/static/` alias path |
| Emails not arriving | `sudo journalctl -u christmas -n 100`; verify the SMTP settings / Gmail app password; check spam |
| Draw button disabled | Fewer than 2 approved people, or exclusions make a draw impossible (the panel says which) |
| Logs | `sudo journalctl -u christmas -f` |
