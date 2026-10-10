"""Regole di dominio dei prestiti: le usano le viste HTML, l'API e i test (come un service Symfony)."""

from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from inventory.models import Copy

from .models import LOAN_DAYS, MAX_RENEWALS, Loan, Member, Reservation


class LoanError(Exception):
    """Regola di prestito violata: il messaggio è pensato per l'utente."""


@transaction.atomic
def lend(*, barcode: str, card_number: str) -> Loan:
    try:
        # select_for_update: SELECT ... FOR UPDATE, la riga resta bloccata fino al COMMIT.
        # Due bibliotecari che prestano la stessa copia nello stesso istante: il secondo aspetta e poi la trova ON_LOAN.
        copy = Copy.objects.select_for_update().get(barcode=barcode)
    except Copy.DoesNotExist:
        raise LoanError(f"Nessuna copia con codice {barcode}.") from None
    try:
        member = Member.objects.get(card_number=card_number)
    except Member.DoesNotExist:
        raise LoanError(f"Nessun lettore con tessera {card_number}.") from None

    if copy.status != Copy.Status.AVAILABLE:
        raise LoanError(
            f"La copia {barcode} non è disponibile ({copy.get_status_display()})."
        )
    if member.loans.overdue().exists():
        raise LoanError("Il lettore ha prestiti scaduti: prima deve restituirli.")
    if member.loans.active().count() >= member.max_loans:
        raise LoanError(f"Il lettore ha già {member.max_loans} prestiti aperti.")

    copy.status = Copy.Status.ON_LOAN
    copy.save(update_fields=["status"])
    return Loan.objects.create(
        copy=copy, member=member, due_at=timezone.now() + timedelta(days=LOAN_DAYS)
    )


@transaction.atomic
def return_copy(*, barcode: str) -> Loan:
    try:
        loan = (
            Loan.objects.select_for_update()
            .active()
            .select_related("copy")
            .get(copy__barcode=barcode)
        )
    except Loan.DoesNotExist:
        raise LoanError(f"La copia {barcode} non risulta in prestito.") from None

    loan.returned_at = timezone.now()
    loan.save(update_fields=["returned_at"])

    reservation = (
        Reservation.objects.filter(book=loan.copy.book, fulfilled_at__isnull=True)
        .order_by("created_at")
        .first()
    )

    if reservation:
        loan.copy.status = Copy.Status.RESERVED
        reservation.fulfilled_at = timezone.now()
        reservation.save(update_fields=["fulfilled_at"])
    else:
        loan.copy.status = Copy.Status.AVAILABLE
    loan.copy.save(update_fields=["status"])
    return loan


@transaction.atomic
def renew(*, loan_id: int, member: Member) -> Loan:
    try:
        # Filtro anche su member=member: un lettore può rinnovare SOLO i propri prestiti,
        # anche manomettendo loan_id nel form (stesso principio di sicurezza di MyLoansView).
        loan = Loan.objects.select_for_update().active().get(pk=loan_id, member=member)
    except Loan.DoesNotExist:
        raise LoanError("Prestito non trovato.") from None
    if loan.is_overdue:
        raise LoanError("Il prestito è scaduto: restituiscilo prima di rinnovarlo.")
    if loan.renewals >= MAX_RENEWALS:
        raise LoanError(
            f"Il prestito non può essere rinnovato: {MAX_RENEWALS} rinnovi già effettuati."
        )
    loan.due_at += timedelta(days=LOAN_DAYS)
    loan.renewals += 1
    loan.save(update_fields=["due_at", "renewals"])
    return loan


@transaction.atomic
def reserve(*, book_id: int, member: Member) -> Reservation:
    if Copy.objects.filter(book_id=book_id, status=Copy.Status.AVAILABLE).exists():
        raise LoanError("Ci sono copie disponibili: prendi in prestito.")
    try:
        return Reservation.objects.create(book_id=book_id, member=member)
    except IntegrityError:
        raise LoanError("Hai già una prenotazione per questo libro.") from None
