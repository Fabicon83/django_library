# Django Library

A learning project: a management system for a large multi-branch library, built with Django while
studying the framework in depth — coming from a background in Symfony (PHP) and Magento 2.

## Goal

This repository is a hands-on path to learning Django professionally, not a toy CRUD app. The domain
is a **large library**: hundreds of thousands of books, physical copies across multiple branches,
members, loans, full-text search, a REST API, background tasks, and tests. A catalog at this scale
makes performance problems (N+1 queries, missing indexes, unnecessary `COUNT(*)`) actually show up,
which is the point.

## Tech stack

- **Django 6.1** (Python 3.14)
- **PostgreSQL 18** — primary database
- **Valkey** — cache
- **Mailpit** — local email testing
- **Django REST Framework** — API layer
- **Docker Compose** — local environment
- **Poetry** — dependency management

## Project structure

```
django_learn/
├── compose.yml          # web (Django), db (PostgreSQL), valkey (cache), mailpit (email)
├── docker/python/        # Dockerfile for the Django service
├── backend/               # Django project (bind-mounted into the container)
│   ├── config/            # settings, urls, wsgi/asgi
│   ├── accounts/          # custom user model
│   ├── catalog/           # authors, publishers, subjects, books
│   ├── inventory/         # branches and physical copies
│   ├── circulation/       # members, loans, domain services
│   └── templates/         # project-level templates
└── docs/                  # extended learning guide (not tracked in git)
```

## Apps overview

| App | Responsibility |
|---|---|
| `accounts` | Custom user model and authentication |
| `catalog` | Books, authors, publishers, subjects |
| `inventory` | Library branches and physical book copies |
| `circulation` | Members and the loan/return domain logic |

## Getting started

Requirements: Docker and Docker Compose.

```bash
cd django_learn
cp .env.example .env     # adjust values as needed
docker compose up -d
```

Then visit:

| Service | URL |
|---|---|
| Django app | http://localhost:8100 |
| Django admin | http://localhost:8100/admin/ |
| Mailpit (email testing) | http://localhost:8036 |
| PostgreSQL | `localhost:5440` |

Containers do **not** restart automatically after a reboot — run `docker compose up -d` again when
you come back. Never run `docker compose down -v`: it deletes the database volume.

### Running management commands

All Python/Django commands run inside the `web` container:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py test
```

## Status

Active learning project — built incrementally, phase by phase (project setup → models → admin →
bulk data & ORM performance → public catalog → auth & permissions → loan domain logic →
PostgreSQL full-text search → REST API → background tasks, email & caching → tests → frontend).
