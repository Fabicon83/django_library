# Le view qui sono "sottili": non contengono regole di dominio (quelle stanno in services.py,
# come un service layer in Symfony). Si occupano solo di: autenticazione/permessi, form HTML,
# messaggi all'utente e redirect. La logica vera (disponibilità copia, limiti prestiti, ecc.)
# vive in services.lend() / services.return_copy().

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView, ListView

from . import services
from .forms import LendForm, ReturnForm
from .models import Loan


class MyLoansView(LoginRequiredMixin, ListView):
    """Pagina "i miei prestiti": un utente loggato vede solo i propri, mai quelli altrui.

    LoginRequiredMixin: se non autenticato, redirect automatico alla pagina di login
    (equivalente concettuale di un IsAuthenticated/voter su un controller Symfony).
    """

    template_name = "circulation/my_loans.html"
    context_object_name = (
        "loans"  # nel template la queryset è disponibile come {{ loans }}
    )

    def get_queryset(self):
        # Solo i prestiti dell'utente collegato: mai fidarsi di un id passato nell'URL
        # (self.request.user è sempre l'utente autenticato lato server, non manipolabile dal client).
        # select_related("copy__book") fa un JOIN SQL per precaricare copy e book insieme ai loan:
        # senza, ogni loan.copy.book nel template genererebbe una query separata (problema N+1).
        return Loan.objects.filter(member__user=self.request.user).select_related(
            "copy__book"
        )


class DeskFormView(PermissionRequiredMixin, FormView):
    """Base per il banco prestiti: solo chi ha il permesso (gruppo Bibliotecari).

    Classe astratta condivisa da LendView e ReturnView: centralizza il pattern comune
    "valida il form → esegui l'azione di dominio → gestisci l'eventuale errore di business".
    Le sottoclassi implementano solo `perform()` con la chiamata al service specifico.
    """

    # Dopo un submit riuscito, FormView fa redirect qui (pattern Post/Redirect/Get,
    # evita il reinvio del form se l'utente ricarica la pagina).
    success_url = reverse_lazy("circulation:desk")

    def form_valid(self, form):
        # form_valid viene chiamato solo se la validazione Django del form (tipi, campi
        # obbligatori, ecc.) è già passata. Qui si prova a eseguire l'azione di dominio:
        # le regole di business (es. copia non disponibile) sono controllate nel service,
        # non nel form, perché richiedono di interrogare il database.
        try:
            message = self.perform(form.cleaned_data)
        except services.LoanError as e:
            # Errore di dominio (non di validazione campo): lo si allega al form come
            # errore "generale" (non legato a un campo specifico, da qui `None`) e si
            # ri-mostra la pagina con il form compilato e il messaggio d'errore.
            form.add_error(None, str(e))
            return self.form_invalid(form)
        # Tutto ok: messaggio di successo (framework django.contrib.messages, mostrato
        # alla prossima pagina via template) e redirect a success_url.
        messages.success(self.request, message)
        return super().form_valid(form)


class LendView(DeskFormView):
    """Form "presta una copia": barcode copia + tessera lettore."""

    # Permesso Django standard, generato automaticamente dal modello Loan
    # (app_label.add_loan): assegnato al gruppo "Bibliotecari" nell'admin.
    permission_required = "circulation.add_loan"
    form_class = LendForm
    template_name = "circulation/desk.html"

    def perform(self, data) -> str:
        # Tutta la logica (copia disponibile? lettore ok? limiti rispettati?) è nel service.
        loan = services.lend(barcode=data["barcode"], card_number=data["card_number"])
        return f"Prestito registrato: {loan.copy} a {loan.member}, scadenza {loan.due_at:%d/%m/%Y}."


class ReturnView(DeskFormView):
    """Form "restituisci una copia": solo barcode della copia."""

    permission_required = "circulation.change_loan"
    form_class = ReturnForm
    template_name = "circulation/return.html"

    def perform(self, data) -> str:
        loan = services.return_copy(barcode=data["barcode"])
        return f"Restituzione registrata: {loan.copy}."


class RenewView(LoginRequiredMixin, View):
    def post(self, request):
        loan_id = request.POST["loan_id"]
        try:
            loan = services.renew(loan_id=loan_id, member=request.user.member)
        except services.LoanError as e:
            messages.error(request, str(e))
        else:
            messages.success(
                request, f"Prestito rinnovato: nuova scadenza {loan.due_at:%d/%m/%Y}."
            )
        return redirect("circulation:my_loans")
