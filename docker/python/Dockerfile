# Immagine ufficiale di Python 3.14 su Debian trixie
FROM python:3.14-slim-trixie

ARG UID=1000
ARG GID=1000
# -l: niente lastlog (con UID molto alti il file diventerebbe enorme)
RUN groupadd -g "$GID" app && useradd -l -m -u "$UID" -g "$GID" app

# Poetry in un venv tutto suo: le sue dipendenze non si mescolano con quelle del progetto
RUN python -m venv /opt/poetry \
    && /opt/poetry/bin/pip install --no-cache-dir "poetry~=2.5" \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/home/app/.cache/pypoetry \
    PATH="/app/.venv/bin:$PATH"

USER app
RUN mkdir -p /home/app/.cache/pypoetry
WORKDIR /app
