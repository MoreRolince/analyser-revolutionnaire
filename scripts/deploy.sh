#!/bin/bash

# Script de déploiement pour MarketPulse Africa
# Usage: ./scripts/deploy.sh [production|staging]

set -e  # Arrêter en cas d'erreur

ENVIRONMENT=${1:-production}
COMPOSE_FILE="docker-compose.prod.yml"

echo "🚀 Déploiement MarketPulse Africa - Environnement: $ENVIRONMENT"
echo "=========================================="

# Vérifier que Docker est installé
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Vérifier que Docker Compose est installé
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Vérifier que le fichier .env existe
if [ ! -f .env ]; then
    echo "❌ Le fichier .env n'existe pas."
    echo "📝 Créez-le à partir de .env.production.example"
    exit 1
fi

# Vérifier que le fichier docker-compose.prod.yml existe
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ Le fichier $COMPOSE_FILE n'existe pas."
    echo "📝 Créez-le à partir de docker-compose.prod.yml.example"
    exit 1
fi

echo "✅ Vérifications préalables OK"
echo ""

# Construire les images
echo "🔨 Construction des images Docker..."
docker-compose -f $COMPOSE_FILE build --no-cache

# Arrêter les anciens conteneurs
echo "🛑 Arrêt des anciens conteneurs..."
docker-compose -f $COMPOSE_FILE down

# Démarrer les services
echo "▶️  Démarrage des services..."
docker-compose -f $COMPOSE_FILE up -d

# Attendre que PostgreSQL soit prêt
echo "⏳ Attente que PostgreSQL soit prêt..."
sleep 10

# Appliquer les migrations
echo "🗄️  Application des migrations de base de données..."
docker exec marketpulse_backend alembic upgrade head || echo "⚠️  Migrations déjà appliquées ou erreur"

# Vérifier la santé des services
echo "🏥 Vérification de la santé des services..."
sleep 5

# Vérifier PostgreSQL
if docker exec marketpulse_postgres pg_isready -U marketpulse > /dev/null 2>&1; then
    echo "✅ PostgreSQL est prêt"
else
    echo "❌ PostgreSQL n'est pas prêt"
fi

# Vérifier Redis
if docker exec marketpulse_redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis est prêt"
else
    echo "❌ Redis n'est pas prêt"
fi

# Vérifier Backend
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend est accessible"
else
    echo "⚠️  Backend n'est pas accessible (peut-être derrière Nginx)"
fi

echo ""
echo "✅ Déploiement terminé!"
echo ""
echo "📊 Statut des services:"
docker-compose -f $COMPOSE_FILE ps

echo ""
echo "📝 Commandes utiles:"
echo "  - Voir les logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "  - Arrêter: docker-compose -f $COMPOSE_FILE down"
echo "  - Redémarrer: docker-compose -f $COMPOSE_FILE restart"
echo "  - Backup DB: docker exec marketpulse_postgres pg_dump -U marketpulse marketpulse > backup.sql"


