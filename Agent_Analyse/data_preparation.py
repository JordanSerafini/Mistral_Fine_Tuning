#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour préparer les données d'entraînement pour le fine-tuning de Mistral 7B Instruct.
"""

import os
import json
import pandas as pd
from sklearn.model_selection import train_test_split
from datasets import Dataset
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Préparation des données pour le fine-tuning")
    parser.add_argument("--data_dir", type=str, default="./data", 
                        help="Répertoire contenant les données brutes")
    parser.add_argument("--output_dir", type=str, default="./data/processed", 
                        help="Répertoire où sauvegarder les données traitées")
    parser.add_argument("--test_size", type=float, default=0.1, 
                        help="Proportion de données pour le test (0.1 = 10%)")
    return parser.parse_args()

def convert_to_mistral_format(examples):
    """
    Convertit les exemples au format attendu par Mistral 7B Instruct
    Format: <s>[INST] Instruction ou question [/INST] Réponse attendue </s>
    """
    formatted_examples = []
    
    for example in examples:
        # Si vos données ont un format différent, adaptez ce code
        instruction = example.get("instruction", "")
        input_text = example.get("input", "")
        output = example.get("output", "")
        
        # Combiner instruction et input si les deux sont présents
        if input_text:
            prompt = f"{instruction}\n\n{input_text}"
        else:
            prompt = instruction
            
        # Formater au format Mistral 7B Instruct
        formatted_text = f"<s>[INST] {prompt} [/INST] {output} </s>"
        
        formatted_examples.append({
            "text": formatted_text,
            "prompt": prompt,
            "completion": output
        })
    
    return formatted_examples

def main():
    args = parse_args()
    
    # Créer le répertoire de sortie s'il n'existe pas
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"Chargement des données depuis {args.data_dir}...")
    
    # Charger les données brutes (à adapter selon votre format)
    # Exemple avec des fichiers JSON
    data = []
    data_files = [f for f in os.listdir(args.data_dir) if f.endswith('.json')]
    
    if not data_files:
        print(f"Aucun fichier JSON trouvé dans {args.data_dir}. Veuillez y placer vos données.")
        print("Format attendu: liste d'objets JSON avec des champs 'instruction', 'input' (optionnel) et 'output'")
        # Créer un exemple de fichier
        example = [
            {
                "instruction": "Explique le concept de l'intelligence artificielle en termes simples.",
                "input": "", 
                "output": "L'intelligence artificielle est un domaine de l'informatique qui vise à créer des machines capables de simuler l'intelligence humaine. Cela inclut l'apprentissage, le raisonnement et l'auto-correction. En termes simples, c'est la création d'ordinateurs qui peuvent penser et apprendre comme les humains."
            }
        ]
        with open(os.path.join(args.data_dir, "example.json"), "w", encoding="utf-8") as f:
            json.dump(example, f, ensure_ascii=False, indent=2)
        print(f"Un fichier d'exemple a été créé: {os.path.join(args.data_dir, 'example.json')}")
        return
        
    for file in data_files:
        file_path = os.path.join(args.data_dir, file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                if isinstance(file_data, list):
                    data.extend(file_data)
                else:
                    data.append(file_data)
        except Exception as e:
            print(f"Erreur lors du chargement de {file_path}: {e}")
    
    if not data:
        print("Aucune donnée n'a pu être chargée. Vérifiez le format de vos fichiers.")
        return
        
    print(f"Nombre d'exemples chargés: {len(data)}")
    
    # Convertir au format attendu par Mistral
    formatted_data = convert_to_mistral_format(data)
    
    # Créer un DataFrame pour une manipulation plus facile
    df = pd.DataFrame(formatted_data)
    
    # Diviser en ensembles d'entraînement et de test
    train_df, test_df = train_test_split(df, test_size=args.test_size, random_state=42)
    
    print(f"Ensemble d'entraînement: {len(train_df)} exemples")
    print(f"Ensemble de test: {len(test_df)} exemples")
    
    # Convertir en format datasets de Hugging Face
    train_dataset = Dataset.from_pandas(train_df)
    test_dataset = Dataset.from_pandas(test_df)
    
    # Sauvegarder les datasets
    train_dataset.save_to_disk(os.path.join(args.output_dir, "train"))
    test_dataset.save_to_disk(os.path.join(args.output_dir, "test"))
    
    print(f"Données traitées sauvegardées dans {args.output_dir}")
    print("Exemple de format de données:")
    print(df["text"].iloc[0])

if __name__ == "__main__":
    main() 