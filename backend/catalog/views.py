from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Prefetch
from django.views.generic import DetailView, ListView

from inventory.models import Copy

from .models import Author, Book, Subject


class BookListView(ListView):
    template_name = "catalog/book_list.html"
    context_object_name = "books"
    paginate_by = 25
    AUTHOR_SEARCH_MIN_LENGTH = 3

    def get_queryset(self):
        books = (
            Book.objects.select_related("publisher").prefetch_related("authors")
            # search_vector serve nel WHERE e in SearchRank, non al template: non leggerla
            .defer("search_vector")
        )
        if subject := self.request.GET.get("subject"):
            books = books.filter(subjects__slug=subject)
        if q := self.request.GET.get("q", "").strip():
            # Full-text PostgreSQL con stemming italiano ("romanzi" trova "romanzo").
            # websearch: sintassi da motore di ricerca (amore -guerra, "frase esatta", a or b)
            query = SearchQuery(q, config="italian", search_type="websearch")
            # Due ricerche indipendenti, ognuna con il proprio indice GIN:
            # titolo → full-text (search_vector @@ query, book_search_gin);
            # autore → trigrammi (author_name_trgm) sulla tabella intermedia libro↔autore
            book_ids = Book.objects.filter(search_vector=query).values("pk")
            # Sotto le 3 lettere i trigrammi sono rumore ("il" troverebbe tutte le "Ilaria"):
            # la ricerca per autore parte solo da AUTHOR_SEARCH_MIN_LENGTH caratteri
            if len(q) >= self.AUTHOR_SEARCH_MIN_LENGTH:
                author_ids = Book.authors.through.objects.filter(
                    # trigram_word_similar (operatore <%): confronta q con le singole PAROLE del nome,
                    # così "Belini" trova "Gianfranco Bellini" (con trigram_similar il nome intero abbassa il punteggio)
                    author__in=Author.objects.filter(name__trigram_word_similar=q)
                ).values("book_id")
                # UNION e non OR: un OR tra condizioni su tabelle diverse costringe a leggere tutta catalog_book
                book_ids = book_ids.union(author_ids)

            # SearchRank: punteggio di pertinenza (≈ 0 per i libri trovati solo per autore)
            books = books.filter(pk__in=book_ids).annotate(
                rank=SearchRank(F("search_vector"), query)
            )
            # Prima i più pertinenti; a parità di punteggio, ordine alfabetico (stabile per la paginazione)
            books = books.order_by("-rank", "title")

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
