# Utilisation de Python Slim pour minimiser la taille de l'image
ARG PYTHON_VERSION=3.12.6
FROM python:${PYTHON_VERSION}-slim AS base

# Éviter l'écriture de fichiers pyc et activer l'affichage en temps réel des logs Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Définition du dossier de travail
WORKDIR /workspace

# Installation des dépendances système
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

# Installation de Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Installation de ChromeDriver
ARG CHROME_DRIVER_VERSION=133.0.6943.126
RUN wget -q "https://chromedriver.storage.googleapis.com/${CHROME_DRIVER_VERSION}/chromedriver_linux64.zip" -O chromedriver.zip && \
    unzip chromedriver.zip && \
    mv chromedriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm chromedriver.zip

# Vérification des installations
RUN google-chrome --version && chromedriver --version

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
