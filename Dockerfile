# Utiliser l'image officielle Python 3.11 slim
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .
COPY pyproject.toml .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY src/ ./src/
COPY app.py .

# Créer le répertoire data/raw s'il n'existe pas
RUN mkdir -p data/raw

# Exposer le port pour FastAPI
EXPOSE 8000

# Commande par défaut pour FastAPI avec uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
