FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système pour Playwright
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    wget \
    gnupg \
    fonts-liberation \
    fonts-unifont \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libx11-6 \
    libxext6 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installer les navigateurs Playwright
RUN playwright install chromium
# Installer les dépendances avec gestion d'erreur pour les packages manquants
RUN playwright install-deps chromium || true

# Copier le code
COPY . .

# Exposer le port (non utilisé mais pour cohérence)
EXPOSE 8001

# Commande par défaut
CMD ["python", "worker.py"]


    libxext6 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installer les navigateurs Playwright
RUN playwright install chromium
# Installer les dépendances avec gestion d'erreur pour les packages manquants
RUN playwright install-deps chromium || true

# Copier le code
COPY . .

# Exposer le port (non utilisé mais pour cohérence)
EXPOSE 8001

# Commande par défaut
CMD ["python", "worker.py"]

