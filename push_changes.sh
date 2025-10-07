#!/bin/bash
# Script de déploiement pour pousser les modifications

echo "🚀 Déploiement des modifications..."

# Vérifier le statut git
echo "📋 Statut git actuel:"
git status

# Ajouter tous les fichiers modifiés
echo "📦 Ajout des fichiers modifiés..."
git add .

# Commit avec message descriptif
echo "💾 Création du commit..."
git commit -m "feat: ajout script test browser et corrections VM Ubuntu

- Ajout test_browser.py pour tester Chrome sur Ubuntu VM
- Configuration adaptée pour environnement VM (headless, no-sandbox)
- Support des chemins Chrome Linux (/usr/bin/google-chrome)
- Tests de navigation et création d'agent
- Script de déploiement push_changes.sh"

# Push vers le repository distant
echo "📤 Push vers le repository distant..."
git push origin main

echo "✅ Déploiement terminé!"
echo "🧪 Pour tester sur Ubuntu VM:"
echo "   python3 test_browser.py"
