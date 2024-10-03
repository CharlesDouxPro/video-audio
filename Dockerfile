# Utiliser l'image Python 3.12.5 slim
FROM python:3.12-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier le fichier des exigences et installer les dépendances
COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Installe les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    build-essential \
    libatlas-base-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -r requirements.txt

RUN python -m spacy download xx_ent_wiki_sm

# Copier le reste des fichiers du projet
COPY . .

# Définir la commande d'entrée
CMD ["python", "pipeline.py"]
