# syntax=docker/dockerfile:1

# Utilisation de Python 3.12 slim comme base
ARG PYTHON_VERSION=3.12.6
FROM python:${PYTHON_VERSION}-slim AS base

# Empêche Python d'écrire des fichiers pyc
ENV PYTHONDONTWRITEBYTECODE=1
# Garde les flux stdout/stderr non bufferisés
ENV PYTHONUNBUFFERED=1
# Définir le répertoire de travail
WORKDIR /app

# Met à jour apt-get et installe les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    ffmpeg \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install -r requirements.txt

# Installer spaCy et télécharger le modèle linguistique
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install spacy && \
    python -m spacy download xx_ent_wiki_sm

# Copier le reste des fichiers de l'application
COPY . .

# Exposer le port et le rendre configurable
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

