FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y gcc g++ make

RUN pip install --no-cache-dir -r requirements.txt

RUN python -m spacy download xx_ent_wiki_sm

COPY . .

EXPOSE 8000

CMD [ "uvicorn", "api:app", "--port", "8000", '--host', '0.0.0.0']

