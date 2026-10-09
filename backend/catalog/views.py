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
            books = books.filter(
                title__icontains=q
            )  # provvisorio: in Fase 10 la ricerca vera
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
        Prefetch(
            "copies",
            queryset=Copy.objects.select_related("branch").order_by(
                "branch__name", "barcode"
            ),
        ),
    )
