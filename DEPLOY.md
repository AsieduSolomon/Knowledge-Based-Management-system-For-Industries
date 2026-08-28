# Deploying DKMS

## What changed to make this deployable

- `daphne` was used in `INSTALLED_APPS` but missing from `requirements.txt` —
  the app would crash on first boot on a fresh install. Fixed.
- `SECRET_KEY` no longer has an insecure fallback — the app now refuses to
  start without a real one set in the environment.
- `DEBUG` defaults to `False`; `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` are
  read from the environment instead of being wide open (`*`).
- Static files are served in production via **WhiteNoise** (with hashed,
  long-cache filenames) — Django alone doesn't serve static files once
  `DEBUG=False`.
- Database can now point at Postgres via a `DATABASE_URL` env var (falls
  back to local SQLite when unset — no config needed for local dev).
- The WebSocket notification layer now uses Redis in production
  (`REDIS_URL`), since the in-memory layer silently breaks notifications the
  moment you run more than one worker process.
- Standard production security headers (HSTS, secure cookies, SSL redirect)
  are turned on automatically whenever `DEBUG=False`.
- Fixed: the inbox always showing "No messages" for every user (a variable
  name collided with Django's flash-messages system), the Logout link
  throwing a 405 error, and the unread-message/notification badges in the
  navbar never appearing anywhere in the app.

## Deploying on Render

1. **Push this project to a GitHub repo** (the `.gitignore` already excludes
   `venv/`, `.env`, `db.sqlite3`, and `staticfiles/`).

2. **Create a Postgres database** on Render (or reuse a Supabase Postgres
   instance) and copy its connection string.

3. **Create a Redis instance** on Render (free tier is enough) for the
   WebSocket notification layer, and copy its connection URL.

4. **Create a new Web Service** on Render, pointing at the repo:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** leave blank — the included `Procfile` handles this
     (`python manage.py migrate && python manage.py collectstatic --noinput
     && daphne -b 0.0.0.0 -p $PORT dkms_project.asgi:application`)

5. **Set environment variables** on the Render service (see `.env.example`
   for the full list):
   - `SECRET_KEY` — generate with:
     `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
   - `DEBUG=False`
   - `ALLOWED_HOSTS` — your Render URL, e.g. `dkms.onrender.com`
   - `CSRF_TRUSTED_ORIGINS` — `https://dkms.onrender.com`
   - `DATABASE_URL` — from step 2
   - `REDIS_URL` — from step 3

6. **Deploy.** Render will run migrations and collect static files
   automatically on every deploy via the Procfile.

7. **Create an admin account** once it's live, via Render's shell tab:
   `python manage.py createsuperuser`

## Notes on uploaded media (photos, audio, video, wiring diagrams)

Render's disks are ephemeral by default — anything saved to `MEDIA_ROOT`
will be **wiped on every redeploy**. For a real deployment where people are
uploading equipment photos and recordings, add a Render persistent disk to
the service (mounted at `/media`), or move `Multimedia.file` to object
storage (e.g. Cloudflare R2 or S3) if you expect meaningful upload volume.
This project currently keeps media on local disk, which is fine to start
with as long as you add the persistent disk — otherwise every upload will
vanish on the next deploy.

## Local development

Nothing changes for local dev — `.env` already has a real (dev-only)
`SECRET_KEY`, `DEBUG=True`, and sqlite/in-memory channels are used
automatically when `DATABASE_URL`/`REDIS_URL` aren't set.

```
python -m venv venv
venv\Scripts\activate        # or source venv/bin/activate on Mac/Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
