#!/bin/bash

# Script pour nettoyer la mémoire GPU avant le fine-tuning

echo "Nettoyage de la mémoire GPU..."

# Activer l'environnement virtuel
source ./venv/bin/activate

# Exécuter un script Python pour libérer la mémoire GPU
python -c "
import torch
import gc

# Vider le cache CUDA
if torch.cuda.is_available():
    print('Mémoire GPU avant nettoyage:')
    print(torch.cuda.memory_summary())
    
    # Libérer la mémoire
    torch.cuda.empty_cache()
    gc.collect()
    
    print('\nMémoire GPU après nettoyage:')
    print(torch.cuda.memory_summary())
    print('\nNettoyage terminé!')
else:
    print('CUDA n\'est pas disponible sur ce système.')
"

# Désactiver l'environnement virtuel
deactivate

echo "Vous pouvez maintenant exécuter le fine-tuning avec ./run_finetune.sh" 