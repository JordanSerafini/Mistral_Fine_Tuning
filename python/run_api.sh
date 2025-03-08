#!/bin/bash

# Script pour lancer l'API du modèle fine-tuné

# Activer l'environnement virtuel
source ./venv/bin/activate

# Installer les dépendances nécessaires
pip install fastapi uvicorn pydantic

# Fonction d'aide
show_help() {
    echo "Usage: ./run_api.sh [option]"
    echo ""
    echo "Options:"
    echo "  --model PATH      Chemin vers le modèle fine-tuné (par défaut: jordanS/analyse_agent)"
    echo "  --base MODEL      Modèle de base utilisé (par défaut: mistralai/Mistral-7B-v0.1)"
    echo "  --port PORT       Port sur lequel lancer l'API (par défaut: 8000)"
    echo "  --help            Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  ./run_api.sh                                # Lancer l'API avec le modèle par défaut"
    echo "  ./run_api.sh --model mon_modele            # Utiliser un modèle spécifique"
    echo "  ./run_api.sh --port 8080                   # Lancer l'API sur le port 8080"
}

# Traiter les arguments
MODEL_PATH="jordanS/analyse_agent"
BASE_MODEL="mistralai/Mistral-7B-v0.1"
PORT=8000

while [[ $# -gt 0 ]]; do
    case "$1" in
        --model)
            MODEL_PATH="$2"
            echo "Modèle: $MODEL_PATH"
            shift
            ;;
        --base)
            BASE_MODEL="$2"
            echo "Modèle de base: $BASE_MODEL"
            shift
            ;;
        --port)
            PORT="$2"
            echo "Port: $PORT"
            shift
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
    shift
done

# Définir les variables d'environnement
export MODEL_PATH=$MODEL_PATH
export BASE_MODEL=$BASE_MODEL

# Lancer l'API
echo "Démarrage de l'API sur http://localhost:$PORT..."
echo "Modèle: $MODEL_PATH"
echo "Modèle de base: $BASE_MODEL"

# Lancer l'API avec uvicorn directement
uvicorn model_api:app --host 0.0.0.0 --port $PORT

# Désactiver l'environnement virtuel (ne sera jamais exécuté tant que l'API est en cours d'exécution)
# deactivate 