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
