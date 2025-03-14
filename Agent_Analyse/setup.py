#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour préparer l'environnement et créer les dossiers nécessaires.
"""

import os
import shutil
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Préparation de l'environnement")
    parser.add_argument("--force", action="store_true",
                      help="Forcer la recréation des dossiers (supprime les données existantes)")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Liste des dossiers à créer
    directories = [
        "data",
        "data/raw",
        "data/processed",
        "output",
        "output/logs"
    ]
    
    # Créer les dossiers
    for directory in directories:
        if os.path.exists(directory) and args.force:
            print(f"Suppression du dossier existant: {directory}")
            shutil.rmtree(directory)
        
        if not os.path.exists(directory):
            print(f"Création du dossier: {directory}")
            os.makedirs(directory)
        else:
            print(f"Le dossier existe déjà: {directory}")
    
    # Créer le fichier .env s'il n'existe pas
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            print("Copie du fichier .env.example vers .env")
            shutil.copy(".env.example", ".env")
            print("Veuillez modifier le fichier .env avec vos propres valeurs.")
        else:
            print("AVERTISSEMENT: Le fichier .env.example n'existe pas. Impossible de créer le fichier .env.")
    else:
        print("Le fichier .env existe déjà.")
    
    print("\nL'environnement a été préparé avec succès!")
    print("\nÉtapes suivantes:")
    print("1. Placez vos données d'entraînement dans le dossier 'data/raw'")
    print("2. Exécutez 'python data_preparation.py' pour préparer les données")
    print("3. Exécutez 'python train.py' pour entraîner le modèle")
    print("4. Testez le modèle avec 'python inference.py --use_gradio'")
    print("5. Déployez le modèle avec 'python deploy.py'")

if __name__ == "__main__":
    main() 