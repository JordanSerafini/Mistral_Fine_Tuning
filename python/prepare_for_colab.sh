#!/bin/bash

# Script pour préparer les fichiers pour Google Colab

# Créer un dossier pour les fichiers à envoyer sur Colab
COLAB_DIR="colab_files"
mkdir -p $COLAB_DIR

# Copier les fichiers nécessaires
echo "Préparation des fichiers pour Google Colab..."

# Copier le script de fine-tuning pour Colab
cp colab_finetune.py $COLAB_DIR/

# Créer un dossier pour les données
mkdir -p $COLAB_DIR/data

# Copier les données d'entraînement
cp -r data/training/*.jsonl $COLAB_DIR/data/

# Créer un fichier README
cat > $COLAB_DIR/README.md << EOF
# Fine-tuning sur Google Colab

Ce dossier contient les fichiers nécessaires pour fine-tuner un modèle de langage sur Google Colab.

## Instructions

1. Téléchargez ce dossier sur votre ordinateur
2. Créez un nouveau notebook Google Colab
3. Uploadez les fichiers dans Google Drive
4. Dans le notebook Colab, exécutez:

\`\`\`python
# Installer les dépendances
!pip install -q transformers datasets peft bitsandbytes accelerate trl

# Exécuter le script de fine-tuning
%run colab_finetune.py
\`\`\`

## Fichiers inclus

- \`colab_finetune.py\`: Script principal pour le fine-tuning
- \`data/\`: Dossier contenant les données d'entraînement
EOF

echo "Fichiers préparés dans le dossier $COLAB_DIR"
echo "Vous pouvez maintenant télécharger ce dossier et l'uploader sur Google Drive pour utiliser avec Colab." 