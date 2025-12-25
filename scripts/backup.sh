#!/bin/bash

# Script de backup pour MarketPulse Africa
# Usage: ./scripts/backup.sh [destination]

set -e

BACKUP_DIR=${1:-./backups}
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql"

echo "💾 Backup de la base de données MarketPulse"
echo "=========================================="

# Créer le dossier de backup s'il n'existe pas
mkdir -p "$BACKUP_DIR"

# Vérifier que le conteneur PostgreSQL existe
if ! docker ps | grep -q marketpulse_postgres; then
    echo "❌ Le conteneur PostgreSQL n'est pas en cours d'exécution"
    exit 1
fi

# Effectuer le backup
echo "📦 Sauvegarde en cours..."
docker exec marketpulse_postgres pg_dump -U marketpulse marketpulse > "$BACKUP_FILE"

# Compresser le backup
echo "🗜️  Compression du backup..."
gzip "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "✅ Backup créé: $BACKUP_FILE ($BACKUP_SIZE)"

# Garder seulement les 7 derniers backups
echo "🧹 Nettoyage des anciens backups (garde les 7 derniers)..."
ls -t "$BACKUP_DIR"/backup_*.sql.gz 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null || true

echo "✅ Backup terminé!"
echo ""
echo "💡 Pour restaurer:"
echo "   gunzip < $BACKUP_FILE | docker exec -i marketpulse_postgres psql -U marketpulse marketpulse"


