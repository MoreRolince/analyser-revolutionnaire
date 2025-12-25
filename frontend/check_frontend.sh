#!/bin/bash

# Script de vérification du frontend
# Vérifie que le frontend Next.js est correctement configuré et fonctionnel

# Couleurs pour le terminal
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_PORT=${FRONTEND_PORT:-3000}
BACKEND_URL=${NEXT_PUBLIC_API_URL:-http://localhost:8000}
FRONTEND_URL="http://localhost:${FRONTEND_PORT}"

# Compteurs
PASSED=0
FAILED=0
WARNINGS=0

print_header() {
    echo ""
    echo -e "${BOLD}${BLUE}============================================================${NC}"
    echo -e "${BOLD}${BLUE}$1${NC}"
    echo -e "${BOLD}${BLUE}============================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Fonction pour vérifier si une commande existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Fonction pour vérifier si un port est utilisé
check_port() {
    if command_exists lsof; then
        lsof -i :$1 >/dev/null 2>&1
    elif command_exists netstat; then
        netstat -an | grep -q ":$1 .*LISTEN"
    elif command_exists ss; then
        ss -lnt | grep -q ":$1 "
    else
        # Fallback: essayer une connexion HTTP
        curl -s "http://localhost:$1" >/dev/null 2>&1
    fi
}

# Fonction pour vérifier une URL HTTP
check_url() {
    local url=$1
    local timeout=${2:-5}
    
    if command_exists curl; then
        curl -s -f -o /dev/null -w "%{http_code}" --max-time $timeout "$url" 2>/dev/null
    elif command_exists wget; then
        wget -q --spider --timeout=$timeout -O /dev/null "$url" 2>/dev/null && echo "200" || echo "000"
    else
        echo "000"
    fi
}

print_header "VÉRIFICATION DU FRONTEND MARKETPULSE AFRICA"

# 1. Vérifier les dépendances
print_header "1. Vérification des dépendances système"

if command_exists node; then
    NODE_VERSION=$(node --version)
    print_success "Node.js installé: $NODE_VERSION"
    
    # Vérifier la version minimale (>= 18)
    NODE_MAJOR=$(echo $NODE_VERSION | sed 's/v//' | cut -d. -f1)
    if [ "$NODE_MAJOR" -ge 18 ]; then
        print_success "Version Node.js compatible (>= 18)"
    else
        print_warning "Version Node.js: $NODE_VERSION (recommandé: >= 18)"
    fi
else
    print_error "Node.js n'est pas installé"
    exit 1
fi

if command_exists npm; then
    NPM_VERSION=$(npm --version)
    print_success "npm installé: $NPM_VERSION"
else
    print_error "npm n'est pas installé"
    exit 1
fi

# 2. Vérifier les fichiers essentiels
print_header "2. Vérification des fichiers essentiels"

FILES_TO_CHECK=(
    "package.json"
    "next.config.js"
    "tsconfig.json"
    "tailwind.config.js"
    "app/layout.tsx"
    "lib/api.ts"
    "lib/auth.ts"
)

for file in "${FILES_TO_CHECK[@]}"; do
    if [ -f "$file" ]; then
        print_success "Fichier trouvé: $file"
    else
        print_error "Fichier manquant: $file"
    fi
done

# 3. Vérifier node_modules
print_header "3. Vérification des dépendances npm"

if [ -d "node_modules" ]; then
    print_success "Dossier node_modules existe"
    
    # Vérifier quelques packages essentiels
    ESSENTIAL_PACKAGES=("next" "react" "react-dom" "axios")
    for package in "${ESSENTIAL_PACKAGES[@]}"; do
        if [ -d "node_modules/$package" ]; then
            print_success "Package installé: $package"
        else
            print_warning "Package manquant: $package (exécutez: npm install)"
        fi
    done
else
    print_error "Dossier node_modules n'existe pas"
    print_info "Exécutez: npm install"
fi

# 4. Vérifier la configuration
print_header "4. Vérification de la configuration"

# Vérifier next.config.js
if [ -f "next.config.js" ]; then
    if grep -q "NEXT_PUBLIC_API_URL" next.config.js; then
        print_success "Configuration API trouvée dans next.config.js"
        CONFIG_API_URL=$(grep -oP "NEXT_PUBLIC_API_URL.*?\Khttp://[^']+" next.config.js || echo "non trouvé")
        if [ "$CONFIG_API_URL" != "non trouvé" ]; then
            print_info "URL API configurée: $CONFIG_API_URL"
        fi
    else
        print_warning "NEXT_PUBLIC_API_URL non trouvé dans next.config.js"
    fi
fi

# Vérifier lib/api.ts
if [ -f "lib/api.ts" ]; then
    API_DEFAULT=$(grep -oP "localhost:\K\d+" lib/api.ts | head -1 || echo "")
    if [ -n "$API_DEFAULT" ]; then
        print_info "URL API par défaut dans lib/api.ts: http://localhost:$API_DEFAULT"
        if [ "$API_DEFAULT" != "8000" ]; then
            print_warning "Port API par défaut ($API_DEFAULT) différent du backend (8000)"
        fi
    fi
fi

# 5. Vérifier la connexion au backend
print_header "5. Vérification de la connexion au backend"

BACKEND_HEALTH=$(check_url "$BACKEND_URL/health" 5)
if [ "$BACKEND_HEALTH" = "200" ]; then
    print_success "Backend accessible: $BACKEND_URL"
    
    # Vérifier le endpoint /health
    HEALTH_RESPONSE=$(curl -s "$BACKEND_URL/health" 2>/dev/null)
    if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
        print_success "Backend en bonne santé"
    else
        print_warning "Backend répond mais /health ne retourne pas 'healthy'"
    fi
else
    print_error "Backend non accessible: $BACKEND_URL"
    print_info "Assurez-vous que le backend est démarré sur le port 8000"
fi

# 6. Vérifier que le serveur de développement tourne
print_header "6. Vérification du serveur de développement"

if check_port $FRONTEND_PORT; then
    print_success "Serveur frontend détecté sur le port $FRONTEND_PORT"
    
    # Vérifier que Next.js répond
    FRONTEND_RESPONSE=$(check_url "$FRONTEND_URL" 5)
    if [ "$FRONTEND_RESPONSE" = "200" ]; then
        print_success "Frontend accessible: $FRONTEND_URL"
    else
        print_warning "Port $FRONTEND_PORT utilisé mais le frontend ne répond pas correctement (HTTP $FRONTEND_RESPONSE)"
    fi
else
    print_warning "Serveur frontend non détecté sur le port $FRONTEND_PORT"
    print_info "Démarrez le serveur avec: npm run dev"
fi

# 7. Vérifier TypeScript (si disponible)
print_header "7. Vérification TypeScript"

if command_exists tsc; then
    print_success "TypeScript installé"
    
    # Essayer de compiler (sans émettre de fichiers)
    if tsc --noEmit --skipLibCheck >/dev/null 2>&1; then
        print_success "Compilation TypeScript réussie (aucune erreur)"
    else
        print_warning "Erreurs TypeScript détectées (exécutez: tsc --noEmit pour voir les détails)"
    fi
else
    print_info "TypeScript CLI non disponible (normal si installé via npm)"
fi

# 8. Vérifier ESLint (si disponible)
print_header "8. Vérification ESLint"

if [ -f "node_modules/.bin/eslint" ] || command_exists eslint; then
    print_success "ESLint disponible"
    print_info "Exécutez 'npm run lint' pour vérifier le code"
else
    print_info "ESLint non disponible"
fi

# Résumé final
print_header "RÉSUMÉ"

echo -e "${BOLD}Tests réussis:${NC} ${GREEN}$PASSED${NC}"
echo -e "${BOLD}Tests échoués:${NC} ${RED}$FAILED${NC}"
echo -e "${BOLD}Avertissements:${NC} ${YELLOW}$WARNINGS${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✓ Tous les tests critiques sont passés!${NC}"
    echo -e "${GREEN}Le frontend est prêt.${NC}"
    echo ""
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}Il y a $WARNINGS avertissement(s) à vérifier.${NC}"
    fi
    exit 0
else
    echo -e "${RED}${BOLD}✗ Certains tests ont échoué${NC}"
    echo -e "${YELLOW}Vérifiez les erreurs ci-dessus et corrigez-les.${NC}"
    exit 1
fi
