from django.conf import settings
from django.db import models
from django.utils import timezone

# Costanti di dominio: vivono qui (non in services.py) perché Loan.can_renew ne ha bisogno
# e models.py non può importare da services.py (services.py importa già da models.py:
# un import nell'altro verso creerebbe un ciclo).
LOAN_DAYS = 30
MAX_RENEWALS = 2


class Member(models.Model):
    """Il lettore: profilo collegato 1-a-1 all'utente (un bibliotecario può non essere lettore)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="member"
    )
    card_number = models.CharField("tessera", max_length=12, unique=True)
    home_branch = models.ForeignKey(
        "inventory.Branch",
        on_delete=models.PROTECT,
        related_name="members",
        verbose_name="sede",
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
    copy = models.ForeignKey(
        "inventory.Copy",
        on_delete=models.PROTECT,
        related_name="loans",
        verbose_name="copia",
    )
    member = models.ForeignKey(
        Member, on_delete=models.PROTECT, related_name="loans", verbose_name="lettore"
    )
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
                fields=["copy"],
                condition=models.Q(returned_at__isnull=True),
                name="one_open_loan_per_copy",
            ),
        ]
        indexes = [
            models.Index(fields=["member", "returned_at"]),
            models.Index(
                fields=["due_at"],
                condition=models.Q(returned_at__isnull=True),
                name="loan_open_due_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.copy} → {self.member}"

    @property
    def is_overdue(self) -> bool:
        return self.returned_at is None and self.due_at < timezone.now()

    @property
    def can_renew(self) -> bool:
        # Serve al template (bottone "Rinnova" visibile solo se vero) senza duplicare
        # qui il numero di MAX_RENEWALS: la stessa condizione è controllata di nuovo,
        # lato server, in services.renew() prima di modificare i dati.
        return (
            self.returned_at is None
            and not self.is_overdue
            and self.renewals < MAX_RENEWALS
        )


class Reservation(models.Model):
    book = models.ForeignKey(
        "catalog.Book",
        on_delete=models.PROTECT,
        related_name="reservations",
        verbose_name="libro",
    )
    member = models.ForeignKey(
        Member,
        on_delete=models.PROTECT,
        related_name="reservations",
        verbose_name="lettore",
    )
    created_at = models.DateTimeField("creata il", default=timezone.now)
    fulfilled_at = models.DateTimeField("evasa il", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "prenotazione"
        verbose_name_plural = "prenotazioni"
        constraints = [
            models.UniqueConstraint(
                fields=["book", "member"],
                condition=models.Q(fulfilled_at__isnull=True),
                name="one_open_reservation_per_member_and_book",
            )
        ]

    def __str__(self) -> str:
        return f"{self.book} -> {self.member}"
