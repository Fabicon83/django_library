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
        RESERVED = "reserved", "Riservata"

    book = models.ForeignKey(
        "catalog.Book",
        on_delete=models.CASCADE,
        related_name="copies",
        verbose_name="libro",
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.PROTECT, related_name="copies", verbose_name="sede"
    )
    barcode = models.CharField("codice a barre", max_length=20, unique=True)
    shelf = models.CharField("collocazione", max_length=30)
    status = models.CharField(
        "stato", max_length=10, choices=Status, default=Status.AVAILABLE
    )

    class Meta:
        ordering = ["barcode"]
        verbose_name = "copia"
        verbose_name_plural = "copie"
        indexes = [models.Index(fields=["book", "status"])]

    def __str__(self) -> str:
        return self.barcode
