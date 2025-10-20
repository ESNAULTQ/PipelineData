# Utiliser l'image officielle Python 3.11 slim
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier le fichier requirements.txt
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY src/ ./src/

# Créer le répertoire data/raw s'il n'existe pas
RUN mkdir -p data/raw

# Exposer le port (optionnel, pour les applications web)
# EXPOSE 8000

# Commande par défaut
CMD ["/bin/sh", "-c", "python src/download_data.py && python src/import_data_postgres.py"]
