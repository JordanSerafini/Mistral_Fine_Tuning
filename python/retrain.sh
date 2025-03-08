#!/bin/bash

# Script pour lancer l'outil interactif de réentraînement

# Vérifier si nous sommes dans le bon répertoire
if [ ! -f "retrain_interactive.py" ]; then
    echo "Ce script doit être exécuté depuis le répertoire python/"
    exit 1
fi

# Activer l'environnement virtuel si présent
if [ -d "venv" ]; then
    echo "Activation de l'environnement virtuel..."
    source ./venv/bin/activate
fi

# Vérifier les dépendances
echo "Vérification des dépendances..."
python -c "import torch" 2>/dev/null || { echo "Installation de PyTorch..."; pip install torch; }
python -c "import transformers" 2>/dev/null || { echo "Installation de Transformers..."; pip install transformers; }
python -c "import datasets" 2>/dev/null || { echo "Installation de Datasets..."; pip install datasets; }
python -c "import peft" 2>/dev/null || { echo "Installation de PEFT..."; pip install peft; }
python -c "import bitsandbytes" 2>/dev/null || { echo "Installation de BitsAndBytes..."; pip install bitsandbytes; }

# Lancer le script interactif
echo "Lancement de l'outil interactif de réentraînement..."
python retrain_interactive.py

# Désactiver l'environnement virtuel
if [ -d "venv" ]; then
    deactivate
fi 