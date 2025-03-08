#!/bin/bash

# Script pour exécuter le fine-tuning avec différentes options

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "Python 3 n'est pas installé. Veuillez l'installer avant de continuer."
    exit 1
fi

# Vérifier si pip est installé
if ! command -v pip3 &> /dev/null; then
    echo "pip3 n'est pas installé. Veuillez l'installer avant de continuer."
    exit 1
fi

# Créer un environnement virtuel si nécessaire
if [ ! -d "venv" ]; then
    echo "Création d'un environnement virtuel..."
    python3 -m venv venv
fi

# Activer l'environnement virtuel
echo "Activation de l'environnement virtuel..."
source ./venv/bin/activate

# Fonction d'aide
show_help() {
    echo "Usage: ./run_finetune.sh [option]"
    echo ""
    echo "Options:"
    echo "  --small           Utiliser le petit modèle TinyLlama (1.1B) avec QLoRA (par défaut)"
    echo "  --large           Utiliser le grand modèle Mistral (7B) avec QLoRA"
    echo "  --gpt2            Utiliser le modèle GPT2 (encore plus petit)"
    echo "  --epochs N        Définir le nombre d'époques (par défaut: 3 pour small/gpt2, 2 pour large)"
    echo "  --batch N         Définir la taille du batch (par défaut: 4 pour small/gpt2, 1 pour large)"
    echo "  --output PATH     Définir le chemin de sortie du modèle"
    echo "  --clean           Nettoyer le dossier de sortie avant l'entraînement"
    echo "  --continue        Continuer l'entraînement à partir d'un modèle existant"
    echo "  --from PATH       Spécifier le modèle existant à partir duquel continuer (avec --continue)"
    echo "  --help            Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  ./run_finetune.sh --small                      # Fine-tuner TinyLlama (1.1B) avec QLoRA"
    echo "  ./run_finetune.sh --large --epochs 3           # Fine-tuner Mistral (7B) avec 3 époques"
    echo "  ./run_finetune.sh --gpt2 --output mon_modele   # Fine-tuner GPT2 et sauvegarder dans mon_modele"
    echo "  ./run_finetune.sh --continue --from jordanS/analyse_agent  # Continuer l'entraînement"
}

# Traiter les arguments
USE_SMALLER_MODEL="true"  # Par défaut, utiliser le petit modèle
ALTERNATIVE_MODEL="false"  # Par défaut, ne pas utiliser le modèle alternatif
EPOCHS=""
BATCH_SIZE=""
OUTPUT_PATH=""
CLEAN_OUTPUT="false"
CONTINUE_TRAINING="false"
EXISTING_MODEL=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --small)
            USE_SMALLER_MODEL="true"
            ALTERNATIVE_MODEL="false"
            echo "Mode sélectionné: TinyLlama (1.1B) avec QLoRA"
            ;;
        --large)
            USE_SMALLER_MODEL="false"
            echo "Mode sélectionné: Mistral (7B) avec QLoRA"
            ;;
        --gpt2)
            USE_SMALLER_MODEL="true"
            ALTERNATIVE_MODEL="true"
            echo "Mode sélectionné: Modèle GPT2"
            ;;
        --epochs)
            EPOCHS="$2"
            echo "Nombre d'époques: $EPOCHS"
            shift
            ;;
        --batch)
            BATCH_SIZE="$2"
            echo "Taille du batch: $BATCH_SIZE"
            shift
            ;;
        --output)
            OUTPUT_PATH="$2"
            echo "Chemin de sortie: $OUTPUT_PATH"
            shift
            ;;
        --clean)
            CLEAN_OUTPUT="true"
            echo "Nettoyage du dossier de sortie activé"
            ;;
        --continue)
            CONTINUE_TRAINING="true"
            echo "Continuation de l'entraînement activée"
            ;;
        --from)
            EXISTING_MODEL="$2"
            echo "Modèle existant: $EXISTING_MODEL"
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

if [ -z "$1" ]; then
    echo "Mode par défaut: TinyLlama (1.1B) avec QLoRA"
fi

# Afficher les options
echo "Options de fine-tuning:"
echo "- USE_SMALLER_MODEL: $USE_SMALLER_MODEL"
echo "- ALTERNATIVE_MODEL: $ALTERNATIVE_MODEL"
if [ ! -z "$EPOCHS" ]; then
    echo "- EPOCHS: $EPOCHS"
fi
if [ ! -z "$BATCH_SIZE" ]; then
    echo "- BATCH_SIZE: $BATCH_SIZE"
fi
if [ ! -z "$OUTPUT_PATH" ]; then
    echo "- OUTPUT_PATH: $OUTPUT_PATH"
fi
echo "- CLEAN_OUTPUT: $CLEAN_OUTPUT"
echo "- CONTINUE_TRAINING: $CONTINUE_TRAINING"
if [ ! -z "$EXISTING_MODEL" ]; then
    echo "- EXISTING_MODEL: $EXISTING_MODEL"
fi

# Exporter les variables d'environnement
export USE_SMALLER_MODEL=$USE_SMALLER_MODEL
export ALTERNATIVE_MODEL=$ALTERNATIVE_MODEL
if [ ! -z "$EPOCHS" ]; then
    export EPOCHS=$EPOCHS
fi
if [ ! -z "$BATCH_SIZE" ]; then
    export BATCH_SIZE=$BATCH_SIZE
fi
if [ ! -z "$OUTPUT_PATH" ]; then
    export OUTPUT_MODEL=$OUTPUT_PATH
fi
export CLEAN_OUTPUT=$CLEAN_OUTPUT
export CONTINUE_TRAINING=$CONTINUE_TRAINING
if [ ! -z "$EXISTING_MODEL" ]; then
    export EXISTING_MODEL=$EXISTING_MODEL
fi

# Nettoyer le dossier de sortie si demandé
if [ "$CLEAN_OUTPUT" = "true" ] && [ ! -z "$OUTPUT_PATH" ]; then
    echo "Nettoyage du dossier de sortie: $OUTPUT_PATH"
    rm -rf "$OUTPUT_PATH"
fi

# Installer les dépendances
echo "Installation des dépendances..."
pip install -r requirements.txt

# Exécuter le fine-tuning
echo "Démarrage du fine-tuning..."
python huggingface_finetune.py

# Désactiver l'environnement virtuel
echo "Fin du script. Désactivation de l'environnement virtuel..."
deactivate

echo "Le fine-tuning est terminé. Votre modèle est disponible dans le dossier $OUTPUT_MODEL" 