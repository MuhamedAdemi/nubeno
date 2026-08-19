# Vendosja në PythonAnywhere (llogaria: nubeno)

PythonAnywhere ekzekuton vetëm Python (jo Node.js si proces i vazhdueshëm),
prandaj React nuk "xhirohet" atje si server i veçantë — ndërtohet paraprakisht
në skedarë statikë (`npm run build`) dhe Django-ja i shërben ata bashkë me API-në,
si një aplikacion i vetëm. Kjo është konfiguruar tashmë në kod
(`whitenoise` + rruga "catch-all" në `backend/config/urls.py`).

**Paketa e gatshme për ngarkim** ndodhet te
`C:\Users\Jusuf\OneDrive\Desktop\nubeno_deploy\nubeno_deploy.zip` — përmban
`backend/` (pa `venv/`, pa `db.sqlite3`) dhe `frontend/dist/` (React-i i
ndërtuar). Nuk të duhet ta rindërtosh vetë, veç nëse ndryshojmë kodin sërish.

## 1. Ngarko kodin

1. Hyr te [pythonanywhere.com](https://www.pythonanywhere.com) me llogarinë `nubeno`.
2. Skeda **Files** → shko te dosja shtëpi (`/home/nubeno/`) → **Upload a file**
   → zgjidh `nubeno_deploy.zip` nga kompjuteri.
3. Hap një **Bash console** (skeda **Consoles** → **Bash**) dhe:
   ```
   unzip nubeno_deploy.zip
   ```
   Kjo krijon `/home/nubeno/nubeno/backend/` dhe `/home/nubeno/nubeno/frontend/dist/`.

## 2. Krijo virtualenv dhe instalo varësitë

Në të njëjtin Bash console:

```
mkvirtualenv --python=python3.12 nubeno-env
pip install -r ~/nubeno/backend/requirements.txt
```

(Django 6.0 kërkon Python 3.12+, prandaj pikërisht ky version. `mkvirtualenv`
e krijon dhe e aktivizon menjëherë; herët e tjera që hyn, aktivizohet me
`workon nubeno-env`.)

## 3. Konfiguro aplikacionin Web

Skeda **Web** → **Add a new web app** → **Next** → **Manual configuration**
(jo wizard-in "Django", sepse projekti ekziston tashmë) → zgjidh **Python 3.12**
(i njëjti version si virtualenv-i) → **Next**.

Në faqen e konfigurimit që hapet për app-in:

- **Source code**: `/home/nubeno/nubeno/backend`
- **Working directory**: `/home/nubeno/nubeno/backend`
- **Virtualenv**: `/home/nubeno/.virtualenvs/nubeno-env`
- **WSGI configuration file**: kliko linkun blu (diçka si
  `/var/www/nubeno_pythonanywhere_com_wsgi.py`) dhe **fshi gjithçka** brenda,
  zëvendësoje me:

  ```python
  import os
  import sys

  path = '/home/nubeno/nubeno/backend'
  if path not in sys.path:
      sys.path.insert(0, path)

  os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
  os.environ['DJANGO_SECRET_KEY'] = 'VENDOS_KËTU_NJË_VARG_TË_GJATË_RASTËSOR'
  os.environ['DJANGO_DEBUG'] = 'False'
  os.environ['DJANGO_ALLOWED_HOSTS'] = 'nubeno.pythonanywhere.com'

  from django.core.wsgi import get_wsgi_application
  application = get_wsgi_application()
  ```

  Për `DJANGO_SECRET_KEY`, gjenero një varg rastësor te Bash console:
  ```
  python -c "import secrets; print(secrets.token_urlsafe(50))"
  ```
  dhe ngjite rezultatin në vend të `VENDOS_KËTU_...`. Ruaje skedarin (Save).

## 4. Migro bazën e të dhënave

Kthehu te Bash console (sigurohu që `(nubeno-env)` shfaqet në fillim të
rreshtit — nëse jo, shkruaj `workon nubeno-env`):

```
cd ~/nubeno/backend
python manage.py migrate
python manage.py seed_menu
python manage.py seed_tables
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

`createsuperuser` do të kërkojë username/email/password — kjo bëhet llogaria
jote e administratorit në internet (mund të jetë e ndryshme nga ajo lokale).

## 5. Rilendo (Reload) aplikacionin

Kthehu te skeda **Web** dhe kliko butonin e madh jeshil **Reload
nubeno.pythonanywhere.com**. Hap pastaj:

```
https://nubeno.pythonanywhere.com
```

Duhet të shohësh faqen e login-it. Kyçu me llogarinë e superuser-it që
krijove në hapin 4.

## Nëse diçka s'punon

Skeda **Web** → poshtë faqes ka **Error log** dhe **Server log** — aty shfaqet
saktësisht ku ka dështuar (p.sh. path i gabuar, modul mungues). Kopjo gabimin
dhe ma trego.

## Përditësime më vonë

Kur ndryshojmë kodin këtu (te kompjuteri): do ta rindërtoj (`npm run build`)
dhe do të krijoj një zip të ri për ty. Ti duhet vetëm ta ringarkosh (Files →
Upload, mbishkruan `nubeno_deploy.zip`), pastaj në Bash console:
```
cd ~
unzip -o nubeno_deploy.zip
cd nubeno/backend
python manage.py migrate
python manage.py collectstatic --noinput
```
pastaj **Reload** nga skeda Web.

**Shënim njëhershëm (korrik 2026):** ky përditësim solli hierarkinë
super-admin/admin dhe faqen e Analitikës. Menjëherë pas `migrate`, ekzekuto
edhe (vetëm një herë, për të shënuar llogarinë tënde si super-admin):
```
python manage.py set_super_admin muhamedademi
```

## Kufizime të planit falas që vlen t'i dish

- Një domain i vetëm: `nubeno.pythonanywhere.com` (pa domain vetjak pa pagesë).
- SQLite (baza aktuale) funksionon mirë për një restorant të vogël; nëse
  më vonë keni shumë porosi njëkohësisht dhe shihni gabime "database is
  locked", kalimi te MySQL (ofrohet nga PythonAnywhere) është hapi tjetër.
- Aksesi në internet nga vetë serveri është i kufizuar në një listë të
  bardhë në planin falas — nuk prek këtë app, sepse s'thërret shërbime
  të jashtme.
- **Printimi vazhdon të funksionojë njësoj** — butoni i printimit e hap
  dialogun e printimit të vetë telefonit/kompjuterit që po e përdor
  kamerieri, pavarësisht nëse app-i xhiron lokalisht apo në internet.
