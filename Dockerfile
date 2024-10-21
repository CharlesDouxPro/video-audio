FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD [ "uvicorn",

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
