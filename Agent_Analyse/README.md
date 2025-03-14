# Fine-tuning de Mistral 7B Instruct

Ce projet vise à fine-tuner le modèle Mistral 7B Instruct et à le déployer sur un endpoint pour être utilisé dans une API.

## Structure du projet

- `requirements.txt` : Liste des dépendances Python nécessaires
- `train.py` : Script pour le fine-tuning du modèle
- `data_preparation.py` : Script pour préparer les données d'entraînement
- `inference.py` : Script pour l'inférence et le test du modèle
- `deploy.py` : Script pour déployer le modèle sur un endpoint
- `data/` : Dossier contenant les données d'entraînement

## Configuration requise

- Python 3.8+
- PyTorch 2.0+
- Accès à un GPU pour l'entraînement (fortement recommandé)

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

1. Préparer les données d'entraînement
```bash
python data_preparation.py
```

2. Fine-tuner le modèle
```bash
python train.py
```

3. Tester le modèle
```bash
python inference.py
```

4. Déployer le modèle
```bash
python deploy.py
``` 