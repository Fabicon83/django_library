# Django 6.1 su Docker: una biblioteca di grandi dimensioni (da Symfony e Magento a Python)

> **Obiettivo:** imparare Django in modo professionale costruendo il gestionale di una **grande biblioteca**
> multi-sede: catalogo da centinaia di migliaia di libri, copie fisiche, lettori, prestiti, ricerca full-text,
> API REST, task in background, test.
> Percorso: ambiente Docker → progetto e utente custom → modelli → admin → dati massivi e ORM veloce →
> catalogo pubblico → login e permessi → prestiti (logica di dominio) → ricerca PostgreSQL → API REST →
> task, email e cache → test → **frontend** (lo scegliamo insieme, vedi [FRONTEND.md](FRONTEND.md)) → produzione.
>
> **Il tuo mentore:** Claude. A fine fase scrivimi *"fase X fatta"* oppure incolla l'errore:
> controllo i file (percorso e contenuto), verifico nei container e ti spiego il perché.

---

## ▶️ Ogni giorno, all'avvio del PC

I container **non ripartono da soli** dopo un riavvio. Prima di lavorare:

```bash
cd /var/www/html/COURSES/django_learn
docker compose up -d       # accende tutti i servizi (db, web, valkey, mailpit, e dalla Fase 10 il worker)
docker compose ps          # db "healthy", gli altri "Up"
```

Poi http://localhost:8100. Codice e database sono al sicuro tra un riavvio e l'altro; **mai**
`docker compose down -v` (cancella il database). Dettagli: [Fase 2.7](#27-cosa-sopravvive-a-un-riavvio-di-docker-o-del-pc).

> Prima della Fase 2.4 (progetto Django non ancora creato) accendi solo `docker compose up -d db valkey mailpit`.

---

## Come usare questa guida

1. **Scrivi i file a mano.** Il codice è un riferimento da confrontare *dopo*.
2. **Ogni fase finisce con un ✅ Checkpoint.** Non passare alla successiva finché non è verde.
3. **I blocchi 🧠 Domanda** sono tipiche domande da colloquio: pensa alla risposta prima di aprirla.
4. **Lavori in:** `/var/www/html/COURSES/django_learn/` (il codice Django in `backend/`).
   Ogni blocco di codice è preceduto dal **percorso completo** del file e da cosa farci:

   | Etichetta | Cosa fare |
   |---|---|
   | 📄 `backend/x.py` — 🆕 **nuovo file** | crea il file (e le cartelle che mancano) e incolla il blocco |
   | 📄 `backend/x.py` — 🔁 **sostituisci tutto** | il file esiste (di solito generato da `startapp`): cancella tutto e metti il blocco |
   | 📄 `backend/x.py` — ✏️ **modifica** | il file esiste: cambia o aggiungi **solo** quello che dice il testo, il resto resta |

   Percorsi che iniziano con `django_learn/` stanno fuori da `backend/` (Docker, `.env`, `.gitignore`).
5. **Python solo nel container.** Il Python locale (3.12) non si usa: come per PHP in Symfony e Magento.
6. **Paragoni:** 🅢 = come in Symfony (`symfony_learn`), 🅜 = come in Magento (`magento2_learn`).

> **Stato del codice:** tutto il codice di questa guida è stato eseguito il 2026-10-07 su un progetto di
> prova (Django 6.1.2, Python 3.14.8, PostgreSQL 18, DRF 3.18.3): migrazioni, seed da 50.000 libri,
> pagine, banco prestiti, API, worker con email su Mailpit e 8 test verdi.

### Versioni (verificate a ottobre 2026)

| Componente | Versione | Note |
|---|---|---|
| **Django** | **6.1** (6.1.2) | uscita ad agosto 2026. Python 3.12-3.14 |
| Django LTS | 5.2 | supportata fino ad aprile 2028: la troverai in molte aziende |
| Prossima LTS | 6.2 | aprile 2027 |
| **Python** | **3.14** | la 3.15 esce proprio in questi giorni: Django 6.1 non la supporta ancora |
| PostgreSQL | 18 | |
| Django REST framework | 3.18 | supporta Django 5.2, 6.0, 6.1 |
| Poetry | 2.5 | gestore di dipendenze e virtualenv (al posto di pip + venv) |

**Ciclo di rilascio** (domanda frequente): una feature release ogni 8 mesi circa; l'ultima di ogni serie
(`x.2`) è **LTS** con 3 anni di supporto. Dal 2028 Django passa al **calendar versioning**: dopo la 6.2
arriverà "Django 2028" (non 7.0).

### Stack che costruiremo

```
django_learn/
├── compose.yaml        web (Django), worker (task), db (PostgreSQL 18), valkey (cache), mailpit (email)
├── .env                segreti e configurazione: lo crei tu
├── docker/python/Dockerfile
├── backend/            il progetto Django (bind mount in /app)
│   ├── config/         settings, urls, wsgi/asgi      🅢 config/ + Kernel
│   ├── accounts/       utente custom
│   ├── catalog/        autori, editori, soggetti, libri
│   ├── inventory/      sedi e copie fisiche
│   ├── circulation/    lettori, prestiti, servizi, task
│   ├── api/            Django REST framework
│   └── templates/      template di progetto (base.html, login)
└── frontend/           Fase 14: lo decidiamo insieme
```

| Servizio | URL / porta |
|---|---|
| Django | http://localhost:8100 (admin su `/admin/`, API su `/api/`) |
| PostgreSQL | `localhost:5440` (DBeaver: utente/password/db `library`) |
| Mailpit | http://localhost:8036 |
| Valkey | solo interno (`valkey:6379`) |

### Perché questa biblioteca è "grande"

Un CRUD da 5 libri non insegna niente sulle prestazioni. Qui il catalogo avrà **50.000-500.000 libri**
e oltre il doppio di copie: ogni N+1, indice mancante o `COUNT(*)` di troppo si **sente**. È lo stesso
motivo per cui Magento ha indexer e OpenSearch.

---

## Fase 0: da Symfony a Django (leggi, 30 minuti)

| Concetto | Symfony 8 | Magento 2 | Django 6.1 |
|---|---|---|---|
| Pattern | MVC | MVC + layout XML | **MTV**: Model, Template, View (la *view* è il controller) |
| Unità di codice | bundle (raro) / `src/` | modulo `app/code/Vendor/Module` | **app** (`python manage.py startapp`), registrata in `INSTALLED_APPS` |
| Console | `bin/console` | `bin/magento` | `python manage.py` |
| Configurazione | YAML/PHP in `config/`, `.env` | XML + `env.php` | **un file Python**: `config/settings.py` |
| Routing | attributi `#[Route]` | `routes.xml` + cartelle | `urls.py` con `path()` e `include()` |
| Controller | classe + metodo | una classe per azione, `execute()` | funzione o **class-based view** (`ListView`, `FormView`...) |
| ORM | Doctrine (*Data Mapper*: entity + EntityManager) | resource model + collection | **Active Record**: `book.save()`, `Book.objects.filter()` |
| Repository | `BookRepository` | repository + service contract | **Manager / QuerySet** (`Book.objects`) |
| Migrazioni | `make:migration` + `doctrine:migrations:migrate` | `db_schema.xml` dichiarativo | `makemigrations` + `migrate` (generate dai modelli) |
| Template | Twig | phtml + layout XML | Django Template Language (molto simile a Twig) |
| Form | Form component | UI Components | `forms.Form` / `forms.ModelForm` |
| Backoffice | EasyAdmin (bundle) | admin con UI Components | **admin integrato**, generato dai modelli |
| Eventi | EventDispatcher / listener | observer `events.xml` | **signals** (`post_save`...) e **middleware** |
| Dependency injection | container + autowiring | ObjectManager + `di.xml` | **non c'è**: import di moduli e funzioni |
| Code / async | Messenger | message queue + cron | **Tasks framework** (6.0+) con un backend (qui DB) |
| API | controller JSON / API Platform | `webapi.xml` + service contracts | **Django REST framework** |
| Dipendenze | Composer | Composer | **Poetry** (`pyproject.toml` + `poetry.lock`) |
| Esecuzione | PHP-FPM: un processo per richiesta | PHP-FPM | **processo lungo** (WSGI/ASGI): gunicorn, uvicorn |

**Le tre differenze che contano di più:**

1. **Niente container DI.** In Symfony chiedi i servizi nel costruttore; in Django *importi* funzioni e
   classi. La logica di dominio va in moduli normali (`services.py`) che importi dove servono. Nei test
   si sostituisce con fixture e `unittest.mock`, non con il container.
2. **Active Record.** Il modello sa salvarsi (`book.save()`), e `Book.objects` è il punto d'accesso
   alle query. Non c'è un EntityManager, non c'è `flush()`: ogni `save()` è subito un `INSERT`/`UPDATE`.
3. **Processo lungo.** Con PHP-FPM ogni richiesta riparte da zero. Un processo Django serve migliaia di
   richieste: una variabile globale modificata **resta** modificata. Mai stato mutabile a livello di modulo.

🧠 **Domanda:** perché si dice che Django è "batteries included"?
<details><summary>Risposta</summary>
Nel pacchetto base ci sono ORM, migrazioni, admin, autenticazione con utenti/gruppi/permessi, sessioni, form,
template, cache, email, i18n, protezione CSRF/XSS/clickjacking, sitemap, e da 6.0 anche task in background e CSP.
Symfony parte minimale e aggiungi componenti; Django parte completo e sostituisci quello che non ti serve.
</details>

🧠 **Domanda:** progetto o app?
<details><summary>Risposta</summary>
Il <b>progetto</b> è la configurazione (settings, URL radice, WSGI/ASGI). Le <b>app</b> sono pacchetti Python
riusabili con modelli, viste, template, migrazioni: un progetto ne attiva molte in <code>INSTALLED_APPS</code>
(anche quelle di Django, come <code>django.contrib.admin</code>). Un'app ≈ un modulo Magento, ma senza XML.
</details>

✅ **Checkpoint 0:** sai spiegare MTV, Active Record vs Data Mapper e perché uno stato globale è pericoloso
in un processo Django.

---

## Fase 1: ambiente Docker

### 1.1 Cartelle

```bash
cd /var/www/html/COURSES/django_learn
mkdir -p docker/python backend
```

> Crea `backend/` **prima** di avviare Docker: se manca, Docker la crea come root e non potrai scriverci.

Alla fine della Fase 1 avrai:

```
django_learn/
├── compose.yaml              ← nella radice, NON in docker/python/
├── .env                      ← nella radice, NON in docker/python/
├── docker/python/Dockerfile  ← l'unico file dentro docker/python/
└── backend/                  vuota per ora
```

`docker/python/` contiene solo il Dockerfile (è il *build context*). `compose.yaml` sta nella radice perché
i suoi percorsi (`./docker/python`, `./backend`, `.env`) sono relativi alla cartella del file, e perché
`docker compose` e gli alias si lanciano da `django_learn/`.

### 1.2 `docker/python/Dockerfile`

📄 `django_learn/docker/python/Dockerfile` — 🆕 **nuovo file**

```dockerfile
# Immagine ufficiale di Python 3.14 su Debian trixie
FROM python:3.14-slim-trixie

ARG UID=1000
ARG GID=1000
# -l: niente lastlog (con UID molto alti il file diventerebbe enorme)
RUN groupadd -g "$GID" app && useradd -l -m -u "$UID" -g "$GID" app

# Poetry in un venv tutto suo: le sue dipendenze non si mescolano con quelle del progetto
RUN python -m venv /opt/poetry \
    && /opt/poetry/bin/pip install --no-cache-dir "poetry~=2.5" \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/home/app/.cache/pypoetry \
    PATH="/app/.venv/bin:$PATH"

USER app
RUN mkdir -p /home/app/.cache/pypoetry
WORKDIR /app
```

- `PYTHONUNBUFFERED=1`: i `print()` e i log arrivano subito in `docker compose logs`.
- `POETRY_VIRTUALENVS_IN_PROJECT=true`: il venv va in `backend/.venv` (non in `~/.cache/pypoetry`),
  quindi sopravvive alla ricreazione del container. 🅢 come `vendor/`.
- `PATH` con `/app/.venv/bin`: dentro il container `python` è già quello del virtualenv del progetto,
  senza `poetry run` davanti.
- `POETRY_NO_INTERACTION=1`: Poetry non fa mai domande (comodo con `docker compose exec`).
- Poetry vive in `/opt/poetry`, **fuori** dal venv del progetto: è uno strumento, non una dipendenza.
- Utente `app` con **il tuo UID/GID**: i file creati nel container restano tuoi (come `www-data` in Magento).

### 1.3 `compose.yaml` (in `django_learn/`)

📄 `django_learn/compose.yaml` — 🆕 **nuovo file**

> Anche `compose.yml` va bene: `docker compose` cerca entrambi i nomi. `compose.yaml` è quello preferito.

```yaml
services:
  web:
    build:
      context: ./docker/python
      args:
        UID: 1035402654      # id -u
        GID: 1035402619      # id -g
    image: django-learn:py3.14
    container_name: dj_web
    env_file: .env
    volumes:
      - ./backend:/app
      - poetry_cache:/home/app/.cache/pypoetry
    ports:
      - "8100:8000"
    command: ["python", "manage.py", "runserver", "0.0.0.0:8000"]
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:18
    container_name: dj_db
    env_file: .env
    ports:
      - "5440:5432"
    volumes:
      # Da PostgreSQL 18 l'immagine vuole il volume su /var/lib/postgresql (non più .../data)
      - db_data:/var/lib/postgresql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      retries: 20

  valkey:
    image: valkey/valkey:9-alpine
    container_name: dj_valkey

  mailpit:
    image: axllent/mailpit:latest
    container_name: dj_mailpit
    ports:
      - "8036:8025"

volumes:
  db_data:
  poetry_cache:
```

> `$${POSTGRES_USER}`: il doppio `$` dice a Compose di non sostituirlo lui; la variabile la legge la shell
> del container, dove `env_file` l'ha messa.

### 1.4 `.env` (in `django_learn/`, lo crei tu)

📄 `django_learn/.env` — 🆕 **nuovo file**

```dotenv
POSTGRES_DB=library
POSTGRES_USER=library
POSTGRES_PASSWORD=library
DJANGO_DEBUG=1
DJANGO_SECRET_KEY=dev-solo-in-locale-cambiami
```

Lo stesso file serve a PostgreSQL (crea utente e database al primo avvio) e a Django (lo leggeremo in
`settings.py` con `os.environ`). 🅢 È il `.env` di Symfony, ma senza il componente Dotenv: le variabili
arrivano già nell'ambiente del processo.

### 1.5 Build e avvio dei servizi di supporto

```bash
docker compose build
docker compose up -d db valkey mailpit
docker compose ps        # db deve essere "healthy"
```

`web` non lo avviamo ancora: il progetto Django non esiste.

### 1.6 Alias comodi (aggiungili al tuo `~/.bashrc`)

```bash
alias dj='docker compose exec web python manage.py'   # dj migrate, dj shell, dj createsuperuser...
alias djpo='docker compose exec web poetry'           # djpo add requests
alias djtest='docker compose exec web pytest'
```

Poi `source ~/.bashrc` (o apri un nuovo terminale). Funzionano dalla cartella `django_learn/` (o da una
sua sottocartella), come gli alias di Magento.

> ⚠️ **Gli alias usano `exec`: funzionano solo con `web` avviato.** `web` parte solo dalla Fase 2.4
> (prima il progetto Django non esiste). Fino ad allora la guida usa `docker compose run --rm web ...`.
>
> | Comando | Cosa fa | Quando |
> |---|---|---|
> | `docker compose run --rm web <cmd>` | crea un container nuovo, esegue `<cmd>`, lo cancella | `web` spento (Fasi 2.1-2.4) |
> | `docker compose exec web <cmd>` (= alias) | entra nel container `web` già acceso | dalla Fase 2.4 in poi |
>
> 🅜 `run --rm` ≈ `docker run` usa e getta; `exec` ≈ `docker exec -it php-fpm bin/magento ...`.
> Errore tipico: `service "web" is not running` → usa `run --rm` oppure `docker compose up -d web`.

✅ **Checkpoint 1:** `docker compose ps` mostra `db` healthy, `valkey` e `mailpit` up; http://localhost:8036 apre Mailpit.

---

## Fase 2: progetto Django, PostgreSQL e utente custom

### 2.1 Progetto con Poetry

📄 `backend/pyproject.toml` — 🆕 **nuovo file**:

```toml
[project]
name = "biblioteca"
version = "0.1.0"
requires-python = ">=3.14,<3.15"
dependencies = []

[tool.poetry]
# È un'applicazione, non una libreria da pubblicare: Poetry non deve installare il progetto stesso
package-mode = false
```

```bash
docker compose run --rm web poetry add "django~=6.1.0" "psycopg[binary]~=3.3"
docker compose run --rm web django-admin startproject config .
ls -a backend   # .venv  config  manage.py  poetry.lock  pyproject.toml
```

- `run --rm` crea un container usa e getta: serve finché `web` non può partire da solo.
- `poetry add` scrive la dipendenza in `pyproject.toml`, aggiorna **`poetry.lock`** e installa in `.venv`.
  🅢 `pyproject.toml` ≈ `composer.json`, `poetry.lock` ≈ `composer.lock` (va in git),
  `poetry add` ≈ `composer require`, `poetry install` ≈ `composer install`.
- `package-mode = false`: senza, `poetry install` cerca un pacchetto `biblioteca/` da installare e fallisce.
- Usa **sempre** il Poetry del container: mai `poetry ...` da solo nel terminale, ma
  `docker compose run --rm web poetry ...` (ora) o `djpo ...` (dalla Fase 2.4). Il Poetry dell'host
  userebbe il Python dell'host (o il venv di un altro progetto attivo nella shell) e un'altra versione di
  Poetry, che riscrive `poetry.lock` in modo diverso.
- `startproject config .`: il `.` finale evita la doppia cartella `biblioteca/biblioteca/`.
  Il nome `config` è una convenzione diffusa (Django propone il nome del progetto).
- `~=6.1.0` significa `>=6.1.0, <6.2`: accetti le patch, non la feature release successiva.

### 2.2 `config/settings.py`: configurazione dall'ambiente

📄 `backend/config/settings.py` — ✏️ **modifica**: il file l'ha generato `startproject`, cambia solo i punti indicati.

In cima:

```python
import os
from pathlib import Path
```

Sostituisci `SECRET_KEY`, `DEBUG` e `ALLOWED_HOSTS`:

```python
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

DEBUG = os.environ.get("DJANGO_DEBUG") == "1"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
```

`os.environ["X"]` (con le quadre) **esplode** se la variabile manca: per un segreto è quello che vuoi.
`os.environ.get("X", default)` per i valori con un default sensato.

Database:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['POSTGRES_DB'],
        'USER': os.environ['POSTGRES_USER'],
        'PASSWORD': os.environ['POSTGRES_PASSWORD'],
        'HOST': os.environ.get('POSTGRES_HOST', 'db'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        'CONN_MAX_AGE': 60,   # riusa la connessione per 60 s invece di aprirne una per richiesta
    }
}
```

Lingua e fuso:

```python
LANGUAGE_CODE = 'it'
TIME_ZONE = 'Europe/Rome'
```

`USE_TZ = True` (già presente) significa: nel database le date sono **in UTC**, Django le converte nel fuso
`TIME_ZONE` solo quando le mostra. Usa sempre `django.utils.timezone.now()`, mai `datetime.now()`.

### 2.3 L'utente custom, PRIMA della prima `migrate`

```bash
# web è ancora spento: run --rm, non dj/exec
docker compose run --rm web python manage.py startapp accounts
ls backend/accounts    # admin.py  apps.py  __init__.py  migrations  models.py  tests.py  views.py
```

📄 `backend/accounts/models.py` — 🔁 **sostituisci tutto** (`startapp` ha messo solo un commento):

```python
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Utente custom: va creato PRIMA della prima migrate, anche se per ora è vuoto."""
```

📄 `backend/accounts/admin.py` — 🔁 **sostituisci tutto**:

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User

admin.site.register(User, UserAdmin)
```

📄 `backend/config/settings.py` — ✏️ **modifica**: aggiungi `"accounts",` in fondo a `INSTALLED_APPS` e, subito dopo il blocco `DATABASES`:

```python
AUTH_USER_MODEL = 'accounts.User'
```

🧠 **Domanda:** perché un utente custom anche se è vuoto?
<details><summary>Risposta</summary>
<code>AUTH_USER_MODEL</code> decide a quale tabella puntano tutte le foreign key verso l'utente (admin log,
gruppi, i tuoi modelli). Cambiarlo dopo la prima <code>migrate</code> significa riscrivere a mano migrazioni e
dati. Con una classe vuota da subito, aggiungere un campo domani è una migrazione normale. È la
raccomandazione ufficiale della documentazione Django.
</details>

### 2.4 Prima migrazione e avvio

```bash
docker compose run --rm web python manage.py makemigrations accounts
docker compose run --rm web python manage.py migrate
docker compose up -d web
# da qui in poi web è acceso: valgono gli alias (dj, djpo, djtest)
dj createsuperuser          # admin / una password a scelta
docker compose logs -f web  # Ctrl+C per uscire
```

> Se `web` si ferma (errore in `settings.py`, PC riavviato...) gli alias rispondono
> `service "web" is not running`: guarda `docker compose logs web`, correggi, `docker compose up -d web`.

Il server di sviluppo (`runserver`) **si ricarica da solo** quando salvi un file `.py`: niente cache da
svuotare come in Magento. I template si rileggono a ogni richiesta con `DEBUG=1`.

### 2.5 `.gitignore` (in `django_learn/`)

📄 `django_learn/.gitignore` — 🆕 **nuovo file**

```gitignore
.env
backend/.venv/
__pycache__/
*.pyc
.pytest_cache/
```

### 2.6 Tour della struttura

```
backend/
├── manage.py            🅢 bin/console
├── pyproject.toml       🅢 composer.json
├── poetry.lock          🅢 composer.lock
├── .venv/               🅢 vendor/ (non va in git)
├── config/
│   ├── settings.py      tutta la configurazione, in Python
│   ├── urls.py          URL radice           🅢 config/routes.yaml
│   ├── wsgi.py / asgi.py punti d'ingresso per gunicorn/uvicorn   🅢 public/index.php
└── accounts/
    ├── apps.py          configurazione dell'app (AppConfig)
    ├── models.py        modelli               🅢 src/Entity
    ├── admin.py         registrazione nell'admin
    ├── views.py         viste                 🅢 src/Controller
    ├── tests.py
    └── migrations/      migrazioni generate   🅢 migrations/
```

### 2.7 Cosa sopravvive a un riavvio di Docker (o del PC)

| Cosa | Dove vive | Dopo il riavvio |
|---|---|---|
| Codice (`backend/`: app, `settings.py`...) | sul tuo disco (bind mount `./backend:/app`) | ✅ resta |
| Dipendenze (`.venv`) | `backend/.venv`, sul disco | ✅ resta |
| Database (tabelle, superuser, dati) | volume Docker `db_data` | ✅ resta |
| Cache di Poetry | volume `poetry_cache` | ✅ resta |
| Cache su Valkey | memoria del container (nessun volume) | ❌ svuotata (è una cache: va bene) |
| Email catturate da Mailpit | memoria del container | ❌ perse |

**I container non ripartono da soli:** in `compose.yaml` non c'è `restart:`, quindi dopo un riavvio restano
spenti e gli alias rispondono `service "web" is not running`. Si riaccendono con `docker compose up -d`
(è il comando quotidiano della sezione «Ogni giorno, all'avvio del PC», in cima alla guida).

> Se vuoi l'avvio automatico, aggiungi `restart: unless-stopped` a ogni servizio in `compose.yaml`.

Sicuri: `docker compose restart`, `stop`/`start`, `down`/`up -d` (eliminano i container, non i volumi),
`docker compose build` (ricostruisce solo l'immagine).

> ⚠️ **L'unico pericoloso:** `docker compose down -v`. Il `-v` cancella anche i volumi: **database perso**.
> Stesso effetto per `docker volume prune` sui volumi non agganciati a un container. Il codice resta (è
> sul disco), ma dovrai rifare `migrate` e `createsuperuser` (e il seed della Fase 6).
>
> 🅜 Come per Magento in Docker: il codice è un bind mount, MySQL vive in un volume.

✅ **Checkpoint 2:** http://localhost:8100 mostra il razzo di Django; http://localhost:8100/admin/ accetta
il login del superuser; in DBeaver (`localhost:5440`) la tabella degli utenti si chiama `accounts_user`.

---

## Fase 3: prima vista, URL e template

Una pagina "Ciao" per vedere il giro completo richiesta → URL → vista → template.

```bash
dj startapp catalog
```

📄 `backend/config/settings.py` — ✏️ **modifica**: aggiungi `"catalog",` in fondo a `INSTALLED_APPS`; poi in `TEMPLATES` cambia `"DIRS": []` in:

```python
        'DIRS': [BASE_DIR / 'templates'],
```

(i template **di progetto**, come `base.html`; quelli delle app stanno in `<app>/templates/<app>/`).

📄 `backend/catalog/views.py` — 🔁 **sostituisci tutto**. La **vista** prepara i dati (il dizionario) e sceglie il template:

```python
from django.shortcuts import render


def hello(request):
    return render(
        request,
        "catalog/hello.html",
        # "html" simula un dato non fidato (es. inserito da un utente): il template lo deve escapare
        {"name": "Django 6.1", "html": "<b>escape automatico</b>"},
    )
```

📄 `backend/catalog/urls.py` — 🆕 **nuovo file**. Solo le rotte dell'app `catalog` (niente `admin/` qui):

```python
from django.urls import path

from . import views

app_name = "catalog"  # namespace: nei template {% url 'catalog:hello' %}

urlpatterns = [
    path("", views.hello, name="hello"),
]
```

📄 `backend/config/urls.py` — 🔁 **sostituisci tutto**. URL radice: `admin/` più un `include()` per ogni app:

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("catalog.urls")),
]
```

📄 `backend/templates/base.html` — 🆕 **nuovo file** (crea la cartella `backend/templates/`). Il layout comune:

```html
<!doctype html>
<html lang="it">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}Biblioteca{% endblock %}</title>
</head>
<body>
<main>{% block content %}{% endblock %}</main>
</body>
</html>
```

📄 `backend/catalog/templates/catalog/hello.html` — 🆕 **nuovo file** (crea le cartelle). Il **template** mostra solo le variabili ricevute dalla vista (`{{ name }}`, `{{ html }}`): i dati non si scrivono qui:

```html
{% extends "base.html" %}
{% block content %}
    <h1>Ciao da {{ name }}!</h1>
    <p>{{ html }}</p>
    <p>{{ html|safe }}</p>
{% endblock %}
```

> ⚠️ **Nuova cartella `templates/` in un'app → riavvia `web`** (`docker compose restart web`). Django
> elenca le cartelle `<app>/templates/` **una volta, all'avvio**: se la crei a server acceso, ottieni
> `TemplateDoesNotExist` anche con il file al posto giusto (nella pagina d'errore vedi che ha cercato solo
> in `/app/templates`). Nuovi file in una cartella già esistente invece si vedono subito.

> Perché `catalog/templates/catalog/` con il nome ripetuto? Django cerca i template in **tutte** le app con
> un unico spazio di nomi: senza la sottocartella, due app con `list.html` si pestano i piedi.
> 🅜 Come `Learn_Library::books.phtml`, ma per convenzione di cartella.

🅢 Il linguaggio è quasi Twig: `{% extends %}`, `{% block %}`, `{{ variabile }}`, escape automatico.
Differenze: niente espressioni arbitrarie (`{{ a + b }}` non esiste: la logica sta nella vista),
i metodi si chiamano senza parentesi (`{{ book.authors.all }}`), i filtri hanno al massimo un argomento.

L'escape automatico vale per le **variabili** (`{{ html }}`): `<` diventa `&lt;`. Il filtro `|safe` lo
disattiva (🅢 `|raw` di Twig): usalo solo su HTML di cui ti fidi. Attenzione: una stringa scritta **nel
template** (`{{ "<b>ciao</b>" }}`) **non** viene escapata, perché Django la considera scritta da te.

✅ **Checkpoint 3:** http://localhost:8100 mostra "Ciao da Django 6.1!"; la prima riga mostra
`<b>escape automatico</b>` come testo (escapato), la seconda in **grassetto** (`|safe`). Cambia il testo nel
template e ricarica: cambia senza riavvii.

---
## Fase 4: il modello di dominio (8 tabelle relazionate)

### 4.1 Il modello

```
catalog                          inventory                     circulation
┌────────────┐                   ┌────────┐                    ┌──────────┐      ┌──────┐
│ Author     │◄── M2M ──┐        │ Branch │◄──────────────────│ Member   │──1:1─│ User │
└────────────┘          │        └────────┘   home_branch      └──────────┘      └──────┘
┌────────────┐     ┌────┴───┐        ▲                              ▲
│ Publisher  │◄────│  Book  │◄───┐   │ branch                       │ member
└────────────┘     └────┬───┘    │ ┌─┴──────┐   copy   ┌──────────┐ │
┌────────────┐          │        └─│  Copy  │◄─────────│   Loan   │─┘
│ Subject    │◄── M2M ──┘   book   └────────┘          └──────────┘
└────────────┘
```

- **Book** è la scheda bibliografica (titolo, ISBN, autori); **Copy** è l'oggetto fisico sullo scaffale,
  con codice a barre, sede e stato. Si prestano le **copie**, non i libri: è il punto chiave del dominio.
- **Member** è il lettore: un profilo 1-a-1 sull'utente (un bibliotecario non è per forza un lettore).
- **Loan** collega una copia a un lettore, con scadenza e data di restituzione.

```bash
dj startapp inventory
dj startapp circulation
```

📄 `backend/config/settings.py` — ✏️ **modifica**: aggiungi `"inventory",` e `"circulation",` in fondo a `INSTALLED_APPS`, e in fondo al file:

```python
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'   # id bigint (già il default dei nuovi progetti)
```

### 4.2 `catalog/models.py`

📄 `backend/catalog/models.py` — 🔁 **sostituisci tutto**

```python
from django.db import models
from django.urls import reverse


class Author(models.Model):
    name = models.CharField("nome", max_length=150)
    birth_year = models.SmallIntegerField("anno di nascita", null=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "autore"
        verbose_name_plural = "autori"
        indexes = [models.Index(fields=["name"])]

    def __str__(self) -> str:
        return self.name


class Publisher(models.Model):
    name = models.CharField("nome", max_length=150, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "editore"
        verbose_name_plural = "editori"

    def __str__(self) -> str:
        return self.name


class Subject(models.Model):
    name = models.CharField("nome", max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "soggetto"
        verbose_name_plural = "soggetti"

    def __str__(self) -> str:
        return self.name


class Book(models.Model):
    class Language(models.TextChoices):
        ITALIAN = "it", "Italiano"
        ENGLISH = "en", "Inglese"
        FRENCH = "fr", "Francese"
        GERMAN = "de", "Tedesco"
        SPANISH = "es", "Spagnolo"

    title = models.CharField("titolo", max_length=255)
    isbn = models.CharField("ISBN", max_length=13, unique=True)
    published_year = models.SmallIntegerField("anno")
    language = models.CharField("lingua", max_length=2, choices=Language, default=Language.ITALIAN)
    pages = models.PositiveSmallIntegerField("pagine", null=True, blank=True)
    publisher = models.ForeignKey(
        Publisher, on_delete=models.PROTECT, related_name="books", verbose_name="editore"
    )
    authors = models.ManyToManyField(Author, related_name="books", verbose_name="autori")
    subjects = models.ManyToManyField(Subject, related_name="books", blank=True, verbose_name="soggetti")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "libro"
        verbose_name_plural = "libri"
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["published_year"]),
        ]
        constraints = [
            models.CheckConstraint(condition=~models.Q(published_year=0), name="book_year_not_zero"),
        ]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("catalog:book_detail", args=[self.pk])
```

Cose da notare:

- **`null` vs `blank`**: `null=True` riguarda il database (colonna NULL), `blank=True` la validazione dei
  form (campo facoltativo). Per i testi si usa `blank=True` *senza* `null` (stringa vuota, non due "vuoti").
- **`on_delete=PROTECT`**: non puoi cancellare un editore che ha libri (Django solleva `ProtectedError`
  prima della query). 🅢 È il problema dell'autore con libri della 6.6 di `symfony_learn`, risolto nel modello.
- **`related_name="books"`**: il lato inverso, `publisher.books.all()`. 🅢 `mappedBy` / `inversedBy`.
- **`ManyToManyField`**: Django crea da solo la tabella intermedia `catalog_book_authors`.
- **`TextChoices`**: enum con etichetta; nel DB va `"it"`, a video `book.get_language_display()` → "Italiano".
- **`CheckConstraint`**: vincolo **nel database** (anno 0 non esiste). Il parametro si chiama `condition`
  (fino a Django 5.0 era `check`, rimosso in 6.0: molti tutorial sono vecchi).
- `reverse("catalog:book_detail", ...)` genera l'URL dal nome della rotta: la creeremo in Fase 7.

### 4.3 `inventory/models.py`

📄 `backend/inventory/models.py` — 🔁 **sostituisci tutto**

```python
from django.db import models


class Branch(models.Model):
    name = models.CharField("nome", max_length=100, unique=True)
    city = models.CharField("città", max_length=100)

    class Meta:
        ordering = ["name"]
        verbose_name = "sede"
        verbose_name_plural = "sedi"

    def __str__(self) -> str:
        return f"{self.name} ({self.city})"


class Copy(models.Model):
    """La copia fisica: un libro (Book) può averne molte, in sedi diverse."""

    class Status(models.TextChoices):
        AVAILABLE = "available", "Disponibile"
        ON_LOAN = "on_loan", "In prestito"
        REPAIR = "repair", "In riparazione"
        LOST = "lost", "Smarrita"

    book = models.ForeignKey("catalog.Book", on_delete=models.CASCADE, related_name="copies", verbose_name="libro")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="copies", verbose_name="sede")
    barcode = models.CharField("codice a barre", max_length=20, unique=True)
    shelf = models.CharField("collocazione", max_length=30)
    status = models.CharField("stato", max_length=10, choices=Status, default=Status.AVAILABLE)

    class Meta:
        ordering = ["barcode"]
        verbose_name = "copia"
        verbose_name_plural = "copie"
        indexes = [models.Index(fields=["book", "status"])]

    def __str__(self) -> str:
        return self.barcode
```

`"catalog.Book"` come **stringa**: riferimento a un modello di un'altra app senza importarlo (evita gli
import circolari). L'indice composto `(book, status)` serve alla domanda più frequente del catalogo:
"quante copie disponibili ha questo libro?".

### 4.4 `circulation/models.py`

📄 `backend/circulation/models.py` — 🔁 **sostituisci tutto**

```python
from django.conf import settings
from django.db import models
from django.utils import timezone


class Member(models.Model):
    """Il lettore: profilo collegato 1-a-1 all'utente (un bibliotecario può non essere lettore)."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="member")
    card_number = models.CharField("tessera", max_length=12, unique=True)
    home_branch = models.ForeignKey(
        "inventory.Branch", on_delete=models.PROTECT, related_name="members", verbose_name="sede"
    )
    max_loans = models.PositiveSmallIntegerField("prestiti massimi", default=5)

    class Meta:
        ordering = ["card_number"]
        verbose_name = "lettore"
        verbose_name_plural = "lettori"

    def __str__(self) -> str:
        return f"{self.card_number} {self.user.get_full_name() or self.user.username}"


class LoanQuerySet(models.QuerySet):
    def active(self):
        return self.filter(returned_at__isnull=True)

    def overdue(self):
        return self.active().filter(due_at__lt=timezone.now())


class Loan(models.Model):
    copy = models.ForeignKey("inventory.Copy", on_delete=models.PROTECT, related_name="loans", verbose_name="copia")
    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name="loans", verbose_name="lettore")
    loaned_at = models.DateTimeField("prestato il", default=timezone.now)
    due_at = models.DateTimeField("scadenza")
    returned_at = models.DateTimeField("restituito il", null=True, blank=True)
    renewals = models.PositiveSmallIntegerField("rinnovi", default=0)

    objects = LoanQuerySet.as_manager()

    class Meta:
        ordering = ["-loaned_at"]
        verbose_name = "prestito"
        verbose_name_plural = "prestiti"
        constraints = [
            # Indice UNIQUE parziale: una copia può avere UN solo prestito aperto alla volta
            models.UniqueConstraint(
                fields=["copy"], condition=models.Q(returned_at__isnull=True), name="one_open_loan_per_copy"
            ),
        ]
        indexes = [
            models.Index(fields=["member", "returned_at"]),
            models.Index(fields=["due_at"], condition=models.Q(returned_at__isnull=True), name="loan_open_due_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.copy} → {self.member}"

    @property
    def is_overdue(self) -> bool:
        return self.returned_at is None and self.due_at < timezone.now()
```

- **`settings.AUTH_USER_MODEL`**, mai `accounts.User` diretto: il codice resta valido anche se l'utente cambia.
- **`LoanQuerySet.as_manager()`**: metodi di query riutilizzabili e **concatenabili**:
  `Loan.objects.active()`, `member.loans.overdue()`, `Loan.objects.filter(...).active()`.
  🅢 Sono i metodi custom del `BookRepository`, ma componibili come i `QueryBuilder`.
- **`default=timezone.now`** senza parentesi: passi la *funzione*, chiamata a ogni nuovo prestito.
  Con le parentesi tutti i prestiti avrebbero l'ora di avvio del server (errore classico).
- **Vincolo e indice parziali** (`condition=`): PostgreSQL indicizza solo le righe che soddisfano il WHERE.
  L'indice dei prestiti aperti resta piccolo anche con milioni di prestiti chiusi.

### 4.5 Migrazioni

```bash
dj makemigrations catalog          # se non l'hai già fatto
dj makemigrations inventory        # dipende da catalog
dj makemigrations circulation      # dipende da inventory e accounts
dj sqlmigrate circulation 0001     # l'SQL che verrà eseguito
dj migrate
dj showmigrations
```

> **Perché un'app alla volta, nell'ordine delle dipendenze?** Con un solo `dj makemigrations` per tutte,
> Django non trova ancora una migrazione di `inventory` a cui agganciare le foreign key di `circulation` e
> spezza `circulation` in due file: `0001` (tabelle senza FK) e `0002` (FK, indici, vincoli). Funziona lo
> stesso, ma è più difficile da leggere e il `sqlmigrate circulation 0001` sotto non mostrerebbe gli indici.

Nel risultato di `sqlmigrate` cerca:

```sql
CREATE UNIQUE INDEX "one_open_loan_per_copy" ON "circulation_loan" ("copy_id") WHERE "returned_at" IS NULL;
CREATE INDEX "loan_open_due_idx" ON "circulation_loan" ("due_at") WHERE "returned_at" IS NULL;
```

🅢 `makemigrations` ≈ `make:migration` (confronta modelli e migrazioni esistenti, **non** il database);
`migrate` ≈ `doctrine:migrations:migrate`. Le migrazioni sono file Python in `<app>/migrations/`: vanno in git.

### 4.6 La shell: prova l'ORM

```bash
dj shell        # da Django 5.2 importa già tutti i modelli
```

```python
b = Branch.objects.create(name="Centrale", city="Milano")
p = Publisher.objects.create(name="Einaudi")
calvino = Author.objects.create(name="Italo Calvino", birth_year=1923)
book = Book.objects.create(title="Il barone rampante", isbn="9788804667926", published_year=1957, publisher=p)
book.authors.add(calvino)                    # M2M: dopo il create, perché serve l'id
Copy.objects.create(book=book, branch=b, barcode="C001", shelf="12.3")

Book.objects.filter(authors__name__icontains="calvino")   # __ attraversa le relazioni
calvino.books.count()
book.copies.filter(status=Copy.Status.AVAILABLE).exists()
print(Book.objects.filter(published_year__lt=1960).query)  # l'SQL generato
Book.objects.create(title="X", isbn="1", published_year=0, publisher=p)   # IntegrityError: il CHECK
```

🧠 **Domanda:** quando viene eseguita la query di un QuerySet?
<details><summary>Risposta</summary>
I QuerySet sono <b>lazy</b>: <code>filter()</code>, <code>exclude()</code>, <code>order_by()</code> costruiscono la
query senza eseguirla. Parte quando la iteri, la affetti con un passo, chiami <code>len()</code>,
<code>list()</code>, <code>bool()</code>, o metodi come <code>count()</code>, <code>exists()</code>,
<code>get()</code>, <code>first()</code>. Il risultato viene messo in cache nel QuerySet: iterarlo due volte
fa una sola query, ma <code>qs.filter(...)</code> ne crea uno nuovo.
</details>

✅ **Checkpoint 4:** `dj showmigrations` è tutto `[X]`; in DBeaver vedi le tabelle `catalog_*`, `inventory_*`,
`circulation_*` e `catalog_book_authors`; il CHECK sull'anno 0 rifiuta l'INSERT.

---

## Fase 5: l'admin di Django per i bibliotecari

L'admin è il punto in cui Django risparmia più lavoro: un backoffice completo generato dai modelli.
🅜 Quello che in Magento sono listing XML + form XML + data provider + controller (tutta la Fase 6 di
`magento2_learn`), qui è una classe Python per modello.

📄 `backend/catalog/admin.py` — 🔁 **sostituisci tutto**:

```python
from django.contrib import admin

from inventory.models import Copy

from .models import Author, Book, Publisher, Subject


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ["name", "birth_year"]
    search_fields = ["name"]  # obbligatorio per usarlo in autocomplete_fields


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name"]


class CopyInline(admin.TabularInline):
    model = Copy
    extra = 0
    fields = ["barcode", "branch", "shelf", "status"]


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["title", "isbn", "published_year", "language", "publisher"]
    list_filter = ["language", "subjects"]
    search_fields = ["title", "isbn"]
    # Con 100.000 autori una <select> normale caricherebbe tutto: autocomplete = ricerca AJAX
    autocomplete_fields = ["publisher", "authors", "subjects"]
    list_select_related = ["publisher"]  # niente N+1 sulla colonna editore
    inlines = [CopyInline]
    show_full_result_count = False  # niente COUNT(*) extra sulle tabelle grandi
```

📄 `backend/inventory/admin.py` — 🔁 **sostituisci tutto**:

```python
from django.contrib import admin

from .models import Branch, Copy


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ["name", "city"]


@admin.register(Copy)
class CopyAdmin(admin.ModelAdmin):
    list_display = ["barcode", "book", "branch", "shelf", "status"]
    list_filter = ["status", "branch"]
    search_fields = ["barcode", "book__title"]
    raw_id_fields = ["book"]
    list_select_related = ["book", "branch"]
```

📄 `backend/circulation/admin.py` — 🔁 **sostituisci tutto**:

```python
from django.contrib import admin

from .models import Loan, Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ["card_number", "user", "home_branch", "max_loans"]
    search_fields = ["card_number", "user__username", "user__last_name"]
    raw_id_fields = ["user"]
    list_select_related = ["user", "home_branch"]


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ["copy", "member", "loaned_at", "due_at", "returned_at"]
    list_filter = ["returned_at"]
    date_hierarchy = "loaned_at"
    raw_id_fields = ["copy", "member"]
    list_select_related = ["copy", "member__user"]
```

> **Perché tutte queste opzioni "di prestazione" già ora?** Con i dati della Fase 6, una `<select>` con
> 10.000 autori o una colonna `book` senza `list_select_related` (una query per riga) rendono l'admin
> inutilizzabile. `raw_id_fields` mostra un campo id con lente di ricerca; `autocomplete_fields` una select
> con ricerca AJAX (richiede `search_fields` sull'admin del modello collegato).

> L'admin è uno strumento **per lo staff**, non il frontend dei lettori. La documentazione Django lo dice
> esplicitamente: se devi personalizzarlo molto, scrivi le tue viste.

✅ **Checkpoint 5:** dall'admin crei sede, editore, autore, soggetto e un libro con due copie inline; il
filtro per lingua funziona; cancellare un editore con libri mostra l'errore di `PROTECT`.

---
## Fase 6: dati massivi e ORM veloce

### 6.1 Dipendenze

```bash
djpo add faker
djpo add --group dev django-debug-toolbar pytest-django factory-boy
```

`--group dev` mette i pacchetti in `[dependency-groups]` di `pyproject.toml`
(🅢 `require-dev`): in produzione si installa con `poetry install --only main`.

### 6.2 Comando di seed: `catalog/management/commands/seed_library.py`

📄 `backend/catalog/management/commands/seed_library.py` — 🆕 **nuovo file**

Crea le cartelle `catalog/management/commands/` (con Python 3 i file `__init__.py` non sono obbligatori,
ma Django li crea nelle app: aggiungili per uniformità).

```python
import random
import time

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify
from faker import Faker

from catalog.models import Author, Book, Publisher, Subject
from inventory.models import Branch, Copy

SUBJECTS = ["Narrativa", "Storia", "Filosofia", "Scienze", "Informatica", "Arte", "Ragazzi", "Poesia", "Viaggi", "Economia"]
BRANCHES = [("Centrale", "Milano"), ("Nord", "Milano"), ("Sud", "Milano"), ("Ovest", "Milano")]


class Command(BaseCommand):
    help = "Popola il catalogo con dati finti (anche centinaia di migliaia di righe)"

    def add_arguments(self, parser):
        parser.add_argument("--books", type=int, default=50_000)
        parser.add_argument("--reset", action="store_true", help="cancella prima catalogo e copie")

    @transaction.atomic
    def handle(self, *args, books: int, reset: bool, **options):
        if reset:
            Copy.objects.all().delete()
            Book.objects.all().delete()
            Author.objects.all().delete()
            Publisher.objects.all().delete()
            Subject.objects.all().delete()
            Branch.objects.all().delete()
        elif Book.objects.exists():
            raise CommandError("Il catalogo non è vuoto: usa --reset")

        start = time.monotonic()
        fake = Faker("it_IT")
        Faker.seed(42)
        random.seed(42)

        subjects = Subject.objects.bulk_create([Subject(name=n, slug=slugify(n)) for n in SUBJECTS])
        branches = Branch.objects.bulk_create([Branch(name=n, city=c) for n, c in BRANCHES])
        publishers = Publisher.objects.bulk_create([Publisher(name=fake.unique.company()) for _ in range(300)])
        authors = Author.objects.bulk_create(
            [Author(name=fake.name(), birth_year=random.randint(1800, 2000)) for _ in range(max(books // 5, 1))],
            batch_size=5000,
        )
        self.stdout.write(f"{len(authors)} autori, {len(publishers)} editori")

        # bulk_create: un INSERT ogni batch_size righe invece di uno per riga (niente save(), niente segnali)
        book_objs = Book.objects.bulk_create(
            [
                Book(
                    title=fake.sentence(nb_words=random.randint(2, 6)).rstrip("."),
                    isbn=f"978{i:010d}",
                    published_year=random.randint(1900, 2025),
                    language=random.choice(Book.Language.values),
                    pages=random.randint(80, 900),
                    publisher=random.choice(publishers),
                )
                for i in range(books)
            ],
            batch_size=5000,
        )
        self.stdout.write(f"{len(book_objs)} libri")

        # Le ManyToMany si popolano scrivendo direttamente nella tabella intermedia
        BookAuthor = Book.authors.through
        BookAuthor.objects.bulk_create(
            [BookAuthor(book_id=b.pk, author_id=random.choice(authors).pk) for b in book_objs], batch_size=10_000
        )
        BookSubject = Book.subjects.through
        BookSubject.objects.bulk_create(
            [BookSubject(book_id=b.pk, subject_id=random.choice(subjects).pk) for b in book_objs], batch_size=10_000
        )

        copies = [
            Copy(
                book_id=b.pk,
                branch=random.choice(branches),
                barcode=f"C{b.pk:08d}{n}",
                shelf=f"{random.randint(1, 99):02d}.{random.randint(1, 20)}",
            )
            for b in book_objs
            for n in range(random.randint(1, 4))
        ]
        Copy.objects.bulk_create(copies, batch_size=10_000)
        self.stdout.write(self.style.SUCCESS(f"{len(copies)} copie. Fatto in {time.monotonic() - start:.1f} s"))
```

```bash
dj seed_library --reset            # 50.000 libri, ~125.000 copie: circa 15 secondi
dj seed_library --reset --books 300000   # quando vuoi sentire davvero il peso
```

- **`@transaction.atomic`**: tutto o niente, e molto più veloce (un solo COMMIT). 🅢 `wrapInTransaction()`.
- **`bulk_create`** restituisce gli oggetti **con l'id** su PostgreSQL (usa `RETURNING`): per questo dopo
  possiamo usare `b.pk`. Non chiama `save()` e non invia segnali.
- **`Book.authors.through`**: il modello della tabella intermedia, generato da Django.
- `Faker.seed(42)`: dati diversi ma **riproducibili** a ogni esecuzione.

> Il seed non crea lettori e prestiti: li aggiungi tu in Fase 9 (esercizio).

### 6.3 Debug toolbar: vedere le query

📄 `backend/config/settings.py` — ✏️ **modifica**: aggiungi in fondo:

```python
# Debug toolbar solo in sviluppo (è nel gruppo dev di Poetry) e mai durante i test:
# pytest forza DEBUG=False, gli URL della toolbar sparirebbero ma il middleware resterebbe
TESTING = 'PYTEST_VERSION' in os.environ
if DEBUG and not TESTING:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    # In Docker la richiesta arriva dall'IP del gateway, non da 127.0.0.1: INTERNAL_IPS non basta
    DEBUG_TOOLBAR_CONFIG = {'SHOW_TOOLBAR_CALLBACK': lambda request: True}
```

📄 `backend/config/urls.py` — ✏️ **modifica**: aggiungi in fondo (l'import va in cima, con gli altri):

```python
from django.conf import settings   # in cima, con gli altri import

if settings.DEBUG and not settings.TESTING:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()
```

🅢 È il **Profiler** di Symfony: pannello SQL con query duplicate, tempi, `EXPLAIN`.

### 6.4 I cinque strumenti contro le query lente

Provali in `dj shell` (con `from django.db import connection, reset_queries` e `DEBUG=1`,
`len(connection.queries)` conta le query eseguite):

```python
# 1. N+1: 1 query per i libri + 1 per OGNI editore
for b in Book.objects.all()[:50]: b.publisher.name

# select_related: JOIN, per ForeignKey e OneToOne (relazioni "a uno")
for b in Book.objects.select_related("publisher")[:50]: b.publisher.name

# 2. prefetch_related: seconda query con IN (...), per ManyToMany e relazioni inverse ("a molti")
for b in Book.objects.prefetch_related("authors")[:50]: [a.name for a in b.authors.all()]

# 3. annotate / aggregate: calcoli nel database, non in Python
from django.db.models import Count, Q
Book.objects.annotate(n_copies=Count("copies")).filter(n_copies__gte=4).count()
Copy.objects.aggregate(total=Count("id"), available=Count("id", filter=Q(status="available")))

# 4. only / values: carica solo le colonne che servono
Book.objects.only("id", "title")[:10]
Book.objects.values_list("isbn", flat=True)[:10]

# 5. explain: il piano di PostgreSQL (cerca "Index Scan" contro "Seq Scan")
print(Book.objects.filter(published_year=1957).explain(analyze=True))
```

**Novità di Django 6.1, i *fetch mode*:** invece di ricordarti `select_related`, puoi dire al QuerySet
cosa fare quando un campo non è stato caricato:

```python
from django.db import models
for b in Book.objects.fetch_mode(models.FETCH_PEERS)[:50]:
    b.publisher.name     # al primo accesso carica l'editore di TUTTI i 50 libri: 2 query in totale
Book.objects.fetch_mode(models.FETCH_RAISE)   # ogni accesso non precaricato solleva un'eccezione
```

`FETCH_RAISE` nei test è un ottimo cane da guardia contro gli N+1.

🧠 **Domanda:** `select_related` o `prefetch_related`?
<details><summary>Risposta</summary>
<code>select_related</code> fa una <b>JOIN</b> nella stessa query: solo per relazioni che restituiscono un oggetto
(ForeignKey, OneToOne). <code>prefetch_related</code> fa una <b>query separata</b> con
<code>WHERE id IN (...)</code> e unisce i risultati in Python: per ManyToMany e relazioni inverse
(<code>book.copies</code>), dove una JOIN moltiplicherebbe le righe. Con <code>Prefetch("copies",
queryset=...)</code> puoi filtrare/ordinare la query precaricata.
🅢 In Doctrine è la differenza tra <code>JOIN ... addSelect()</code> e il fetch EXTRA_LAZY/batch.
</details>

🧠 **Domanda:** quanto costa `paginator.count` su 500.000 righe?
<details><summary>Risposta</summary>
La paginazione classica fa un <code>SELECT COUNT(*)</code> a ogni pagina: su PostgreSQL con centinaia di
migliaia di righe e filtri complessi può pesare più della query della pagina. Alternative: paginazione a
<b>cursore</b> (DRF <code>CursorPagination</code>, "carica altri" senza numero di pagine), conteggi stimati,
oppure in admin <code>show_full_result_count = False</code>.
</details>

✅ **Checkpoint 6:** `dj seed_library --reset` crea 50.000 libri; l'admin dei libri e delle copie si apre in
meno di mezzo secondo; nella debug toolbar la lista libri dell'admin fa poche query, non centinaia.

---

## Fase 7: il catalogo pubblico (class-based views)

### 7.1 Viste: `catalog/views.py`

📄 `backend/catalog/views.py` — 🔁 **sostituisci tutto** (la vista `hello` della Fase 3 sparisce)

```python
from django.db.models import Prefetch
from django.views.generic import DetailView, ListView

from inventory.models import Copy

from .models import Book, Subject


class BookListView(ListView):
    template_name = "catalog/book_list.html"
    context_object_name = "books"
    paginate_by = 25

    def get_queryset(self):
        books = Book.objects.select_related("publisher").prefetch_related("authors")
        if subject := self.request.GET.get("subject"):
            books = books.filter(subjects__slug=subject)
        if q := self.request.GET.get("q", "").strip():
            books = books.filter(title__icontains=q)   # provvisorio: in Fase 10 la ricerca vera
        return books

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subjects"] = Subject.objects.all()
        return context


class BookDetailView(DetailView):
    template_name = "catalog/book_detail.html"
    context_object_name = "book"
    queryset = Book.objects.select_related("publisher").prefetch_related(
        "authors",
        "subjects",
        Prefetch("copies", queryset=Copy.objects.select_related("branch").order_by("branch__name", "barcode")),
    )
```

Le **class-based view** sono il pattern *template method*: `ListView` sa già paginare, scegliere il
template e passare il contesto; tu sovrascrivi solo i "ganci" (`get_queryset`, `get_context_data`).
`DetailView` cerca l'oggetto per `pk` dall'URL e risponde **404** da sola se non esiste.
🅢 Sono i controller generati da `make:crud`, ma ereditati invece che copiati.

Cancella la vista `hello` e il suo template: non servono più.

### 7.2 URL: `catalog/urls.py`

📄 `backend/catalog/urls.py` — 🔁 **sostituisci tutto**

```python
from django.urls import path

from . import views

app_name = "catalog"  # namespace: nei template {% url 'catalog:book_list' %}

urlpatterns = [
    path("", views.BookListView.as_view(), name="book_list"),
    path("libri/<int:pk>/", views.BookDetailView.as_view(), name="book_detail"),
]
```

`<int:pk>` è un *path converter*: accetta solo numeri e passa `pk` come intero. 🅢 `requirements: ['id' => '\d+']`.

### 7.3 Template

📄 `backend/templates/base.html` — 🔁 **sostituisci tutto** (quello della Fase 3). È la versione **finale**: un `{% url %}` verso una
rotta che non esiste ancora dà `NoReverseMatch`, quindi per ora nel `<nav>` tieni solo il link "Catalogo";
in Fase 8 aggiungi il ramo `{% if user.is_authenticated %}` con il form di logout e "Accedi", in Fase 9 i due
link ai prestiti.

```html
<!doctype html>
<html lang="it">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}Biblioteca{% endblock %}</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 60rem; margin: 0 auto; padding: 1rem; }
        nav { display: flex; gap: 1rem; align-items: center; border-bottom: 1px solid #ccc; padding-bottom: .5rem; }
        nav form { margin-left: auto; }
        table { border-collapse: collapse; width: 100%; }
        th, td { text-align: left; padding: .3rem; border-bottom: 1px solid #eee; }
        .success { color: green; } .error, .errorlist { color: #b00; }
    </style>
</head>
<body>
<nav>
    <a href="{% url 'catalog:book_list' %}">Catalogo</a>
    {% if user.is_authenticated %}
        <a href="{% url 'circulation:my_loans' %}">I miei prestiti</a>
        {% if perms.circulation.add_loan %}<a href="{% url 'circulation:desk' %}">Banco prestiti</a>{% endif %}
        {# Da Django 5.0 il logout accetta solo POST (protezione CSRF) #}
        <form method="post" action="{% url 'logout' %}">{% csrf_token %}
            {{ user.username }} <button>Esci</button>
        </form>
    {% else %}
        <a href="{% url 'login' %}" style="margin-left:auto">Accedi</a>
    {% endif %}
</nav>
{% for message in messages %}<p class="{{ message.tags }}">{{ message }}</p>{% endfor %}
<main>{% block content %}{% endblock %}</main>
</body>
</html>
```

Lo stile è volutamente minimo: l'aspetto lo decidiamo in Fase 14.

📄 `backend/catalog/templates/catalog/book_list.html` — 🆕 **nuovo file**:

```html
{% extends "base.html" %}
{% block title %}Catalogo{% endblock %}
{% block content %}
<h1>Catalogo</h1>

<form method="get">
    <input type="search" name="q" value="{{ request.GET.q }}" placeholder="Cerca un titolo">
    <select name="subject">
        <option value="">Tutti i soggetti</option>
        {% for s in subjects %}
            <option value="{{ s.slug }}" {% if s.slug == request.GET.subject %}selected{% endif %}>{{ s.name }}</option>
        {% endfor %}
    </select>
    <button>Filtra</button>
</form>

<table>
    <thead><tr><th>Titolo</th><th>Autori</th><th>Editore</th><th>Anno</th></tr></thead>
    <tbody>
    {% for book in books %}
        <tr>
            <td><a href="{{ book.get_absolute_url }}">{{ book.title }}</a></td>
            <td>{{ book.authors.all|join:", " }}</td>
            <td>{{ book.publisher }}</td>
            <td>{{ book.published_year }}</td>
        </tr>
    {% empty %}
        <tr><td colspan="4">Nessun libro trovato.</td></tr>
    {% endfor %}
    </tbody>
</table>

{% if is_paginated %}
    {# {% querystring %} (Django 5.1+) tiene q e subject dell'URL attuale e cambia solo page #}
    <p>
        {% if page_obj.has_previous %}<a href="{% querystring page=page_obj.previous_page_number %}">« Precedente</a>{% endif %}
        Pagina {{ page_obj.number }} di {{ page_obj.paginator.num_pages }}
        {% if page_obj.has_next %}<a href="{% querystring page=page_obj.next_page_number %}">Successiva »</a>{% endif %}
    </p>
{% endif %}
{% endblock %}
```

> **Il tag `{% querystring %}`** risolve un problema classico: a pagina 2 i filtri spariscono. I vecchi
> tutorial concatenano `"&q="|add:request.GET.q`, che con `q` assente **va in errore 500**.

📄 `backend/catalog/templates/catalog/book_detail.html` — 🆕 **nuovo file**:

```html
{% extends "base.html" %}
{% block title %}{{ book.title }}{% endblock %}
{% block content %}
<h1>{{ book.title }}</h1>
<p>
    {{ book.authors.all|join:", " }} · {{ book.publisher }} · {{ book.published_year }} ·
    {{ book.get_language_display }}{% if book.pages %} · {{ book.pages }} pagine{% endif %}<br>
    ISBN {{ book.isbn }} · {{ book.subjects.all|join:", " }}
</p>

<h2>Copie</h2>
<table>
    <thead><tr><th>Codice</th><th>Sede</th><th>Collocazione</th><th>Stato</th></tr></thead>
    <tbody>
    {% for copy in book.copies.all %}
        <tr><td>{{ copy.barcode }}</td><td>{{ copy.branch }}</td><td>{{ copy.shelf }}</td><td>{{ copy.get_status_display }}</td></tr>
    {% endfor %}
    </tbody>
</table>
{% endblock %}
```

`book.authors.all` nel template **non** fa una query per libro, perché la vista ha usato `prefetch_related`:
verificalo nella debug toolbar togliendo il prefetch (25 query in più).

✅ **Checkpoint 7:** http://localhost:8100 elenca i libri 25 per pagina; filtro per soggetto e ricerca
restano attivi cambiando pagina; il dettaglio mostra le copie con sede; `/libri/999999/` dà 404; la lista
fa **4 query** (conteggio per la paginazione, soggetti, libri con editore, autori) indipendentemente dai
libri mostrati, il dettaglio altre 4 (libro, autori, soggetti, copie con sede).

---
## Fase 8: login, gruppi e permessi

### 8.1 Le viste di autenticazione già pronte

📄 `backend/config/urls.py` — ✏️ **modifica**: aggiungi in `urlpatterns`:

```python
    path("accounts/", include("django.contrib.auth.urls")),  # login, logout, cambio e reset password
```

📄 `backend/config/settings.py` — ✏️ **modifica**: aggiungi in fondo:

```python
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'catalog:book_list'
LOGOUT_REDIRECT_URL = 'catalog:book_list'
```

📄 `backend/templates/registration/login.html` — 🆕 **nuovo file** (Django lo cerca proprio lì):

```html
{% extends "base.html" %}
{% block title %}Accedi{% endblock %}
{% block content %}
<h1>Accedi</h1>
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <input type="hidden" name="next" value="{{ next }}">
    <button>Accedi</button>
</form>
{% endblock %}
```

🅢 È `security.yaml` con `form_login`, senza scriverlo: utenti, hash delle password (PBKDF2 di default,
Argon2 con un pacchetto in più), sessioni e CSRF sono già nel framework. Il **logout è solo POST**
(da Django 5.0): un `<a href>` di logout restituisce 405, per questo in `base.html` è un form.

### 8.2 Permessi e gruppi

Per ogni modello Django crea quattro permessi: `add_`, `change_`, `delete_`, `view_` (es. `circulation.add_loan`).
Si assegnano a utenti o, meglio, a **gruppi**. 🅢 Sono i ruoli, ma più granulari (per modello e azione).

Il gruppo "Bibliotecari" lo creiamo con una **migrazione di dati**, così esiste in ogni ambiente:

```bash
dj makemigrations accounts --empty -n librarians_group
```

Sostituisci il contenuto del file generato (`accounts/migrations/0002_librarians_group.py`):

```python
from django.contrib.auth.management import create_permissions
from django.db import migrations

PERMISSIONS = ["add_loan", "change_loan", "view_loan", "view_member", "view_copy", "change_copy"]


def create_group(apps, schema_editor):
    # I permessi vengono creati dopo TUTTE le migrazioni (segnale post_migrate):
    # su un database nuovo qui non esisterebbero ancora, quindi li creiamo noi
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, verbosity=0)
        app_config.models_module = None

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    group, _ = Group.objects.get_or_create(name="Bibliotecari")
    group.permissions.set(Permission.objects.filter(codename__in=PERMISSIONS))


def delete_group(apps, schema_editor):
    apps.get_model("auth", "Group").objects.filter(name="Bibliotecari").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("circulation", "0001_initial"),
        ("inventory", "0001_initial"),
    ]

    operations = [migrations.RunPython(create_group, delete_group)]
```

- **`apps.get_model(...)`** e non `from django.contrib.auth.models import Group`: la migrazione deve usare
  il modello *com'era in quel punto della storia*, non quello di oggi.
- La seconda funzione rende la migrazione **reversibile** (`dj migrate accounts 0001`).
- 🅜 È una *data patch* (`Setup/Patch/Data`) di Magento.

```bash
dj migrate
```

Poi dall'admin crea due utenti: `bibliotecario` (nel gruppo Bibliotecari, **senza** "staff") e `lettore`
(con nome ed email), e per `lettore` un **Lettore** (Member) con tessera `M0000001`.

### 8.3 Proteggere le viste

| Strumento | Dove | Effetto |
|---|---|---|
| `LoginRequiredMixin` | class-based view | anonimo → redirect al login con `?next=` |
| `PermissionRequiredMixin` + `permission_required = "app.codename"` | class-based view | senza permesso → **403** |
| `@login_required`, `@permission_required` | function view | come sopra |
| `{% if perms.circulation.add_loan %}` | template | mostra/nasconde un link (non è sicurezza!) |
| `user.has_perm("circulation.add_loan")` | codice | controllo esplicito |

Le useremo in Fase 9. 🅢 `#[IsGranted('ROLE_...')]` e `is_granted()` in Twig.

🧠 **Domanda:** `is_staff`, `is_superuser` e i permessi: che differenza c'è?
<details><summary>Risposta</summary>
<code>is_staff</code> permette solo di <b>entrare</b> nell'admin. <code>is_superuser</code> ha tutti i permessi
senza assegnarli. I <b>permessi</b> decidono cosa si può fare su ogni modello (in admin e nelle tue viste).
Un bibliotecario può avere i permessi sui prestiti senza essere staff: userà il banco prestiti, non l'admin.
</details>

✅ **Checkpoint 8:** login e logout funzionano (il nome utente appare nel `<nav>`); `/accounts/logout/` aperto
come link dà 405; il gruppo Bibliotecari ha 6 permessi (admin → Gruppi).

---

## Fase 9: i prestiti (logica di dominio, transazioni, concorrenza)

### 9.1 Il servizio: `circulation/services.py`

📄 `backend/circulation/services.py` — 🆕 **nuovo file**

Le regole di prestito **non** vanno nella vista (ci sarà anche l'API) né nel `save()` del modello (troppo
nascoste): vanno in un modulo di servizio, funzioni normali che viste, API, comandi e test chiamano.

```python
"""Regole di dominio dei prestiti: le usano le viste HTML, l'API e i test (come un service Symfony)."""

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from inventory.models import Copy

from .models import Loan, Member

LOAN_DAYS = 30
MAX_RENEWALS = 2


class LoanError(Exception):
    """Regola di prestito violata: il messaggio è pensato per l'utente."""


@transaction.atomic
def lend(*, barcode: str, card_number: str) -> Loan:
    try:
        # select_for_update: SELECT ... FOR UPDATE, la riga resta bloccata fino al COMMIT.
        # Due bibliotecari che prestano la stessa copia nello stesso istante: il secondo aspetta e poi la trova ON_LOAN.
        copy = Copy.objects.select_for_update().get(barcode=barcode)
    except Copy.DoesNotExist:
        raise LoanError(f"Nessuna copia con codice {barcode}.") from None
    try:
        member = Member.objects.get(card_number=card_number)
    except Member.DoesNotExist:
        raise LoanError(f"Nessun lettore con tessera {card_number}.") from None

    if copy.status != Copy.Status.AVAILABLE:
        raise LoanError(f"La copia {barcode} non è disponibile ({copy.get_status_display()}).")
    if member.loans.overdue().exists():
        raise LoanError("Il lettore ha prestiti scaduti: prima deve restituirli.")
    if member.loans.active().count() >= member.max_loans:
        raise LoanError(f"Il lettore ha già {member.max_loans} prestiti aperti.")

    copy.status = Copy.Status.ON_LOAN
    copy.save(update_fields=["status"])
    return Loan.objects.create(copy=copy, member=member, due_at=timezone.now() + timedelta(days=LOAN_DAYS))


@transaction.atomic
def return_copy(*, barcode: str) -> Loan:
    try:
        loan = Loan.objects.select_for_update().active().select_related("copy").get(copy__barcode=barcode)
    except Loan.DoesNotExist:
        raise LoanError(f"La copia {barcode} non risulta in prestito.") from None

    loan.returned_at = timezone.now()
    loan.save(update_fields=["returned_at"])
    loan.copy.status = Copy.Status.AVAILABLE
    loan.copy.save(update_fields=["status"])
    return loan
```

- **`*,` nella firma**: argomenti solo per nome (`lend(barcode=..., card_number=...)`), impossibile
  scambiarli per errore.
- **`@transaction.atomic`**: se una riga fallisce, si annulla tutto (copia e prestito restano coerenti).
- **Tre livelli di difesa** contro il doppio prestito: il controllo `status` (messaggio chiaro), il
  `select_for_update` (concorrenza) e l'indice UNIQUE parziale della Fase 4 (ultima garanzia, nel DB).
- **`save(update_fields=[...])`**: aggiorna solo quella colonna, non riscrive tutta la riga.
- `from None` nasconde l'eccezione originale (`DoesNotExist`) dal traceback: è un errore *atteso*.

🅢 È un servizio Symfony senza container: lo importi (`from circulation import services`). Nei test non
serve un mock del container: si testa con un database vero (Fase 13).

### 9.2 Form: `circulation/forms.py`

📄 `backend/circulation/forms.py` — 🆕 **nuovo file**

```python
from django import forms


class LendForm(forms.Form):
    barcode = forms.CharField(label="Codice a barre della copia", max_length=20)
    card_number = forms.CharField(label="Tessera del lettore", max_length=12)


class ReturnForm(forms.Form):
    barcode = forms.CharField(label="Codice a barre della copia", max_length=20)
```

Un `Form` (non `ModelForm`): i campi non corrispondono a un modello, sono l'input del banco prestiti.

### 9.3 Viste: `circulation/views.py`

📄 `backend/circulation/views.py` — 🔁 **sostituisci tutto**

```python
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView

from . import services
from .forms import LendForm, ReturnForm
from .models import Loan


class MyLoansView(LoginRequiredMixin, ListView):
    template_name = "circulation/my_loans.html"
    context_object_name = "loans"

    def get_queryset(self):
        # Solo i prestiti dell'utente collegato: mai fidarsi di un id passato nell'URL
        return Loan.objects.filter(member__user=self.request.user).select_related("copy__book")


class DeskFormView(PermissionRequiredMixin, FormView):
    """Base per il banco prestiti: solo chi ha il permesso (gruppo Bibliotecari)."""

    success_url = reverse_lazy("circulation:desk")

    def form_valid(self, form):
        try:
            message = self.perform(form.cleaned_data)
        except services.LoanError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
        messages.success(self.request, message)
        return super().form_valid(form)


class LendView(DeskFormView):
    permission_required = "circulation.add_loan"
    form_class = LendForm
    template_name = "circulation/desk.html"

    def perform(self, data) -> str:
        loan = services.lend(barcode=data["barcode"], card_number=data["card_number"])
        return f"Prestito registrato: {loan.copy} a {loan.member}, scadenza {loan.due_at:%d/%m/%Y}."


class ReturnView(DeskFormView):
    permission_required = "circulation.change_loan"
    form_class = ReturnForm
    template_name = "circulation/return.html"

    def perform(self, data) -> str:
        loan = services.return_copy(barcode=data["barcode"])
        return f"Restituzione registrata: {loan.copy}."
```

- **`form.add_error(None, ...)`**: errore "non di campo", mostrato in cima al form.
- **`messages.success`**: il flash message che sopravvive al redirect. 🅢 `addFlash()`.
- **`reverse_lazy`**: `reverse` valutato più tardi; serve negli attributi di classe, letti all'import
  quando gli URL non sono ancora caricati.
- **Post/Redirect/Get**: `form_valid` fa redirect a `success_url`, così F5 non ripete il prestito.

📄 `backend/circulation/urls.py` — 🆕 **nuovo file**:

```python
from django.urls import path

from . import views

app_name = "circulation"

urlpatterns = [
    path("miei-prestiti/", views.MyLoansView.as_view(), name="my_loans"),
    path("banco/", views.LendView.as_view(), name="desk"),
    path("banco/restituzione/", views.ReturnView.as_view(), name="return"),
]
```

📄 `backend/config/urls.py` — ✏️ **modifica**: aggiungi in `urlpatterns`:

```python
    path("prestiti/", include("circulation.urls")),
```

Django prova i pattern **in ordine** e si ferma al primo che corrisponde. `include("catalog.urls")` montato
su `""` non "cattura tutto": corrisponde solo se uno dei suoi pattern interni combacia. L'ordine conta solo
quando due pattern possono descrivere lo stesso URL.

### 9.4 Template

📄 `backend/circulation/templates/circulation/desk.html` — 🆕 **nuovo file** (crea le cartelle):

```html
{% extends "base.html" %}
{% block title %}Banco prestiti{% endblock %}
{% block content %}
<h1>Nuovo prestito</h1>
<p><a href="{% url 'circulation:return' %}">Registra una restituzione</a></p>
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button>Presta</button>
</form>
{% endblock %}
```

📄 `backend/circulation/templates/circulation/return.html` — 🆕 **nuovo file**: uguale, con titolo "Restituzione", link a
`circulation:desk` ("Torna ai prestiti") e pulsante "Restituisci".

📄 `backend/circulation/templates/circulation/my_loans.html` — 🆕 **nuovo file**:

```html
{% extends "base.html" %}
{% block title %}I miei prestiti{% endblock %}
{% block content %}
<h1>I miei prestiti</h1>
<table>
    <thead><tr><th>Libro</th><th>Copia</th><th>Prestato il</th><th>Scadenza</th><th>Restituito</th></tr></thead>
    <tbody>
    {% for loan in loans %}
        <tr>
            <td>{{ loan.copy.book }}</td>
            <td>{{ loan.copy }}</td>
            <td>{{ loan.loaned_at|date:"d/m/Y" }}</td>
            <td {% if loan.is_overdue %}class="error"{% endif %}>{{ loan.due_at|date:"d/m/Y" }}</td>
            <td>{{ loan.returned_at|date:"d/m/Y"|default:"—" }}</td>
        </tr>
    {% empty %}
        <tr><td colspan="5">Nessun prestito.</td></tr>
    {% endfor %}
    </tbody>
</table>
{% endblock %}
```

### 9.5 Esercizi

1. **Rinnovo**: `services.renew(*, loan_id, member)` che sposta `due_at` di `LOAN_DAYS`, al massimo
   `MAX_RENEWALS` volte, rifiutato se il prestito è scaduto. Pulsante in "I miei prestiti" (form POST).
2. **Prenotazioni**: modello `Reservation(book, member, created_at, fulfilled_at)`. Si prenota un **libro**
   (non una copia) quando nessuna copia è disponibile; alla restituzione, se c'è una prenotazione aperta,
   la copia va in stato "riservata" invece che "disponibile". Serve un nuovo valore in `Copy.Status`:
   prova a capire perché `makemigrations` genera una migrazione anche se nel DB non cambia nulla.
3. **Seed dei lettori**: estendi il seed (o crea `seed_circulation`) con 5.000 lettori e 20.000 prestiti
   storici, usando `bulk_create` anche per gli utenti (`make_password` una volta sola, è lenta).

🧠 **Domanda:** perché `select_for_update` e non basta controllare lo stato?
<details><summary>Risposta</summary>
Tra il SELECT che legge "disponibile" e l'UPDATE passano millisecondi: due richieste parallele possono
leggere entrambe "disponibile" (race condition, <i>check-then-act</i>). <code>SELECT ... FOR UPDATE</code>
blocca la riga: la seconda transazione aspetta il COMMIT della prima e poi legge lo stato aggiornato.
Funziona solo dentro una transazione (<code>atomic</code>), altrimenti Django solleva un errore.
L'indice UNIQUE parziale resta l'ultima difesa, anche contro codice che non passa dal servizio.
</details>

🧠 **Domanda:** fat models, services o signals?
<details><summary>Risposta</summary>
Il "fat model" (logica nei metodi del modello) va bene per regole che riguardano <b>un solo oggetto</b>
(<code>loan.is_overdue</code>). Le operazioni che toccano più modelli e hanno regole di business vanno in
<b>servizi</b> espliciti. I <b>signals</b> (<code>post_save</code>) sono comodi per disaccoppiare app diverse,
ma nascondono il flusso: chi legge <code>lend()</code> non vede cosa succede dopo. Si usano con parsimonia,
soprattutto per integrazioni (cache, indicizzazione), mai per regole di dominio.
</details>

✅ **Checkpoint 9:** il bibliotecario presta una copia (messaggio verde con scadenza); prestare di nuovo la
stessa copia dà "non è disponibile"; tessera sbagliata dà errore; il lettore la vede in "I miei prestiti";
la restituzione la rimette disponibile; il lettore su `/prestiti/banco/` riceve **403**, un anonimo su
`/prestiti/miei-prestiti/` viene mandato al login.

---
## Fase 10: ricerca full-text con PostgreSQL

`title__icontains` diventa `WHERE UPPER(title) LIKE UPPER('%rosa%')`: nessun indice lo aiuta, legge tutta la
tabella, e non capisce che "romanzi" e "romanzo" sono la stessa parola. Su 500.000 libri serve altro.
🅜 Magento usa OpenSearch; per un catalogo come il nostro **PostgreSQL basta**: full-text con stemming
italiano e trigrammi per gli errori di battitura, senza un servizio in più.

### 10.1 `django.contrib.postgres` e l'estensione `pg_trgm`

📄 `backend/config/settings.py` — ✏️ **modifica**: aggiungi `"django.contrib.postgres",` a `INSTALLED_APPS` (dopo le app `django.contrib.*`).

```bash
dj makemigrations catalog --empty -n pg_extensions
```

Contenuto di `catalog/migrations/0002_pg_extensions.py`:

```python
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
    ]

    # CREATE EXTENSION pg_trgm: serve prima di creare l'indice gin_trgm_ops
    operations = [TrigramExtension()]
```

### 10.2 Colonna di ricerca generata e indici GIN

📄 `backend/catalog/models.py` — ✏️ **modifica**: aggiungi gli import in cima:

```python
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
```

Sempre in `backend/catalog/models.py`, in `Author.Meta.indexes`:

```python
            # trigrammi: ricerca tollerante agli errori di battitura
            GinIndex(fields=["name"], name="author_name_trgm", opclasses=["gin_trgm_ops"]),
```

Sempre in `backend/catalog/models.py`, nella classe `Book`, dopo `created_at`:

```python
    # Colonna calcolata da PostgreSQL: si aggiorna da sola quando cambia il titolo
    search_vector = models.GeneratedField(
        expression=SearchVector("title", config="italian"),
        output_field=SearchVectorField(),
        db_persist=True,
    )
```

e in `Book.Meta.indexes`:

```python
            GinIndex(fields=["search_vector"], name="book_search_gin"),
```

```bash
dj makemigrations catalog -n book_search
dj sqlmigrate catalog 0003
dj migrate
```

L'SQL mostra il cuore della soluzione:

```sql
ALTER TABLE "catalog_book" ADD COLUMN "search_vector" tsvector
    GENERATED ALWAYS AS (to_tsvector('italian'::regconfig, COALESCE("title", ''))) STORED;
CREATE INDEX "book_search_gin" ON "catalog_book" USING gin ("search_vector");
```

- **`GeneratedField`** (Django 5.0+): colonna calcolata **dal database**. Niente trigger, niente segnali,
  niente `save()` da ricordare: anche il `bulk_create` del seed la riempie.
- **`tsvector`**: il titolo ridotto a radici di parole italiane ("romanzi" → "romanz") senza parole vuote.
- **Indice GIN**: indice invertito (parola → righe), come quello di un motore di ricerca.
- Gli autori non entrano nella colonna generata (sono in un'altra tabella). Esercizio: cercarli con i
  trigrammi e unire i risultati.

### 10.3 La vista

📄 `backend/catalog/views.py` — ✏️ **modifica**: gli import in cima diventano:

```python
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Prefetch
```

e, sempre in `backend/catalog/views.py`, in `BookListView.get_queryset` sostituisci il blocco `if q := ...`:

```python
        if q := self.request.GET.get("q", "").strip():
            # Full-text PostgreSQL con stemming italiano ("romanzi" trova "romanzo")
            query = SearchQuery(q, config="italian", search_type="websearch")
            books = books.filter(search_vector=query).annotate(rank=SearchRank(F("search_vector"), query))
            books = books.order_by("-rank", "title")
```

`search_type="websearch"` accetta la sintassi dei motori di ricerca: `amore -guerra`, `"frase esatta"`, `a or b`.

Trigrammi in shell:

```python
from django.contrib.postgres.search import TrigramSimilarity
Author.objects.annotate(sim=TrigramSimilarity("name", "Calvno")).filter(sim__gt=0.3).order_by("-sim")[:5]
Author.objects.filter(name__trigram_similar="Calvno")[:5]     # stesso effetto con l'operatore %
```

🧠 **Domanda:** quando PostgreSQL non basta più e serve OpenSearch/Elasticsearch?
<details><summary>Risposta</summary>
Quando servono faccette con conteggi su molti campi in tempo reale, ricerca su più lingue e campi con pesi
complessi, sinonimi gestiti dal business, "did you mean", volumi di decine di milioni di documenti o carico
di ricerca che non deve pesare sul database transazionale. Il prezzo: un servizio in più e la sincronizzazione
dei dati (indexer, code), cioè quello che fa Magento. Per un catalogo da centinaia di migliaia di righe,
<code>tsvector</code> + GIN + trigrammi coprono quasi tutto.
</details>

✅ **Checkpoint 10:** la ricerca trova parole anche al plurale/singolare; in `dj shell`,
`Book.objects.filter(search_vector=SearchQuery("amore", config="italian")).explain()` mostra
`Bitmap Index Scan on book_search_gin`; la ricerca trigram trova un autore anche con una lettera sbagliata
(il seed `--reset` ha cancellato Calvino: ricrealo dall'admin o usa un nome generato dal seed) e il suo
`.explain()` usa `author_name_trgm`.

---

## Fase 11: API REST con Django REST framework

🅢 DRF è l'equivalente di Serializer + controller JSON (o di API Platform); 🅜 delle Web API generate dai
service contracts. Dà paginazione, filtri, autenticazione, permessi, validazione e una **API navigabile**
dal browser.

### 11.1 Installazione

```bash
djpo add "djangorestframework~=3.18" django-filter
dj startapp api
```

In `backend/api/` cancella `models.py`, `admin.py`, `tests.py` e la cartella `migrations/` (l'app non ha modelli).
📄 `backend/config/settings.py` — ✏️ **modifica**: in fondo a `INSTALLED_APPS` aggiungi `"rest_framework"`, `"rest_framework.authtoken"`, `"django_filters"`, `"api"`.

📄 `backend/config/settings.py` — ✏️ **modifica**: aggiungi in fondo:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # Token per primo: senza credenziali la risposta è 401 con "WWW-Authenticate: Token".
        # Con Session per prima sarebbe 403 (la sessione non ha un header da proporre)
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticatedOrReadOnly'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}
```

```bash
dj migrate      # tabella dei token
```

### 11.2 Serializer: `api/serializers.py`

📄 `backend/api/serializers.py` — 🆕 **nuovo file**

```python
from rest_framework import serializers

from catalog.models import Author, Book, Publisher
from circulation.models import Loan


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "birth_year"]


class BookSerializer(serializers.ModelSerializer):
    # Lettura: autori annidati. Scrittura: solo gli id (come i gruppi di serializzazione in Symfony)
    authors = AuthorSerializer(many=True, read_only=True)
    author_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, source="authors", queryset=Author.objects.all()
    )
    publisher = serializers.PrimaryKeyRelatedField(queryset=Publisher.objects.all())
    publisher_name = serializers.CharField(source="publisher.name", read_only=True)
    available_copies = serializers.IntegerField(read_only=True)  # arriva dall'annotate del ViewSet

    class Meta:
        model = Book
        fields = [
            "id", "title", "isbn", "published_year", "language", "pages",
            "publisher", "publisher_name", "authors", "author_ids", "subjects", "available_copies",
        ]

    def validate_published_year(self, value: int) -> int:
        if value == 0 or not -3000 <= value <= 2100:
            raise serializers.ValidationError("Anno non valido (da -3000 a 2100, senza lo 0).")
        return value


class LoanSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source="copy.book.title", read_only=True)
    barcode = serializers.CharField(source="copy.barcode", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Loan
        fields = ["id", "book_title", "barcode", "loaned_at", "due_at", "returned_at", "is_overdue"]
```

- Il serializer fa **due lavori**: oggetto → JSON (lettura) e JSON → dati validati → oggetto (scrittura).
  🅢 Normalizer + Validator + DTO di input in una classe.
- **`validate_<campo>`**: validazione di un campo; `validate(self, attrs)` per le regole tra più campi.
- I `ModelSerializer` ereditano già i vincoli del modello: ISBN `unique` → 400 automatico se duplicato.

### 11.3 ViewSet e permessi

📄 `backend/api/permissions.py` — 🆕 **nuovo file**:

```python
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsStaffOrReadOnly(BasePermission):
    """GET/HEAD/OPTIONS per tutti, scrittura solo per lo staff."""

    def has_permission(self, request, view) -> bool:
        return request.method in SAFE_METHODS or bool(request.user and request.user.is_staff)
```

📄 `backend/api/views.py` — 🔁 **sostituisci tutto**:

```python
from django.db.models import Count, Q
from rest_framework import generics, permissions, viewsets

from catalog.models import Author, Book
from circulation.models import Loan
from inventory.models import Copy

from .permissions import IsStaffOrReadOnly
from .serializers import AuthorSerializer, BookSerializer, LoanSerializer


class BookViewSet(viewsets.ModelViewSet):
    """list, retrieve, create, update, partial_update, destroy: un controller REST completo."""

    serializer_class = BookSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["language", "publisher", "subjects"]  # ?language=it&subjects=3
    search_fields = ["title", "isbn"]                          # ?search=rosa
    ordering_fields = ["title", "published_year"]              # ?ordering=-published_year

    def get_queryset(self):
        return (
            Book.objects.select_related("publisher")
            .prefetch_related("authors", "subjects")
            .annotate(available_copies=Count("copies", filter=Q(copies__status=Copy.Status.AVAILABLE)))
            .order_by("title", "id")
        )


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsStaffOrReadOnly]
    search_fields = ["name"]


class MyLoansView(generics.ListAPIView):
    serializer_class = LoanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Loan.objects.filter(member__user=self.request.user).select_related("copy__book")
```

`order_by("title", "id")`: con la paginazione l'ordinamento deve essere **univoco**, altrimenti due libri
con lo stesso titolo possono comparire su due pagine (o su nessuna).

📄 `backend/api/urls.py` — 🆕 **nuovo file**:

```python
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("books", views.BookViewSet, basename="book")
router.register("authors", views.AuthorViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("me/loans/", views.MyLoansView.as_view(), name="my-loans"),
    path("token/", obtain_auth_token, name="api-token"),
]
```

📄 `backend/config/urls.py` — 🔁 **sostituisci tutto** (versione completa a questo punto):

```python
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),  # login, logout, cambio password
    path("api/", include("api.urls")),
    path("prestiti/", include("circulation.urls")),
    path("", include("catalog.urls")),
]

if settings.DEBUG and not settings.TESTING:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()
```

`basename="book"` serve perché il ViewSet ha `get_queryset()` e non un attributo `queryset` da cui
dedurre il nome delle rotte (`book-list`, `book-detail`).

### 11.4 Prova con curl

```bash
# Pubblico: lista, filtri, ricerca, ordinamento
curl -s 'localhost:8100/api/books/?search=amore&ordering=-published_year' | python3 -m json.tool | head -40
curl -s 'localhost:8100/api/books/?language=en&page=2' | python3 -m json.tool | head -20
curl -s localhost:8100/api/books/1/ | python3 -m json.tool

# Token (crealo per un utente con password)
TOKEN=$(curl -s -X POST localhost:8100/api/token/ -d username=lettore -d 'password=LA_PASSWORD' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["token"])')
curl -s -H "Authorization: Token $TOKEN" localhost:8100/api/me/loans/ | python3 -m json.tool

# Scrittura senza credenziali → 401; con il token del lettore (non staff) → 403
curl -s -o /dev/null -w '%{http_code}\n' -X POST localhost:8100/api/books/ -d title=x
```

Apri anche http://localhost:8100/api/books/ nel browser: è l'API navigabile, con form per il POST se sei
loggato come staff.

🧠 **Domanda:** sessione o token per un'API?
<details><summary>Risposta</summary>
La <b>sessione</b> (cookie) va bene per un frontend sullo <b>stesso dominio</b> servito da Django: richiede il
token CSRF nelle richieste di scrittura. Il <b>token</b> (header <code>Authorization</code>) serve a client
esterni: app mobile, integrazioni, SPA su un altro dominio. Il token di DRF non scade: in produzione si usano
spesso JWT (<code>djangorestframework-simplejwt</code>) con scadenza e refresh, o OAuth2.
</details>

✅ **Checkpoint 11:** la lista è paginata a 20 con `count`, `next`, `previous`; `available_copies` è corretto;
il POST anonimo dà 401, quello di un non-staff 403, quello dello staff 201; un anno `0` dà 400 con il messaggio
italiano; `/api/me/loans/` mostra solo i prestiti di chi fa la richiesta.

---

## Fase 12: task in background, email e cache

### 12.1 Email verso Mailpit

`startproject` ha già messo in `settings.py` il nuovo setting **`MAILERS`** (Django 6.1, sostituisce
`EMAIL_BACKEND`, `EMAIL_HOST`... ora deprecati). Cambialo così:

```python
MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
        'OPTIONS': {'host': 'mailpit', 'port': 1025},
    },
}
DEFAULT_FROM_EMAIL = 'Biblioteca <biblioteca@example.com>'
```

Prova in `dj shell`:

```python
from django.core.mail import send_mail
send_mail("Prova", "Ciao dalla biblioteca", None, ["io@example.com"])
```

e guarda http://localhost:8036.

### 12.2 Il Tasks framework (Django 6.0+)

Spedire email dentro una richiesta HTTP è lento e fragile (se l'SMTP è giù, la pagina va in errore).
Si mette il lavoro **in coda** e lo esegue un processo separato, il *worker*.
🅢 Messenger con un transport; 🅜 message queue + consumer.

Django 6.0 ha introdotto l'API standard dei task (`@task`, `.enqueue()`), ma **non** un worker: i backend
integrati sono solo `ImmediateBackend` (esegue subito, per lo sviluppo) e `DummyBackend` (per i test).
Per una coda vera usiamo `django-tasks-db`, che salva i task in una tabella PostgreSQL.

```bash
djpo add django-tasks-db
```

`INSTALLED_APPS`: `'django_tasks_db',`. In `settings.py`:

```python
TASKS = {
    'default': {
        'BACKEND': 'django_tasks_db.DatabaseBackend',
        'QUEUES': ['default'],
    }
}
```

```bash
dj migrate
```

📄 `backend/circulation/tasks.py` — 🆕 **nuovo file**:

```python
from django.core.mail import send_mail
from django.tasks import task

from .models import Loan


@task
def send_due_reminder(loan_id: int) -> str:
    # Si passa l'id, non l'oggetto: gli argomenti di un task devono essere serializzabili in JSON
    loan = Loan.objects.select_related("member__user", "copy__book").get(pk=loan_id)
    user = loan.member.user
    send_mail(
        subject=f"Promemoria: restituisci «{loan.copy.book}»",
        message=f"Ciao {user.first_name or user.username},\n"
        f"il prestito di «{loan.copy.book}» scade il {loan.due_at:%d/%m/%Y}.",
        from_email=None,  # DEFAULT_FROM_EMAIL
        recipient_list=[user.email],
    )
    return user.email
```

📄 `backend/circulation/management/commands/send_due_reminders.py` — 🆕 **nuovo file** (crea le cartelle, con `__init__.py` come in Fase 6):

```python
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from circulation.models import Loan
from circulation.tasks import send_due_reminder


class Command(BaseCommand):
    help = "Mette in coda un promemoria per i prestiti che scadono entro N giorni"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=3)

    def handle(self, *args, days: int, **options):
        limit = timezone.now() + timedelta(days=days)
        loan_ids = (
            Loan.objects.active()
            .filter(due_at__lte=limit, member__user__email__gt="")
            .values_list("id", flat=True)
        )
        for loan_id in loan_ids.iterator():
            send_due_reminder.enqueue(loan_id)  # ritorna subito: la mail la spedisce il worker
        self.stdout.write(self.style.SUCCESS(f"{len(loan_ids)} promemoria in coda"))
```

Il worker in `compose.yaml` (stessa immagine, comando diverso):

```yaml
  worker:
    image: django-learn:py3.14
    container_name: dj_worker
    env_file: .env
    volumes:
      - ./backend:/app
    command: ["python", "manage.py", "db_worker"]
    depends_on:
      db:
        condition: service_healthy
```

```bash
docker compose up -d worker
# presta una copia, poi in dj shell porta la scadenza a domani:
#   Loan.objects.filter(pk=ID).update(due_at=timezone.now() + timedelta(days=1))
dj send_due_reminders
docker compose logs worker      # "state=SUCCESSFUL"
```

e l'email arriva in Mailpit. Il worker **non** si ricarica quando cambi il codice: dopo una modifica a
`tasks.py`, `docker compose restart worker`.

> **Chi lancia `send_due_reminders` ogni mattina?** Il Tasks framework non ha (ancora) uno scheduler.
> In produzione: cron o un timer systemd che esegue il comando, oppure Celery con `celery beat`.
> 🅜 È il `crontab.xml` di Magento, ma fuori da Django.

🧠 **Domanda:** perché passare `loan_id` e non l'oggetto `loan`?
<details><summary>Risposta</summary>
Gli argomenti finiscono in una coda (qui una tabella) come JSON: un'istanza di modello non è serializzabile,
e anche se lo fosse sarebbe una fotografia vecchia. Il worker gira più tardi, magari dopo minuti: deve
rileggere lo stato attuale dal database. Stessa regola in Celery e in Messenger.
Se il task parte da una transazione, va accodato con <code>transaction.on_commit(...)</code>: altrimenti
il worker potrebbe cercare un prestito che non è ancora stato committato.
</details>

### 12.3 Cache su Valkey

```bash
djpo add redis
```

Il client si chiama `redis` ma parla con Valkey (stesso protocollo). In `settings.py`:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://valkey:6379/0',
    }
}
```

Statistiche del catalogo: contare 125.000 copie a ogni pagina è inutile, cambiano poco.
📄 `backend/catalog/views.py` — ✏️ **modifica**: gli import in cima diventano:

```python
from django.core.cache import cache
from django.db.models import Count, F, Prefetch, Q
```

e, sempre in `backend/catalog/views.py`, in `BookListView` sostituisci `get_context_data` e aggiungi `_stats`:

```python
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subjects"] = Subject.objects.all()
        context["stats"] = cache.get_or_set("catalog_stats", self._stats, timeout=300)
        return context

    @staticmethod
    def _stats() -> dict:
        return Copy.objects.aggregate(
            total=Count("id"), available=Count("id", filter=Q(status=Copy.Status.AVAILABLE))
        )
```

📄 `backend/catalog/templates/catalog/book_list.html` — ✏️ **modifica**: sotto `<h1>Catalogo</h1>` aggiungi:

```html
<p>{{ stats.available }} copie disponibili su {{ stats.total }}.</p>
```

`get_or_set` passa la **funzione** (`self._stats`, senza parentesi): viene chiamata solo se la chiave non
c'è. Verifica: `docker compose exec valkey valkey-cli keys '*'` mostra `:1:catalog_stats`.

Altri livelli di cache da conoscere: `@cache_page(60)` su una vista intera, `{% cache 300 nome %}` nei
template, `SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"` per le sessioni.

🧠 **Domanda:** come invalidi una cache quando i dati cambiano?
<details><summary>Risposta</summary>
Tre strategie: <b>scadenza</b> (timeout: accetti dati vecchi per N secondi, la più semplice), <b>invalidazione
esplicita</b> (<code>cache.delete("catalog_stats")</code> nel servizio che presta/restituisce, o con un signal
<code>post_save</code>), <b>chiavi versionate</b> (la chiave include un numero di versione o un
<code>updated_at</code>: cambiando il dato cambia la chiave). 🅜 Magento usa i <i>cache tag</i>: ogni voce
ha dei tag, salvare un modello pulisce tutte le voci con il suo tag.
</details>

✅ **Checkpoint 12:** l'email di prova arriva in Mailpit; `dj send_due_reminders` mette in coda i promemoria
e il worker li spedisce (`SUCCESSFUL` nei log, email in Mailpit); la home mostra le statistiche e la seconda
richiesta non esegue la query di conteggio delle copie (debug toolbar).

---
## Fase 13: test con pytest

Django ha un suo test runner (`dj test`, basato su `unittest`); nei progetti moderni si usa quasi sempre
**pytest** con `pytest-django`: test come funzioni, `assert` normali, fixture. 🅢 PHPUnit + `KernelTestCase`.

### 13.1 Configurazione

📄 `backend/pyproject.toml` — ✏️ **modifica**: aggiungi in fondo:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
python_files = ["test_*.py"]
```

pytest-django crea un database `test_library` vuoto, applica le migrazioni e lo distrugge alla fine; ogni
test gira in una transazione annullata. L'utente PostgreSQL deve poter creare database (quello
dell'immagine ufficiale è superuser: ok).

### 13.2 Factory: `conftest.py` (nella radice di `backend/`)

📄 `backend/conftest.py` — 🆕 **nuovo file**

```python
import factory
import pytest
from factory.django import DjangoModelFactory

from accounts.models import User
from catalog.models import Book, Publisher
from circulation.models import Member
from inventory.models import Branch, Copy


class PublisherFactory(DjangoModelFactory):
    class Meta:
        model = Publisher

    name = factory.Sequence(lambda n: f"Editore {n}")


class BookFactory(DjangoModelFactory):
    class Meta:
        model = Book

    title = factory.Faker("sentence", nb_words=4)
    isbn = factory.Sequence(lambda n: f"978{n:010d}")
    published_year = 1990
    publisher = factory.SubFactory(PublisherFactory)


class BranchFactory(DjangoModelFactory):
    class Meta:
        model = Branch
        django_get_or_create = ["name"]

    name = "Centrale"
    city = "Milano"


class CopyFactory(DjangoModelFactory):
    class Meta:
        model = Copy

    book = factory.SubFactory(BookFactory)
    branch = factory.SubFactory(BranchFactory)
    barcode = factory.Sequence(lambda n: f"T{n:06d}")
    shelf = "01.1"


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"utente{n}")
    email = factory.LazyAttribute(lambda u: f"{u.username}@example.com")


class MemberFactory(DjangoModelFactory):
    class Meta:
        model = Member

    user = factory.SubFactory(UserFactory)
    card_number = factory.Sequence(lambda n: f"T{n:08d}")
    home_branch = factory.SubFactory(BranchFactory)


@pytest.fixture
def copy():
    return CopyFactory()


@pytest.fixture
def member():
    return MemberFactory()
```

`conftest.py` è caricato automaticamente da pytest: le **fixture** definite qui (`copy`, `member`) si
ricevono come parametri dei test. 🅢 Le factory sono le fixture di Foundry/Doctrine, ma create nel test.

### 13.3 Test del servizio: `circulation/tests/test_services.py`

📄 `backend/circulation/tests/test_services.py` — 🆕 **nuovo file**

Cancella `circulation/tests.py` e crea la cartella `circulation/tests/` con un `__init__.py` vuoto.

```python
from datetime import timedelta

import pytest
from django.utils import timezone

from circulation import services
from circulation.models import Loan
from conftest import CopyFactory
from inventory.models import Copy

pytestmark = pytest.mark.django_db


def test_lend_marks_copy_on_loan(copy, member):
    loan = services.lend(barcode=copy.barcode, card_number=member.card_number)

    copy.refresh_from_db()
    assert copy.status == Copy.Status.ON_LOAN
    assert loan.due_at > timezone.now() + timedelta(days=29)


def test_cannot_lend_a_copy_already_on_loan(copy, member):
    services.lend(barcode=copy.barcode, card_number=member.card_number)

    with pytest.raises(services.LoanError, match="non è disponibile"):
        services.lend(barcode=copy.barcode, card_number=member.card_number)


def test_max_loans(member):
    member.max_loans = 2
    member.save()
    for c in CopyFactory.create_batch(2):
        services.lend(barcode=c.barcode, card_number=member.card_number)

    with pytest.raises(services.LoanError, match="già 2 prestiti"):
        services.lend(barcode=CopyFactory().barcode, card_number=member.card_number)


def test_overdue_loans_block_new_loans(copy, member):
    loan = services.lend(barcode=copy.barcode, card_number=member.card_number)
    Loan.objects.filter(pk=loan.pk).update(due_at=timezone.now() - timedelta(days=1))

    with pytest.raises(services.LoanError, match="scaduti"):
        services.lend(barcode=CopyFactory().barcode, card_number=member.card_number)


def test_return_makes_copy_available(copy, member):
    services.lend(barcode=copy.barcode, card_number=member.card_number)

    loan = services.return_copy(barcode=copy.barcode)

    copy.refresh_from_db()
    assert loan.returned_at is not None
    assert copy.status == Copy.Status.AVAILABLE
```

`pytestmark = pytest.mark.django_db`: senza, pytest-django **vieta** l'accesso al database (per tenere
veloci i test che non ne hanno bisogno).

### 13.4 Test dell'API: `api/tests/test_books.py`

📄 `backend/api/tests/test_books.py` — 🆕 **nuovo file**

Crea `api/tests/__init__.py` vuoto.

```python
import pytest
from rest_framework.test import APIClient

from conftest import BookFactory, CopyFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_list_books_is_public_and_counts_available_copies(django_assert_num_queries):
    book = BookFactory()
    CopyFactory.create_batch(2, book=book)
    BookFactory.create_batch(3)

    # Il numero di query NON deve crescere con i libri: COUNT + libri + autori + soggetti = 4
    with django_assert_num_queries(4):
        response = APIClient().get("/api/books/")

    assert response.status_code == 200
    assert response.data["count"] == 4
    by_id = {b["id"]: b for b in response.data["results"]}
    assert by_id[book.id]["available_copies"] == 2


def test_create_book_requires_staff():
    payload = {"title": "Nuovo", "isbn": "9780000000001", "published_year": 2000,
               "publisher": BookFactory().publisher_id, "author_ids": []}
    client = APIClient()

    assert client.post("/api/books/", payload, format="json").status_code == 401

    client.force_authenticate(UserFactory(is_staff=True))
    response = client.post("/api/books/", payload, format="json")
    assert response.status_code == 201, response.data


def test_year_zero_is_rejected():
    client = APIClient()
    client.force_authenticate(UserFactory(is_staff=True))
    payload = {"title": "X", "isbn": "9780000000002", "published_year": 0,
               "publisher": BookFactory().publisher_id, "author_ids": []}

    response = client.post("/api/books/", payload, format="json")

    assert response.status_code == 400
    assert "published_year" in response.data
```

```bash
djtest            # 8 passed
djtest -k lend -v # solo i test con "lend" nel nome
```

> **Esperimento:** togli `"subjects"` dal `prefetch_related` del `BookViewSet` e rilancia. Il test fallisce
> con *"Expected to perform 4 queries but 7 were done"*: il serializer legge `subjects` di ogni libro, una
> query per libro. È un N+1 vero che durante la scrittura di questa guida **solo il test ha trovato**.
> `django_assert_num_queries` è il modo più economico per proteggere le prestazioni nel tempo.

🧠 **Domanda:** perché la debug toolbar va esclusa durante i test?
<details><summary>Risposta</summary>
Il test runner forza <code>DEBUG=False</code> anche se il <code>.env</code> dice 1. <code>settings.py</code> però è
già stato letto con <code>DEBUG=True</code>: il middleware della toolbar è installato mentre i suoi URL (aggiunti
solo con <code>settings.DEBUG</code>) no, e ogni risposta va in errore con <code>KeyError: 'djdt'</code>. Da qui
la variabile <code>TESTING</code> della Fase 6.
</details>

✅ **Checkpoint 13:** `djtest` → `8 passed`; l'esperimento sul prefetch fa fallire il test giusto.

---

## Fase 14: il frontend (lo decidiamo insieme)

Il backend è completo: pagine server-side (Fasi 7-9) e API REST (Fase 11). Per il frontend ci sono strade
diverse, con costi e benefici diversi: le trovi confrontate in **[FRONTEND.md](FRONTEND.md)**.
Leggilo, poi ne parliamo e scriviamo insieme le fasi del frontend scelto.

---

## Fase 15: verso la produzione

> Questa fase non è ancora stata eseguita nel progetto di prova: la verifichiamo insieme quando ci arrivi.

| Sviluppo | Produzione |
|---|---|
| `runserver` (single thread, ricarica automatica) | **gunicorn** (WSGI) o **uvicorn**/gunicorn+uvicorn worker (ASGI), dietro nginx |
| `DEBUG=1` | `DEBUG=0`: niente traceback all'utente, niente debug toolbar |
| statici serviti da Django | `collectstatic` + nginx o **WhiteNoise** |
| `SECRET_KEY` di sviluppo | segreto vero dall'ambiente / secret manager |
| `poetry install` | `poetry install --only main` nell'immagine (fallisce se `poetry.lock` non è allineato) |

```bash
dj check --deploy        # elenca le impostazioni di sicurezza mancanti (HSTS, cookie secure, ...)
```

Da preparare: `STATIC_ROOT`, `CSRF_TRUSTED_ORIGINS`, `SECURE_PROXY_SSL_HEADER` dietro un proxy HTTPS,
`SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE`, logging su stdout, `CONN_MAX_AGE` o un pool di connessioni
(`OPTIONS: {"pool": True}` con psycopg 3), un'immagine Docker multi-stage senza i tool di sviluppo,
le migrazioni lanciate **una volta** per deploy (non da ogni container).

🧠 **Domanda:** WSGI o ASGI?
<details><summary>Risposta</summary>
<b>WSGI</b> è l'interfaccia sincrona classica: un worker gestisce una richiesta alla volta (gunicorn con N
processi/thread). <b>ASGI</b> è asincrona: serve per WebSocket, streaming, long polling e viste
<code>async def</code> che aspettano molto I/O esterno. Django supporta entrambe; l'ORM ha API async
(<code>await Book.objects.aget(...)</code>) ma le query restano sincrone dietro le quinte. Per un'applicazione
CRUD come la nostra, WSGI con gunicorn è la scelta semplice e solida.
</details>

---

## Ripasso per il colloquio

<details><summary>Ciclo di vita di una richiesta in Django</summary>
gunicorn/runserver → <code>WSGIHandler</code> → <b>middleware</b> in ordine (security, sessioni, CSRF,
autenticazione, messaggi...) → <b>URL resolver</b> (<code>ROOT_URLCONF</code>, primo <code>path()</code> che
corrisponde) → <b>vista</b> → risposta (spesso <code>TemplateResponse</code>, renderizzata alla fine) →
middleware in ordine inverso → client. Le eccezioni non gestite diventano 500 (404 per
<code>Http404</code>, 403 per <code>PermissionDenied</code>).
🅢 Kernel → listener <code>kernel.request</code> → router → controller → <code>kernel.response</code>.
</details>

<details><summary>Middleware vs signals</summary>
Il <b>middleware</b> avvolge ogni richiesta/risposta (autenticazione, header, timing): è una funzione che
riceve <code>get_response</code> e restituisce un callable. I <b>signals</b> sono eventi del framework
(<code>pre_save</code>, <code>post_save</code>, <code>post_delete</code>, <code>request_finished</code>,
<code>post_migrate</code>) a cui si collegano ricevitori: sincroni, nella stessa transazione, invisibili a chi
legge il codice che salva. <code>bulk_create</code> e <code>update()</code> <b>non</b> inviano signal.
</details>

<details><summary>Migrazioni: comandi da sapere</summary>
<code>makemigrations</code> (genera), <code>migrate</code> (applica), <code>migrate app 0003</code> (torna
indietro), <code>sqlmigrate</code> (mostra l'SQL), <code>showmigrations</code>, <code>squashmigrations</code>
(comprime la storia), <code>makemigrations --check</code> (in CI: fallisce se manca una migrazione),
<code>RunPython</code> e <code>RunSQL</code> per dati e SQL a mano. Conflitti tra branch:
<code>makemigrations --merge</code>.
</details>

<details><summary>Sicurezza integrata</summary>
CSRF (token nei form POST, <code>{% csrf_token %}</code>), XSS (escape automatico nei template,
<code>|safe</code> e <code>mark_safe</code> da usare con cautela), SQL injection (l'ORM parametrizza; attenzione a
<code>raw()</code> ed <code>extra()</code> con stringhe concatenate), clickjacking (<code>X-Frame-Options</code>),
hash delle password con salt, <code>ALLOWED_HOSTS</code> contro l'Host header injection, e da Django 6.0
la Content Security Policy integrata.
</details>

<details><summary>Transazioni</summary>
Di default Django è in <b>autocommit</b>: ogni query è una transazione. <code>transaction.atomic</code>
(decoratore o <code>with</code>) apre una transazione; annidata diventa un savepoint.
<code>ATOMIC_REQUESTS = True</code> avvolge ogni vista in una transazione (comodo, ma lunga quanto la richiesta).
<code>transaction.on_commit()</code> per azioni che devono partire solo dopo il COMMIT (email, task).
</details>

<details><summary>ORM: F, Q, annotate, aggregate, subquery</summary>
<code>F("campo")</code> riferisce una colonna nel DB (<code>update(renewals=F("renewals") + 1)</code> evita la
race condition di leggere e riscrivere). <code>Q(a) | Q(b)</code>, <code>~Q(...)</code> per OR e NOT.
<code>annotate</code> aggiunge un valore per riga, <code>aggregate</code> riduce a un dizionario.
<code>Subquery</code> + <code>OuterRef</code> per le sottoquery correlate, <code>Exists</code> per i filtri
"ha almeno un...".
</details>

<details><summary>Django vs FastAPI vs Flask</summary>
<b>Django</b>: tutto incluso (ORM, admin, auth, migrazioni), ideale per gestionali e siti con database
relazionale. <b>FastAPI</b>: solo API, asincrono, validazione con Pydantic e OpenAPI automatico; ORM e auth
li scegli tu (SQLAlchemy, Alembic). <b>Flask</b>: micro-framework minimale. Molte aziende usano Django per
il backoffice e il dominio, FastAPI per microservizi API ad alto carico.
</details>

<details><summary>Cosa è cambiato da Django 4 a 6.1</summary>
5.0: <code>GeneratedField</code>, <code>db_default</code>, choices come enum diretto, form field group.
5.1: tag <code>{% querystring %}</code>, <code>LoginRequiredMiddleware</code>, pool di connessioni PostgreSQL.
5.2 (LTS): chiavi primarie composite, import automatico dei modelli nella shell.
6.0: Tasks framework, CSP integrata, template partials, Python ≥ 3.12, rimosso <code>CheckConstraint(check=)</code>.
6.1: fetch mode (<code>FETCH_PEERS</code>, <code>FETCH_RAISE</code>), <code>DB_CASCADE</code> sulle FK,
<code>MAILERS</code>, annuncio del calendar versioning.
</details>

---

## Troubleshooting

| Sintomo | Causa probabile | Soluzione |
|---|---|---|
| `KeyError: 'DJANGO_SECRET_KEY'` (o `POSTGRES_DB`) all'avvio | `.env` mancante o variabile non scritta | crea/correggi `.env`, poi `docker compose up -d --force-recreate web` |
| `service "web" is not running` con `dj`/`djpo` | gli alias usano `exec`, ma `web` è spento (o è crashato) | prima della Fase 2.4 usa `docker compose run --rm web ...`; dopo `docker compose logs web` e `docker compose up -d web` |
| Dopo un riavvio del PC/Docker gli alias non funzionano | i container non ripartono da soli (nessun `restart:`) | `docker compose up -d` (Fase 2.7) |
| Database vuoto, superuser sparito | è stato lanciato `docker compose down -v` (volume `db_data` cancellato) | `dj migrate`, `dj createsuperuser`, rilancia il seed |
| `dj: command not found` | alias non caricati | aggiungili a `~/.bashrc` (Fase 1.6) e `source ~/.bashrc` |
| `could not translate host name "db"` | comando lanciato fuori da Docker o `db` spento | usa gli alias; `docker compose up -d db` |
| `Permission denied` scrivendo in `backend/` | cartella creata da Docker come root | `sudo chown -R $(id -u):$(id -g) backend` |
| `No module named 'xyz'` dopo `poetry add` | il worker/il server girano con il venv vecchio | `docker compose restart web worker` |
| `pyproject.toml changed significantly since poetry.lock was last generated` | hai modificato `pyproject.toml` a mano | `djpo lock`, poi `djpo install` |
| `No file/folder found for package biblioteca` | manca `package-mode = false` | aggiungilo in `[tool.poetry]` (Fase 2.1) |
| Le modifiche a `tasks.py` non hanno effetto | il worker non si ricarica da solo | `docker compose restart worker` |
| `NoReverseMatch` in un template | `{% url %}` verso un nome inesistente o senza namespace | controlla `app_name` e `name=` in `urls.py` |
| `TemplateDoesNotExist` | percorso sbagliato, oppure cartella `<app>/templates/` creata a server acceso | `<app>/templates/<app>/file.html`; `DIRS` per `templates/` di progetto; `docker compose restart web` |
| `KeyError: 'djdt'` nei test | debug toolbar attiva durante i test | variabile `TESTING` della Fase 6 |
| `Database access not allowed` in pytest | manca il marker | `pytestmark = pytest.mark.django_db` |
| `django.db.utils.ProgrammingError: relation ... does not exist` | migrazione non applicata | `dj migrate`; se manca il file, `dj makemigrations` |
| `operator class "gin_trgm_ops" does not exist` | estensione `pg_trgm` non creata | migrazione `TrigramExtension` (Fase 10.1) prima dell'indice |
| Logout con un link → 405 | da Django 5.0 il logout è solo POST | form con `{% csrf_token %}` |
| Debug toolbar non appare | `INTERNAL_IPS` non corrisponde all'IP Docker | `SHOW_TOOLBAR_CALLBACK` della Fase 6 |
| 403 CSRF su un form | manca `{% csrf_token %}` o cookie bloccato | aggiungilo dentro `<form method="post">` |

---

## Piano consigliato

| Giorno | Fasi | Tempo |
|---|---|---|
| 1 | 0, 1, 2, 3 | 3 h |
| 2 | 4, 5 | 3 h |
| 3 | 6, 7 | 3-4 h |
| 4 | 8, 9 (con esercizi) | 4 h |
| 5 | 10, 11 | 3-4 h |
| 6 | 12, 13 | 3 h |
| 7+ | 14 (frontend), 15, ripasso | da definire insieme |
