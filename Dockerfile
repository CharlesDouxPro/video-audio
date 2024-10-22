# Utiliser l'image python:3.12-slim comme base
FROM python:3.12-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier requirements.txt avant d'installer les dépendances
COPY requirements.txt .

# Mettre à jour les paquets et installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python à partir de requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Installer spaCy et télécharger le modèle linguistique
RUN pip install --no-cache-dir spacy && \
    python -m spacy download xx_ent_wiki_sm

# Copier le reste des fichiers de l'application
COPY . .

# Exposer le port sur lequel l'application sera exécutée
EXPOSE 8000

# Définir la commande pour démarrer l'application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
