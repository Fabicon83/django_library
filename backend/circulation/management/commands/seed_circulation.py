# --- Import: standard library ---
import random  # numeri/scelte casuali (random.choice, random.randint)
import time  # misura la durata del comando
from datetime import (
    timedelta,
)  # durata (giorni, secondi) da sommare/sottrarre a un datetime


# --- Import: librerie esterne (Django, Faker) ---
from django.contrib.auth import (
    get_user_model,
)  # restituisce il modello utente attivo (AUTH_USER_MODEL)
from django.core.management.base import (
    BaseCommand,
    CommandError,
)  # base dei comandi manage.py + errore "pulito"
from django.db import transaction  # gestione transazioni (atomic)
from django.utils import (
    timezone,
)  # timezone.now(): datetime "aware" (con fuso), come vuole USE_TZ=True

from django.contrib.auth.hashers import (
    make_password,
)  # hash di una password in chiaro (PBKDF2)

from faker import Faker  # genera dati finti realistici (nomi, cognomi, ...)

# --- Import: app del progetto ---
from circulation.models import Loan, Member, Reservation, LOAN_DAYS
from inventory.models import Branch, Copy


# Django cerca in <app>/management/commands/ un modulo con una classe che si chiama
# ESATTAMENTE "Command": il nome del file (seed_circulation) diventa il nome del comando,
# cioè "python manage.py seed_circulation". 🅢 Come una classe che estende Symfony Command.
class Command(BaseCommand):
    # Testo mostrato da "manage.py seed_circulation --help"
    help = "Popola lettori e prestiti storici (richiede il catalogo di seed_library)"

    # Django chiama questo metodo per dichiarare le opzioni da riga di comando.
    # "parser" è un argparse.ArgumentParser della standard library. 🅢 Come configure() + addOption().
    def add_arguments(self, parser):
        # --members N: quanti lettori creare. type=int converte la stringa "300" nel numero 300
        # (e rifiuta valori non numerici); default se l'opzione non viene passata.
        # 5_000 = 5000: l'underscore serve solo a leggere meglio le cifre.
        parser.add_argument("--members", type=int, default=5_000)
        # --loans N: quanti prestiti storici creare
        parser.add_argument("--loans", type=int, default=20_000)
        # --reset è un flag senza valore: action="store_true" vale True se presente, False se assente
        parser.add_argument(
            "--reset",
            action="store_true",
            help="cancella prima lettori, prestiti e prenotazioni",
        )

    # Tutto handle() gira in UNA transazione: se qualcosa fallisce a metà (eccezione),
    # PostgreSQL annulla tutto con un ROLLBACK e il DB resta com'era prima del comando.
    @transaction.atomic
    # handle() è il corpo del comando (🅢 execute()). Le opzioni arrivano come argomenti per nome:
    # "--members" diventa members, "--reset" diventa reset. **options raccoglie quelle standard
    # di Django (verbosity, settings, ...) che qui non usiamo.
    def handle(self, *args, members: int, loans: int, reset: bool, **options):
        # Senza copie non ci sono prestiti da creare: il catalogo va popolato prima.
        # exists() fa "SELECT 1 ... LIMIT 1": più leggero di count() su tabelle grandi.
        if not Copy.objects.exists():
            # CommandError: Django stampa solo il messaggio (niente traceback) ed esce con codice 1
            raise CommandError("Nessuna copia nel catalogo: prima lancia seed_library")

        if reset:
            # Loan e Reservation puntano a Member con PROTECT: vanno cancellati per primi
            # (altrimenti cancellare un Member solleverebbe ProtectedError)
            Reservation.objects.all().delete()
            Loan.objects.all().delete()
            # I Member spariscono in CASCADE con il loro utente; lo staff (bibliotecari) resta.
            # member__isnull=False: solo utenti che HANNO un profilo Member (JOIN sulla relazione inversa).
            get_user_model().objects.filter(
                member__isnull=False, is_staff=False
            ).delete()
            # Le copie rimaste ON_LOAN/RESERVED senza più prestiti tornano disponibili.
            # update() è un solo "UPDATE ... WHERE status IN (...)": non carica gli oggetti in Python.
            Copy.objects.filter(
                status__in=[Copy.Status.ON_LOAN, Copy.Status.RESERVED]
            ).update(status=Copy.Status.AVAILABLE)
        elif Member.objects.exists():
            # Senza --reset ci fermiamo se ci sono già lettori: rilanciare creerebbe username
            # duplicati e il vincolo UNIQUE farebbe fallire tutto a metà
            raise CommandError("Ci sono già dei lettori: usa --reset")

        # monotonic(): orologio che non torna mai indietro (ideale per misurare durate)
        start = time.monotonic()
        # Faker con locale italiano: nomi e cognomi italiani
        fake = Faker("it_IT")
        # Seed fissi: ogni esecuzione genera gli STESSI dati (riproducibili, utili per confronti e bug)
        Faker.seed(42)
        random.seed(42)

        # Le sedi sono poche: le carichiamo una volta in una lista Python, così random.choice()
        # sceglie in memoria invece di fare una query per ogni lettore
        branches = list(Branch.objects.all())

        # --- Punto 2: utenti ---
        User = get_user_model()
        # make_password è VOLUTAMENTE lenta (PBKDF2, centinaia di migliaia di iterazioni, ~0,3 s):
        # chiamata 5.000 volte = ~25 minuti. Una volta sola = stesso hash per tutti (ok per dati finti)
        hashed = make_password("password")
        # bulk_create: un INSERT ogni batch_size righe, invece di un INSERT per utente.
        # Non chiama save() né set_password(): per questo la password deve essere GIÀ hashata
        users = User.objects.bulk_create(
            [
                User(
                    username=f"lettore{i:05d}",  # lettore00001, lettore00002, ... (5 cifre con zeri)
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    email=f"lettore{i:05d}@example.com",  # example.com: dominio riservato, mai email vere
                    password=hashed,
                )
                for i in range(
                    1, members + 1
                )  # da 1 a members incluso: parte da lettore00001
            ],
            batch_size=5000,
        )
        # Su PostgreSQL bulk_create restituisce gli oggetti con il pk già valorizzato
        # (INSERT ... RETURNING id): al punto 3 li usiamo direttamente come FK dei Member
        self.stdout.write(f"{len(users)} utenti")

        # --- Punto 3: lettori ---
        # Un Member per ogni utente appena creato. zip() non serve: enumerate() dà l'indice
        # per la tessera e l'utente insieme. start=1 → la tessera T00000001 va a lettore00001
        member_objs = Member.objects.bulk_create(
            [
                Member(
                    user=u,  # FK OneToOne: u ha già il pk grazie a bulk_create del punto 2
                    card_number=f"T{i:08d}",  # T + 8 cifre = 9 caratteri (max_length=12)
                    home_branch=random.choice(
                        branches
                    ),  # sede scelta in memoria, nessuna query
                    # max_loans non serve: prende il default del modello (5)
                )
                for i, u in enumerate(users, start=1)
            ],
            batch_size=5000,
        )
        self.stdout.write(f"{len(member_objs)} lettori")

        # --- Punto 4: prestiti storici (tutti già restituiti) ---
        now = timezone.now()
        # Solo gli id delle copie, non oggetti interi: values_list(flat=True) → lista di interi.
        # Con ~125.000 copie sono pochi MB invece di 125.000 istanze Copy in memoria
        copy_ids = list(Copy.objects.values_list("pk", flat=True))

        loan_objs = []
        # Ciclo for normale (non list comprehension): ogni prestito ha 3 date che dipendono
        # l'una dall'altra, più leggibile su più righe. "_" = variabile che non ci interessa
        for _ in range(loans):
            # Inizio prestito tra 2 anni fa e (LOAN_DAYS + 30) giorni fa: così anche il ritardo
            # massimo (scadenza + 30 giorni) cade nel passato e returned_at non è mai nel futuro.
            # seconds casuali: orari diversi durante la giornata, non tutti alla stessa ora
            loaned_at = now - timedelta(
                days=random.randint(LOAN_DAYS + 30, 730),
                seconds=random.randint(0, 86_399),
            )
            due_at = loaned_at + timedelta(days=LOAN_DAYS)
            # random.random() → float tra 0 e 1: < 0.8 vale per circa l'80% dei prestiti
            if random.random() < 0.8:
                # restituito in tempo: tra 1 giorno e la scadenza
                returned_at = loaned_at + timedelta(days=random.randint(1, LOAN_DAYS))
            else:
                # restituito in ritardo: da 1 a 30 giorni dopo la scadenza
                returned_at = due_at + timedelta(days=random.randint(1, 30))
            loan_objs.append(
                Loan(
                    copy_id=random.choice(
                        copy_ids
                    ),  # FK passata come id: nessun oggetto Copy
                    member=random.choice(
                        member_objs
                    ),  # oggetto Member del punto 3 (ha già il pk)
                    loaned_at=loaned_at,  # sovrascrive default=timezone.now del modello
                    due_at=due_at,
                    returned_at=returned_at,  # valorizzato → prestito chiuso: l'indice UNIQUE parziale
                    # one_open_loan_per_copy (returned_at IS NULL) non lo considera
                )
            )
        Loan.objects.bulk_create(loan_objs, batch_size=5000)
        self.stdout.write(f"{len(loan_objs)} prestiti storici")

        # self.stdout (non print): Django lo gestisce, e nei test si può catturare.
        # style.SUCCESS colora il testo di verde nel terminale.
        self.stdout.write(
            self.style.SUCCESS(f"Fatto in {time.monotonic() - start:.1f} s")
        )
