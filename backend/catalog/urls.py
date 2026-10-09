from django.urls import path

from . import views

app_name = "catalog"  # namespace: nei template {% url 'catalog:book_list' %}

urlpatterns = [
    path("", views.BookListView.as_view(), name="book_list"),
    path("libri/<int:pk>/", views.BookDetailView.as_view(), name="book_detail"),
]
