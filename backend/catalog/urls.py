from django.urls import path

from . import views

app_name = "catalog"  # namespace: nei template {% url 'catalog:hello' %}

urlpatterns = [
    path("", views.hello, name="hello"),
]
