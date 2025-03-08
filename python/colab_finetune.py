"""
Script pour fine-tuner un modèle Mistral sur Google Colab.
Ce script est conçu pour être exécuté dans un notebook Google Colab.
"""

# Installation des dépendances
# !pip install -q transformers datasets peft bitsandbytes accelerate trl

import os
import json
import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from google.colab import drive

# Configuration pour éviter la fragmentation de la mémoire CUDA
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

# Configuration
BASE_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
OUTPUT_MODEL = "mistral-finetuned"

# Monter Google Drive pour sauvegarder le modèle et accéder aux données
drive.mount('/content/drive')

# Fonction pour charger les données depuis Google Drive
def load_training_data(file_paths):
    """Charger et préparer les données d'entraînement"""
    all_data = []
    
    for file_path in file_paths:
        if os.path.exists(file_path):
            print(f"Chargement du fichier: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                for line in lines:
                    if line.strip():
                        try:
                            item = json.loads(line)
                            all_data.append(item)
                        except json.JSONDecodeError:
                            print(f"Erreur de parsing pour la ligne: {line[:50]}...")
            
            print(f"Chargé {len(lines)} exemples d'entraînement depuis {os.path.basename(file_path)}")
        else:
            print(f"Fichier non trouvé: {file_path}")
    
    print(f"Total: {len(all_data)} exemples d'entraînement chargés")
    
    if len(all_data) == 0:
        raise ValueError("Aucune donnée d'entraînement valide trouvée")
    
    return all_data

def format_data_for_training(data):
    """Convertir les données au format attendu pour le fine-tuning"""
    formatted_data = []
    
    for item in data:
        messages = item.get("messages", [])
        
        system_message = next((msg["content"] for msg in messages if msg["role"] == "system"), "")
        user_message = next((msg["content"] for msg in messages if msg["role"] == "user"), "")
        assistant_message = next((msg["content"] for msg in messages if msg["role"] == "assistant"), "")
        
        # Format pour l'entraînement
        formatted_text = f"<s>[INST] {system_message}\n\n{user_message} [/INST] {assistant_message}</s>"
        
        formatted_data.append({
            "text": formatted_text
        })
    
    return formatted_data

def fine_tune_model():
    """Fonction principale pour le fine-tuning avec Hugging Face sur Colab"""
    print("Démarrage du fine-tuning avec Hugging Face sur Google Colab...")
    
    # 1. Charger les données d'entraînement depuis Google Drive
    TRAINING_FILES = [
        "/content/drive/MyDrive/data/analyse_agent_data.jsonl",
        "/content/drive/MyDrive/data/analyse_agent_data-set2.jsonl"
    ]
    
    raw_data = load_training_data(TRAINING_FILES)
    
    # 2. Formater les données pour l'entraînement
    formatted_data = format_data_for_training(raw_data)
    
    # 3. Créer un dataset Hugging Face
    dataset = Dataset.from_list(formatted_data)
    
    # 4. Charger le tokenizer et le modèle
    print(f"Chargement du modèle {BASE_MODEL}...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    
    # Configurer le tokenizer
    tokenizer.pad_token = tokenizer.eos_token
    
    # 5. Tokeniser les données
    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=1024)
    
    tokenized_dataset = dataset.map(tokenize_function, batched=True)
    
    # 6. Configurer LoRA pour un fine-tuning efficace
    peft_config = LoraConfig(
        r=8,  # Sur Colab, on peut utiliser des valeurs plus élevées
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"]
    )
    
    # 7. Charger le modèle avec quantification 4-bit
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.float16
    )
    
    # Préparer le modèle pour l'entraînement 4-bit
    model = prepare_model_for_kbit_training(model)
    
    # 8. Préparer le modèle pour le fine-tuning avec LoRA
    model = get_peft_model(model, peft_config)
    
    # Afficher le nombre de paramètres entraînables vs total
    model.print_trainable_parameters()
    
    # 9. Configurer l'entraînement
    training_args = TrainingArguments(
        output_dir="/content/drive/MyDrive/models/" + OUTPUT_MODEL,
        per_device_train_batch_size=2,  # Colab a plus de mémoire
        gradient_accumulation_steps=4,
        num_train_epochs=3,
        learning_rate=2e-4,
        fp16=True,
        logging_steps=10,
        save_steps=100,
        save_total_limit=3,
        gradient_checkpointing=True,
        optim="adamw_torch_fused",
    )
    
    # 10. Créer le data collator
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    
    # 11. Créer le trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=data_collator,
    )
    
    # 12. Lancer l'entraînement
    print("Lancement de l'entraînement...")
    trainer.train()
    
    # 13. Sauvegarder le modèle
    print("Sauvegarde du modèle...")
    trainer.save_model()
    
    print("Fine-tuning terminé avec succès !")
    print(f"Votre modèle est disponible dans Google Drive à: /content/drive/MyDrive/models/{OUTPUT_MODEL}")

if __name__ == "__main__":
    fine_tune_model() 