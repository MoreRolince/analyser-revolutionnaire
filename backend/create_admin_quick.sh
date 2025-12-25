#!/bin/bash
# Script rapide pour créer un admin par défaut
# Usage: ./create_admin_quick.sh

cd "$(dirname "$0")"

# Activer l'environnement virtuel si disponible
if [ -d "env" ]; then
    source env/bin/activate
fi

# Créer un admin par défaut
python3 create_admin.py --create-direct admin@marketpulse.com "Admin Principal" admin123

echo ""
echo "✅ Admin créé!"
echo "Vous pouvez maintenant vous connecter avec:"
echo "  Email: admin@marketpulse.com"
echo "  Password: admin123"
