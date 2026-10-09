import random
import time

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify
from faker import Faker

from catalog.models import Author, Book, Publisher, Subject
from inventory.models import Branch, Copy

SUBJECTS = [
    "Narrativa",
    "Storia",
    "Filosofia",
    "Scienze",
    "Informatica",
    "Arte",
    "Ragazzi",
    "Poesia",
    "Viaggi",
    "Economia",
]
BRANCHES = [
    ("Centrale", "Milano"),
    ("Nord", "Milano"),
    ("Sud", "Milano"),
    ("Ovest", "Milano"),
]


class Command(BaseCommand):
    help = "Popola il catalogo con dati finti (anche centinaia di migliaia di righe)"

    def add_arguments(self, parser):
        parser.add_argument("--books", type=int, default=50_000)
        parser.add_argument(
            "--reset", action="store_true", help="cancella prima catalogo e copie"
        )

    @transaction.atomic
    def handle(self, *args, books: int, reset: bool, **options):
        if reset:
            Copy.objects.all().delete()
            Book.objects.all().delete()
            Author.objects.all().delete()
            Publisher.objects.all().delete()
            Subject.objects.all().delete()
            Branch.objects.all().delete()
        elif Book.objects.exists():
            raise CommandError("Il catalogo non è vuoto: usa --reset")

        start = time.monotonic()
        fake = Faker("it_IT")
        Faker.seed(42)
        random.seed(42)

        subjects = Subject.objects.bulk_create(
            [Subject(name=n, slug=slugify(n)) for n in SUBJECTS]
        )
        branches = Branch.objects.bulk_create(
            [Branch(name=n, city=c) for n, c in BRANCHES]
        )
        publishers = Publisher.objects.bulk_create(
            [Publisher(name=fake.unique.company()) for _ in range(300)]
        )
        authors = Author.objects.bulk_create(
            [
                Author(name=fake.name(), birth_year=random.randint(1800, 2000))
                for _ in range(max(books // 5, 1))
            ],
            batch_size=5000,
        )
        self.stdout.write(f"{len(authors)} autori, {len(publishers)} editori")

        # bulk_create: un INSERT ogni batch_size righe invece di uno per riga (niente save(), niente segnali)
        book_objs = Book.objects.bulk_create(
            [
                Book(
                    title=fake.sentence(nb_words=random.randint(2, 6)).rstrip("."),
                    isbn=f"978{i:010d}",
                    published_year=random.randint(1900, 2025),
                    language=random.choice(Book.Language.values),
                    pages=random.randint(80, 900),
                    publisher=random.choice(publishers),
                )
                for i in range(books)
            ],
            batch_size=5000,
        )
        self.stdout.write(f"{len(book_objs)} libri")

        # Le ManyToMany si popolano scrivendo direttamente nella tabella intermedia
        BookAuthor = Book.authors.through
        BookAuthor.objects.bulk_create(
            [
                BookAuthor(book_id=b.pk, author_id=random.choice(authors).pk)
                for b in book_objs
            ],
            batch_size=10_000,
        )
        BookSubject = Book.subjects.through
        BookSubject.objects.bulk_create(
            [
                BookSubject(book_id=b.pk, subject_id=random.choice(subjects).pk)
                for b in book_objs
            ],
            batch_size=10_000,
        )

        copies = [
            Copy(
                book_id=b.pk,
                branch=random.choice(branches),
                barcode=f"C{b.pk:08d}{n}",
                shelf=f"{random.randint(1, 99):02d}.{random.randint(1, 20)}",
            )
            for b in book_objs
            for n in range(random.randint(1, 4))
        ]
        Copy.objects.bulk_create(copies, batch_size=10_000)
        self.stdout.write(
            self.style.SUCCESS(
                f"{len(copies)} copie. Fatto in {time.monotonic() - start:.1f} s"
            )
        )
