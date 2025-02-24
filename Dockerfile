# Utilisation de Python Slim pour minimiser la taille de l'image
ARG PYTHON_VERSION=3.12.6
FROM python:${PYTHON_VERSION}-slim AS base


# Définition du dossier de travail
WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    gcc \
    g++ \
    make \
    ffmpeg \
    unzip \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*
    
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install ./google-chrome-stable_current_amd64.deb
RUN sudo apt-get install -y libnss3 libatk-bridge2.0-0 libgbm-dev libx11-xcb1 libasound2

# Copie des dépendances Python et installation
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    python -m pip install -r requirements.txt

# Téléchargement du modèle spaCy
RUN python -m spacy download xx_ent_wiki_sm

# Copie du code source
COPY . .

# Exposition du port pour FastAPI
EXPOSE 8000

# Commande de démarrage de FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
