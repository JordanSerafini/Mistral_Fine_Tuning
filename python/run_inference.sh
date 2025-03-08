#!/bin/bash

# Script pour utiliser le modèle fine-tuné

# Activer l'environnement virtuel
source ./venv/bin/activate

# Fonction d'aide
show_help() {
    echo "Usage: ./run_inference.sh [option]"
    echo ""
    echo "Options:"
    echo "  --interactive    Lancer le mode interactif (chat)"
    echo "  --prompt \"texte\" Générer une réponse pour un prompt spécifique"
    echo "  --help           Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  ./run_inference.sh --interactive    # Démarrer une conversation interactive"
    echo "  ./run_inference.sh --prompt \"Analyse ce document: ...\"    # Générer une réponse"
}

# Vérifier les arguments
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

# Traiter les arguments
case "$1" in
    --interactive)
        echo "Démarrage du mode interactif..."
        python inference.py --interactive
        ;;
    --prompt)
        if [ -z "$2" ]; then
            echo "Erreur: Veuillez fournir un prompt après --prompt"
            exit 1
        fi
        echo "Génération d'une réponse pour le prompt: $2"
        python inference.py --prompt "$2"
        ;;
    --help)
        show_help
        exit 0
        ;;
    *)
        echo "Option non reconnue: $1"
        show_help
        exit 1
        ;;
esac

# Désactiver l'environnement virtuel
deactivate 