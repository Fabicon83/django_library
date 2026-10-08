from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Utente custom: va creato PRIMA della prima migrate, anche se per ora è vuoto."""
