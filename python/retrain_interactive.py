#!/usr/bin/env python3
import os
import glob
import subprocess
import sys
import json

def clear_screen():
    """Nettoie l'écran du terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')

def list_training_files():
    """Liste tous les fichiers d'entraînement disponibles"""
    training_dir = os.path.join(os.path.dirname(__file__), "data", "training")
    files = glob.glob(os.path.join(training_dir, "*.jsonl"))
    return files

def select_files(files):
    """Permet à l'utilisateur de sélectionner un ou plusieurs fichiers"""
    selected = []
    
    while True:
        clear_screen()
        print("=== SÉLECTION DES FICHIERS D'ENTRAÎNEMENT ===\n")
        
        for i, file in enumerate(files, 1):
            filename = os.path.basename(file)
            status = "[X]" if file in selected else "[ ]"
            print(f"{i}. {status} {filename}")
        
        print("\nCommandes disponibles:")
        print("- Entrez un numéro pour sélectionner/désélectionner un fichier")
        print("- 'a' pour tout sélectionner")
        print("- 'n' pour ne rien sélectionner")
        print("- 'c' pour continuer avec la sélection actuelle")
        print("- 'q' pour quitter")
        
        choice = input("\nVotre choix: ").strip().lower()
        
        if choice == 'q':
            sys.exit(0)
        elif choice == 'a':
            selected = files.copy()
        elif choice == 'n':
            selected = []
        elif choice == 'c':
            if not selected:
                print("\nVeuillez sélectionner au moins un fichier.")
                input("Appuyez sur Entrée pour continuer...")
                continue
            return selected
        else:
            try:
                index = int(choice) - 1
                if 0 <= index < len(files):
                    if files[index] in selected:
                        selected.remove(files[index])
                    else:
                        selected.append(files[index])
                else:
                    print("\nNuméro invalide.")
                    input("Appuyez sur Entrée pour continuer...")
            except ValueError:
                print("\nEntrée invalide.")
                input("Appuyez sur Entrée pour continuer...")

def select_model():
    models = [
        "mistralai/Mistral-7B-v0.1",
        "mistralai/Mistral-7B-Instruct-v0.1",
        "mistralai/Mistral-7B-Instruct-v0.2",
        "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "gpt2"
    ]
    
    print("\n=== SÉLECTION DU MODÈLE DE BASE ===")
    print("Choisissez un modèle de base:")
    
    for i, model in enumerate(models, 1):
        print(f"{i}. {model}")
    
    choice = input("\nVotre choix (1-5): ")
    
    try:
        index = int(choice) - 1
        if 0 <= index < len(models):
            return models[index]
        else:
            print("Choix invalide. Utilisation du modèle par défaut.")
            return models[0]  # Utiliser Mistral-7B-v0.1 comme modèle par défaut
    except ValueError:
        print("Entrée invalide. Utilisation du modèle par défaut.")
        return models[0]  # Utiliser Mistral-7B-v0.1 comme modèle par défaut

def configure_training():
    """Configure les paramètres d'entraînement"""
    clear_screen()
    print("=== CONFIGURATION DE L'ENTRAÎNEMENT ===\n")
    
    # Modèle de base
    base_model = select_model()
    
    # Nombre d'époques
    epochs = input("\nNombre d'époques (défaut: 3 pour petits modèles, 2 pour grands): ").strip()
    if not epochs:
        epochs = "3" if "TinyLlama" in base_model or "gpt2" in base_model else "2"
    
    # Taille du batch
    batch_size = input("\nTaille du batch (défaut: 4 pour GPT2, 2 pour TinyLlama, 1 pour Mistral): ").strip()
    if not batch_size:
        if "TinyLlama" in base_model or "gpt2" in base_model:
            batch_size = "4"
        else:
            batch_size = "1"
    
    # Nom du modèle de sortie
    output_model = input("\nNom du modèle de sortie (défaut: jordanS/agent_router): ").strip()
    if not output_model:
        output_model = "jordanS/agent_router"
    
    # Continuer l'entraînement
    continue_training = input("\nContinuer l'entraînement à partir d'un modèle existant? (o/n, défaut: n): ").strip().lower()
    continue_training = "true" if continue_training == "o" else "false"
    
    # Modèle existant si continuation
    existing_model = ""
    if continue_training == "true":
        existing_model = input("\nChemin du modèle existant: ").strip()
        if not existing_model:
            existing_model = output_model
    
    # Nettoyer le dossier de sortie
    clean_output = input("\nNettoyer le dossier de sortie? (o/n, défaut: n): ").strip().lower()
    clean_output = "true" if clean_output == "o" else "false"
    
    return {
        "BASE_MODEL": base_model,
        "EPOCHS": epochs,
        "BATCH_SIZE": batch_size,
        "OUTPUT_MODEL": output_model,
        "CONTINUE_TRAINING": continue_training,
        "EXISTING_MODEL": existing_model,
        "CLEAN_OUTPUT": clean_output
    }

def create_training_file(selected_files):
    """Crée un fichier temporaire avec les chemins des fichiers sélectionnés"""
    temp_file = os.path.join(os.path.dirname(__file__), "selected_training_files.py")
    
    with open(temp_file, 'w') as f:
        f.write("# Fichier généré automatiquement par retrain_interactive.py\n")
        f.write("# Ne pas modifier manuellement\n\n")
        f.write("import os\n\n")
        f.write("# Fichiers d'entraînement sélectionnés\n")
        f.write("TRAINING_FILES = [\n")
        
        for file in selected_files:
            f.write(f"    \"{file}\",\n")
        
        f.write("]\n")
    
    return temp_file

def run_training(config, training_files_module, selected_files):
    """Exécute l'entraînement avec les paramètres configurés"""
    clear_screen()
    print("=== DÉMARRAGE DE L'ENTRAÎNEMENT ===\n")
    
    # Définir les variables d'environnement
    env = os.environ.copy()
    for key, value in config.items():
        env[key] = value
    
    # Modifier le code pour utiliser notre module de fichiers sélectionnés
    env["SELECTED_TRAINING_FILES"] = training_files_module
    
    # Exécuter le script de fine-tuning
    print("Lancement de l'entraînement avec les paramètres suivants:")
    for key, value in config.items():
        if value:  # Ne pas afficher les valeurs vides
            print(f"- {key}: {value}")
    
    print("\nFichiers d'entraînement sélectionnés:")
    for file in selected_files:
        print(f"- {os.path.basename(file)}")
    
    print("\nDémarrage de l'entraînement...")
    
    # Créer un script temporaire qui utilise les fichiers sélectionnés
    temp_script = os.path.join(os.path.dirname(__file__), "temp_finetune.py")
    
    # Lire le contenu du fichier original
    with open(os.path.join(os.path.dirname(__file__), "huggingface_finetune.py"), 'r') as src:
        content = src.read()
    
    # Trouver la position de la définition de TRAINING_FILES
    training_files_start = content.find("# Définir les chemins des fichiers d'entraînement\nTRAINING_FILES = [")
    training_files_end = content.find("]", training_files_start)
    
    if training_files_start != -1 and training_files_end != -1:
        # Créer le nouveau contenu
        new_content = content[:training_files_start]
        new_content += "# Utiliser les fichiers sélectionnés\nimport json\nwith open('" + training_files_module + "', 'r') as f:\n    TRAINING_FILES = json.load(f)\n\n"
        new_content += content[training_files_end+1:]
        
        # Écrire le nouveau contenu dans le fichier temporaire
        with open(temp_script, 'w') as dst:
            dst.write(new_content)
    else:
        print("Erreur: Impossible de trouver la définition de TRAINING_FILES dans le fichier source.")
        return
    
    try:
        # Écrire les fichiers sélectionnés dans un fichier JSON temporaire
        with open(training_files_module, 'w') as f:
            # Ne pas redemander la sélection des fichiers, utiliser ceux déjà sélectionnés
            print("DEBUG: selected_files =", selected_files)
            json.dump([os.path.abspath(file) for file in selected_files], f)
        
        # Exécuter le script temporaire
        process = subprocess.Popen(
            [sys.executable, temp_script],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Afficher la sortie en temps réel
        for line in iter(process.stdout.readline, ''):
            print(line, end='')
        
        process.wait()
        
        if process.returncode == 0:
            print("\nL'entraînement s'est terminé avec succès!")
        else:
            print(f"\nL'entraînement s'est terminé avec le code d'erreur: {process.returncode}")
    
    finally:
        # Nettoyer les fichiers temporaires
        if os.path.exists(temp_script):
            os.remove(temp_script)
        if os.path.exists(training_files_module):
            os.remove(training_files_module)

def main():
    """Fonction principale"""
    # Lister les fichiers d'entraînement disponibles
    files = list_training_files()
    
    if not files:
        print("Aucun fichier d'entraînement trouvé dans le répertoire data/training.")
        sys.exit(1)
    
    # Sélectionner les fichiers
    selected_files = select_files(files)
    
    # Configurer l'entraînement
    config = configure_training()
    
    # Créer un fichier temporaire avec les chemins des fichiers sélectionnés
    training_files_module = os.path.join(os.path.dirname(__file__), "selected_files.json")
    
    # Exécuter l'entraînement
    run_training(config, training_files_module, selected_files)

if __name__ == "__main__":
    main() 