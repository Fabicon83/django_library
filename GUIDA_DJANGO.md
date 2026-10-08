# Guida Introduttiva a Django

Guida base, copertura ampia, per studio framework Django. Esempi minimi, concetti chiave.

---

## 1. Cos'è Django

Framework web Python, "batteries-included". Filosofia MVT (Model-View-Template), simile a MVC:

- **Model**: dati, ORM, database.
- **View**: logica, riceve richiesta, ritorna risposta.
- **Template**: HTML, presentazione.

Più componenti extra: admin automatico, routing URL, form, autenticazione, migrazioni DB.

---

## 2. Setup progetto

```bash
pip install django
django-admin startproject config .
python manage.py startapp accounts
```

Struttura tipica:

```
config/
  settings.py   # configurazione globale
  urls.py       # routing principale
  wsgi.py/asgi.py  # entry point server
accounts/
  models.py     # tabelle DB
  views.py      # logica richieste
  urls.py       # routing app (da creare)
  admin.py      # registrazione admin
  migrations/   # storico schema DB
manage.py       # CLI comandi
```

Un progetto = config globale. Un'app = modulo funzionale (es. `accounts`, `blog`, `shop`). Progetto può contenere più app.

---

## 3. Comandi essenziali (`manage.py`)

```bash
python manage.py runserver          # avvia server dev (localhost:8000)
python manage.py makemigrations     # genera file migrazione da modifiche ai model
python manage.py migrate            # applica migrazioni al DB
python manage.py createsuperuser    # crea utente admin
python manage.py shell              # shell Python con contesto Django caricato
python manage.py startapp nome      # crea nuova app
python manage.py test               # esegue test
```

---

## 4. Settings principali (`settings.py`)

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "accounts",          # ogni app va registrata qui
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",  # o sqlite3, mysql
        "NAME": "mydb",
    }
}

MIDDLEWARE = [...]        # pipeline elaborazione richiesta/risposta
ROOT_URLCONF = "config.urls"
TEMPLATES = [...]
STATIC_URL = "static/"    # CSS/JS/immagini
```

Nel tuo progetto, nota: `SECRET_KEY` e `DEBUG` letti da variabili d'ambiente (`os.environ`), buona pratica per non versionare segreti.

---

## 5. Models — definire i dati

```python
# accounts/models.py
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile({self.user.username})"
```

Campi comuni: `CharField`, `TextField`, `IntegerField`, `BooleanField`, `DateTimeField`, `ForeignKey`, `ManyToManyField`, `OneToOneField`.

Dopo ogni modifica a `models.py`:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Query ORM (al posto di SQL)

```python
Profile.objects.all()
Profile.objects.filter(bio__icontains="python")
Profile.objects.get(id=1)
Profile.objects.create(user=u, bio="ciao")
p.save()
p.delete()
Profile.objects.order_by("-created_at")
```

---

## 6. Views — la logica

Due stili: **function-based** (FBV) e **class-based** (CBV).

```python
# accounts/views.py
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

def hello(request):
    return HttpResponse("Ciao mondo")

def profile_detail(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    return render(request, "accounts/profile_detail.html", {"profile": profile})
```

```python
from django.views.generic import ListView

class ProfileListView(ListView):
    model = Profile
    template_name = "accounts/profile_list.html"
    context_object_name = "profiles"
```

CBV generiche utili: `ListView`, `DetailView`, `CreateView`, `UpdateView`, `DeleteView`.

---

## 7. URL routing

```python
# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.hello, name="hello"),
    path("profile/<int:pk>/", views.profile_detail, name="profile-detail"),
]
```

```python
# config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
]
```

`name="..."` permette riferimento nei template con `{% url 'profile-detail' pk=1 %}` invece di hardcodare path.

---

## 8. Template

```html
<!-- accounts/templates/accounts/profile_detail.html -->
{% extends "base.html" %}

{% block content %}
  <h1>{{ profile.user.username }}</h1>
  <p>{{ profile.bio|default:"Nessuna bio" }}</p>

  {% if profile.bio %}
    <p>Bio presente</p>
  {% endif %}

  <ul>
    {% for item in some_list %}
      <li>{{ item }}</li>
    {% endfor %}
  </ul>
{% endblock %}
```

Tag comuni: `{% extends %}`, `{% block %}`, `{% for %}`, `{% if %}`, `{% url %}`, `{% csrf_token %}`. Filtri: `{{ valore|upper }}`, `{{ data|date:"d/m/Y" }}`.

---

## 9. Admin automatico

```python
# accounts/admin.py
from django.contrib import admin
from .models import Profile

admin.site.register(Profile)
```

Dopo `createsuperuser`, interfaccia CRUD già pronta su `/admin/`. Ottimo per gestire dati senza scrivere view.

---

## 10. Form

```python
# accounts/forms.py
from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["bio"]
```

```python
def edit_profile(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    form = ProfileForm(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("profile-detail", pk=pk)
    return render(request, "accounts/edit.html", {"form": form})
```

```html
<form method="post">
  {% csrf_token %}
  {{ form.as_p }}
  <button type="submit">Salva</button>
</form>
```

---

## 11. Autenticazione

Django include sistema utenti pronto (`django.contrib.auth`):

```python
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

@login_required
def dashboard(request):
    return render(request, "dashboard.html")
```

CBV equivalente: `LoginRequiredMixin`.

---

## 12. Migrazioni — concetto chiave

Le migrazioni sono il "git" dello schema DB: ogni modifica ai model genera un file che descrive come trasformare il DB.

```bash
python manage.py makemigrations   # genera file in accounts/migrations/
python manage.py migrate          # applica al DB reale
python manage.py sqlmigrate accounts 0001   # mostra SQL generato
python manage.py showmigrations   # stato migrazioni
```

Mai modificare manualmente il DB senza passare da una migrazione: si perde la sincronia tra codice e schema.

---

## 13. Django REST Framework (se progetto API, come il tuo)

Visto che il progetto ha `accounts` come app e pare orientato a backend/API, probabile uso di DRF:

```bash
pip install djangorestframework
```

```python
# serializers.py
from rest_framework import serializers
from .models import Profile

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = "__all__"

# views.py
from rest_framework.viewsets import ModelViewSet

class ProfileViewSet(ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

# urls.py
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register("profiles", ProfileViewSet)
urlpatterns = [path("api/", include(router.urls))]
```

Un `ModelViewSet` dà gratis: list, create, retrieve, update, delete via HTTP.

---

## 14. Test

```python
# accounts/tests.py
from django.test import TestCase
from .models import Profile

class ProfileTests(TestCase):
    def test_str(self):
        p = Profile.objects.create(bio="test")
        self.assertIn("Profile", str(p))
```

```bash
python manage.py test
```

---

## 15. Flusso di una richiesta (riassunto mentale)

```
Browser → urls.py (routing) → views.py (logica) → models.py (query DB)
                                     ↓
                            template.html (render) → Browser
```

Middleware intercetta richiesta/risposta ad ogni passaggio (auth, CSRF, sicurezza, ecc.).

---

## 16. Buone pratiche da subito

- Un'app Django = una responsabilità (es. `accounts`, `orders`, `catalog`), non un monolite.
- `settings.py`: mai secret key o credenziali hardcoded, usare variabili ambiente (il tuo progetto già lo fa).
- Sempre eseguire `makemigrations` + `migrate` dopo modifiche ai model, e **committare i file di migrazione** nel repo.
- Usare `get_object_or_404` invece di `try/except` manuale.
- Preferire CBV generiche quando il caso è standard (CRUD), FBV quando la logica è specifica.
- Non mettere query/logica business nei template: solo presentazione.
- File `requirements.txt` o `pyproject.toml` (il tuo caso, con Poetry) per pinnare dipendenze.

---

## 17. Percorso di studio consigliato

1. Models + ORM + migrazioni (capire come i dati vivono nel DB).
2. Views (FBV) + URL routing + template base.
3. Admin (per velocizzare test manuali dei dati).
4. Form (gestione input utente).
5. Autenticazione (`auth`, login/logout, permessi).
6. CBV generiche (ListView, DetailView, ecc.).
7. Django REST Framework, se l'obiettivo è un'API (il tuo progetto sembra backend API).
8. Test automatici.
9. Deploy (ASGI/WSGI, static files, variabili ambiente, Docker — hai già `compose.yml` e `docker/`).

---

## 18. Risorse ufficiali

- Documentazione: https://docs.djangoproject.com/
- Tutorial ufficiale (polls app): https://docs.djangoproject.com/en/stable/intro/tutorial01/
- Django REST Framework: https://www.django-rest-framework.org/
