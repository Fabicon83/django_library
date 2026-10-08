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
    language = models.CharField(
        "lingua", max_length=2, choices=Language, default=Language.ITALIAN
    )
    pages = models.PositiveSmallIntegerField("pagine", null=True, blank=True)
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.PROTECT,
        related_name="books",
        verbose_name="editore",
    )
    authors = models.ManyToManyField(
        Author, related_name="books", verbose_name="autori"
    )
    subjects = models.ManyToManyField(
        Subject, related_name="books", blank=True, verbose_name="soggetti"
    )
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
            models.CheckConstraint(
                condition=~models.Q(published_year=0), name="book_year_not_zero"
            ),
        ]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("catalog:book_detail", args=[self.pk])
