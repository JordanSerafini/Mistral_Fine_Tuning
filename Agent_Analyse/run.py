#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script principal pour exécuter les différentes étapes du projet.
"""

import os
import argparse
import subprocess
import sys
from typing import List, Optional

def parse_args():
    parser = argparse.ArgumentParser(description="Script principal pour le projet de fine-tuning de Mistral 7B")
    
    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")
    
    # Sous-commande pour préparer l'environnement
    setup_parser = subparsers.add_parser("setup", help="Préparer l'environnement")
    setup_parser.add_argument("--force", action="store_true", help="Forcer la recréation des dossiers")
    
    # Sous-commande pour préparer les données
    data_parser = subparsers.add_parser("prepare_data", help="Préparer les données")
    data_parser.add_argument("--data_dir", type=str, default="./data/raw", help="Dossier des données brutes")
    data_parser.add_argument("--output_dir", type=str, default="./data/processed", help="Dossier de sortie")
    
    # Sous-commande pour entraîner le modèle
    train_parser = subparsers.add_parser("train", help="Entraîner le modèle")
    train_parser.add_argument("--base_model", type=str, default="mistralai/Mistral-7B-Instruct-v0.2", help="Modèle de base")
    train_parser.add_argument("--data_dir", type=str, default="./data/processed", help="Dossier des données traitées")
    train_parser.add_argument("--output_dir", type=str, default="./output", help="Dossier de sortie")
    train_parser.add_argument("--epochs", type=int, default=3, help="Nombre d'époques")
    train_parser.add_argument("--batch_size", type=int, default=8, help="Taille du batch")
    train_parser.add_argument("--use_wandb", action="store_true", help="Utiliser Weights & Biases")
    
    # Sous-commande pour tester le modèle
    test_parser = subparsers.add_parser("test", help="Tester le modèle")
    test_parser.add_argument("--base_model", type=str, default="mistralai/Mistral-7B-Instruct-v0.2", help="Modèle de base")
    test_parser.add_argument("--adapter_path", type=str, default="./output/final", help="Chemin vers l'adaptateur")
    test_parser.add_argument("--use_4bit", action="store_true", help="Utiliser la quantification 4-bit")
    test_parser.add_argument("--use_gradio", action="store_true", help="Utiliser l'interface Gradio")
    
    # Sous-commande pour déployer le modèle
    deploy_parser = subparsers.add_parser("deploy", help="Déployer le modèle")
    deploy_parser.add_argument("--base_model", type=str, default="mistralai/Mistral-7B-Instruct-v0.2", help="Modèle de base")
    deploy_parser.add_argument("--adapter_path", type=str, default="./output/final", help="Chemin vers l'adaptateur")
    deploy_parser.add_argument("--use_4bit", action="store_true", help="Utiliser la quantification 4-bit")
    deploy_parser.add_argument("--port", type=int, default=8000, help="Port pour l'API")
    
    # Sous-commande pour exécuter l'ensemble du pipeline
    pipeline_parser = subparsers.add_parser("pipeline", help="Exécuter l'ensemble du pipeline")
    pipeline_parser.add_argument("--base_model", type=str, default="mistralai/Mistral-7B-Instruct-v0.2", help="Modèle de base")
    pipeline_parser.add_argument("--epochs", type=int, default=3, help="Nombre d'époques")
    pipeline_parser.add_argument("--batch_size", type=int, default=8, help="Taille du batch")
    pipeline_parser.add_argument("--use_wandb", action="store_true", help="Utiliser Weights & Biases")
    
    return parser.parse_args()

def run_command(command: List[str], env: Optional[dict] = None) -> int:
    """
    Exécute une commande et retourne le code de sortie
    """
    print(f"Exécution de la commande : {' '.join(command)}")
    
    # Fusionner l'environnement actuel avec celui fourni
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=merged_env
        )
        
        # Afficher la sortie en temps réel
        for line in process.stdout:
            print(line, end='')
            
        process.wait()
        return process.returncode
    except Exception as e:
        print(f"Erreur lors de l'exécution de la commande : {e}")
        return 1

def main():
    args = parse_args()
    
    # Si aucune commande n'est spécifiée, afficher l'aide
    if not args.command:
        print("Aucune commande spécifiée. Utilisez --help pour voir les options disponibles.")
        sys.exit(1)
    
    # Exécuter la commande appropriée
    if args.command == "setup":
        setup_cmd = ["python", "setup.py"]
        if args.force:
            setup_cmd.append("--force")
        return run_command(setup_cmd)
    
    elif args.command == "prepare_data":
        data_cmd = ["python", "data_preparation.py",
                  f"--data_dir={args.data_dir}",
                  f"--output_dir={args.output_dir}"]
        return run_command(data_cmd)
    
    elif args.command == "train":
        train_cmd = ["python", "train.py",
                   f"--base_model={args.base_model}",
                   f"--data_dir={args.data_dir}",
                   f"--output_dir={args.output_dir}",
                   f"--epochs={args.epochs}",
                   f"--batch_size={args.batch_size}"]
        
        if args.use_wandb:
            train_cmd.append("--use_wandb")
            
        return run_command(train_cmd)
    
    elif args.command == "test":
        test_cmd = ["python", "inference.py",
                  f"--base_model={args.base_model}",
                  f"--adapter_path={args.adapter_path}"]
        
        if args.use_4bit:
            test_cmd.append("--use_4bit")
        
        if args.use_gradio:
            test_cmd.append("--use_gradio")
            
        return run_command(test_cmd)
    
    elif args.command == "deploy":
        deploy_cmd = ["python", "deploy.py",
                    f"--base_model={args.base_model}",
                    f"--adapter_path={args.adapter_path}",
                    f"--port={args.port}"]
        
        if args.use_4bit:
            deploy_cmd.append("--use_4bit")
            
        return run_command(deploy_cmd)
    
    elif args.command == "pipeline":
        # Exécuter le pipeline complet
        print("Exécution du pipeline complet...")
        
        # 1. Préparer l'environnement
        setup_result = run_command(["python", "setup.py"])
        if setup_result != 0:
            print("Erreur lors de la préparation de l'environnement")
            return setup_result
        
        # 2. Préparer les données
        data_result = run_command(["python", "data_preparation.py"])
        if data_result != 0:
            print("Erreur lors de la préparation des données")
            return data_result
        
        # 3. Entraîner le modèle
        train_cmd = ["python", "train.py",
                   f"--base_model={args.base_model}",
                   f"--epochs={args.epochs}",
                   f"--batch_size={args.batch_size}"]
        
        if args.use_wandb:
            train_cmd.append("--use_wandb")
            
        train_result = run_command(train_cmd)
        if train_result != 0:
            print("Erreur lors de l'entraînement du modèle")
            return train_result
        
        # 4. Tester le modèle
        test_result = run_command(["python", "inference.py", "--use_gradio"])
        if test_result != 0:
            print("Erreur lors du test du modèle")
            return test_result
        
        print("Pipeline exécuté avec succès!")
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 