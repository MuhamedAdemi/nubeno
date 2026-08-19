# Nubeno — Order Taking Platform

Web app for taking orders on tables from a phone: pick a table, build the
order from the menu, customize items, pay or cancel, print a receipt.
Menu is shown in Albanian (default), Croatian, and English.

- `backend/` — Django + Django REST Framework API
- `frontend/` — React + TypeScript (Vite) app

## First-time setup

### Backend

```
cd backend
venv\Scripts\python.exe -m pip install -r requirements.txt   # or see below
venv\Scripts\python.exe manage.py migrate
venv\Scripts\python.exe manage.py seed_menu      # loads the price-list menu (hr/en/sq)
venv\Scripts\python.exe manage.py seed_tables    # creates tables 1..14 (pass a number to change count)
venv\Scripts\python.exe manage.py createsuperuser  # the restaurant admin login
```

(A virtualenv already exists at `backend/venv`. If it's missing:
`python -m venv backend/venv` then `pip install django djangorestframework django-cors-headers`.)

### Frontend

```
cd frontend
npm install
```

## Running it

Two servers, both need to be running:

```
cd backend && venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
cd frontend && npm run dev
```

Vite prints a "Network" URL (e.g. `http://192.168.x.x:5173`) — that's what
waiter phones on the same WiFi should open. The frontend auto-detects the
API host from whatever hostname it was loaded from, so no config is needed
as long as both servers run on the same machine.

## Managing staff, tables, and the menu

There's no custom admin UI by design — the built-in **Django admin**
(`http://<server-ip>:8000/admin/`) covers all of it:

- **Staff logins**: only a superuser can add `User` accounts there. Give
  waitstaff `is_staff` (unchecked "superuser") accounts — they can log
  into the ordering app but not into `/admin/`'s user section.
- **Tables**: add/remove `Table` rows (the `seed_tables` command just
  bootstraps 1–14).
- **Menu, prices, categories, modifiers**: all editable there too.

## Deploying to PythonAnywhere

PythonAnywhere only runs Python (no standalone Node process for Vite), so
the deployed setup is: **build the React app to static files, and let
Django serve both the API and those static files as one app.** That's
already wired up (`whitenoise` + a catch-all SPA route in
`backend/config/urls.py`) — see [PYTHONANYWHERE.md](PYTHONANYWHERE.md)
for the exact step-by-step.

## Notes / things to double-check before real use

- Menu prices/volumes were transcribed from photos of the physical price
  list. Everything under Burger/Chicken/Pizza/Kebab/Tortilla/Ćevapi/
  Salads was read cleanly, but the **Sokovi/Juice column alignment** was
  the least legible photo — please spot-check those rows in the admin
  against the real price list before going live.
- "Pogača" (pizza menu) had no visible price in the photo and was left
  out — add it manually in the admin if it should be sold.
- CORS/hosts are wide open (`CORS_ALLOW_ALL_ORIGINS`, `ALLOWED_HOSTS=['*']`)
  since this is meant to run on the restaurant's local WiFi only, not the
  public internet. Don't expose port 8000 to the internet as-is.
