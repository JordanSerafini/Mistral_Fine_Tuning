import os
import json
import argparse
from dotenv import load_dotenv
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig
)
import torch
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# Configuration pour éviter la fragmentation de la mémoire CUDA
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

# Charger les variables d'environnement
load_dotenv()

# Configuration
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
BASE_MODEL = os.getenv("BASE_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
OUTPUT_MODEL = os.getenv("OUTPUT_MODEL", "jordanS/analyse_agent")
MODEL_ID = os.getenv("MODEL_ID", "jordanS/analyse_agent")

# Options pour personnaliser l'entraînement
EPOCHS = os.getenv("EPOCHS", "")  # Vide par défaut, sera défini plus tard
BATCH_SIZE = os.getenv("BATCH_SIZE", "")  # Vide par défaut, sera défini plus tard
CLEAN_OUTPUT = os.getenv("CLEAN_OUTPUT", "false").lower() == "true"

# Option pour utiliser un modèle plus petit si la mémoire est insuffisante
USE_SMALLER_MODEL = os.getenv("USE_SMALLER_MODEL", "True").lower() == "true"
ALTERNATIVE_MODEL = os.getenv("ALTERNATIVE_MODEL", "False").lower() == "true"

if USE_SMALLER_MODEL:
    print("Utilisation d'un modèle plus petit pour économiser la mémoire...")
    if ALTERNATIVE_MODEL:
        print("Utilisation du modèle alternatif (GPT2)...")
        BASE_MODEL = "gpt2"  # Modèle encore plus petit et plus simple
    else:
        BASE_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # Modèle beaucoup plus petit (1.1B au lieu de 7B)

# Définir les chemins des fichiers d'entraînement
TRAINING_FILES = [
    os.path.join(os.path.dirname(__file__), "data", "training", "analyse_agent_data.jsonl"),
    os.path.join(os.path.dirname(__file__), "data", "training", "analyse_agent_data-set2.jsonl")
]

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
    """Fonction principale pour le fine-tuning avec Hugging Face"""
    print("Démarrage du fine-tuning avec Hugging Face...")
    
    # 1. Charger les données d'entraînement
    raw_data = load_training_data(TRAINING_FILES)
    
    # 2. Formater les données pour l'entraînement
    formatted_data = format_data_for_training(raw_data)
    
    # 3. Créer un dataset Hugging Face
    dataset = Dataset.from_list(formatted_data)
    
    # 4. Charger le tokenizer et le modèle
    print(f"Chargement du modèle {BASE_MODEL}...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, token=HF_API_KEY)
    
    # Configurer le tokenizer
    tokenizer.pad_token = tokenizer.eos_token
    
    # 5. Tokeniser les données
    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=1024)
    
    tokenized_dataset = dataset.map(tokenize_function, batched=True)
    
    # 6. Charger le modèle en fonction de la taille
    if USE_SMALLER_MODEL:
        if ALTERNATIVE_MODEL:
            # Pour GPT2, pas besoin de quantification
            print("Chargement du modèle GPT2 sans quantification...")
            model = AutoModelForCausalLM.from_pretrained(
                BASE_MODEL,
                device_map="auto",
                token=HF_API_KEY,
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True
            )
        else:
            # Pour TinyLlama, utiliser QLoRA avec quantification 4-bit
            print("Chargement du modèle TinyLlama avec QLoRA (quantification 4-bit)...")
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
                token=HF_API_KEY,
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True
            )
            
            # Préparer le modèle pour l'entraînement 4-bit
            model = prepare_model_for_kbit_training(model)
    else:
        # Pour les grands modèles, utiliser QLoRA avec quantification 4-bit
        print("Chargement du modèle Mistral avec QLoRA (quantification 4-bit)...")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            llm_int8_enable_fp32_cpu_offload=True
        )
        
        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            quantization_config=bnb_config,
            device_map="auto",
            token=HF_API_KEY,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True
        )
        
        # Préparer le modèle pour l'entraînement 4-bit
        model = prepare_model_for_kbit_training(model)
    
    # 7. Configurer LoRA pour un fine-tuning efficace
    if USE_SMALLER_MODEL:
        if ALTERNATIVE_MODEL:
            # Configuration LoRA adaptée à GPT2
            peft_config = LoraConfig(
                r=8,
                lora_alpha=16,
                lora_dropout=0.05,
                bias="none",
                task_type="CAUSAL_LM",
                target_modules=["c_attn", "c_proj", "c_fc"]  # Modules spécifiques à GPT2
            )
        else:
            # Pour TinyLlama avec QLoRA
            peft_config = LoraConfig(
                r=8,  # Réduire pour économiser la mémoire
                lora_alpha=16,
                lora_dropout=0.05,
                bias="none",
                task_type="CAUSAL_LM",
                target_modules=["q_proj", "v_proj", "k_proj", "o_proj"]
            )
    else:
        # Pour les grands modèles avec QLoRA
        peft_config = LoraConfig(
            r=4,  # Valeur équilibrée pour QLoRA
            lora_alpha=16,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj"]
        )
    
    # 8. Préparer le modèle pour le fine-tuning avec LoRA
    if not (USE_SMALLER_MODEL and ALTERNATIVE_MODEL):
        # Pas besoin de préparer GPT2 pour l'entraînement 4-bit
        print("Application de QLoRA au modèle...")
    
    model = get_peft_model(model, peft_config)
    
    # Afficher le nombre de paramètres entraînables vs total
    model.print_trainable_parameters()
    
    # 9. Configurer l'entraînement
    if USE_SMALLER_MODEL:
        if ALTERNATIVE_MODEL:
            # Pour GPT2
            epochs = int(EPOCHS) if EPOCHS else 3
            batch_size = int(BATCH_SIZE) if BATCH_SIZE else 4
            
            training_args = TrainingArguments(
                output_dir=OUTPUT_MODEL,
                per_device_train_batch_size=batch_size,
                gradient_accumulation_steps=4,
                num_train_epochs=epochs,
                learning_rate=5e-4,
                fp16=True,
                logging_steps=10,
                save_steps=100,
                save_total_limit=2,
                push_to_hub=False,
                gradient_checkpointing=False,  # Désactiver pour GPT2
                optim="adamw_torch_fused",
            )
        else:
            # Pour TinyLlama avec QLoRA
            epochs = int(EPOCHS) if EPOCHS else 3
            batch_size = int(BATCH_SIZE) if BATCH_SIZE else 2
            
            training_args = TrainingArguments(
                output_dir=OUTPUT_MODEL,
                per_device_train_batch_size=batch_size,
                gradient_accumulation_steps=8,
                num_train_epochs=epochs,
                learning_rate=2e-4,
                fp16=True,
                logging_steps=10,
                save_steps=100,
                save_total_limit=2,
                push_to_hub=False,
                gradient_checkpointing=True,  # Activer pour QLoRA
                optim="paged_adamw_8bit",  # Optimiseur optimisé pour QLoRA
                max_grad_norm=0.3,
            )
    else:
        # Pour les grands modèles avec QLoRA
        epochs = int(EPOCHS) if EPOCHS else 2
        batch_size = int(BATCH_SIZE) if BATCH_SIZE else 1
        
        training_args = TrainingArguments(
            output_dir=OUTPUT_MODEL,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=16,
            num_train_epochs=epochs,
            learning_rate=1e-4,
            fp16=True,
            logging_steps=10,
            save_steps=200,
            save_total_limit=1,
            push_to_hub=False,
            gradient_checkpointing=True,
            optim="paged_adamw_8bit",  # Optimiseur optimisé pour QLoRA
            max_grad_norm=0.3,
        )
    
    # 10. Créer le data collator
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    
    # 11. Créer le trainer avec device_map=None pour éviter les problèmes de déplacement
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
    
    # 14. Pousser le modèle sur Hugging Face Hub
    if training_args.push_to_hub:
        print(f"Publication du modèle sur Hugging Face Hub: {MODEL_ID}")
        trainer.push_to_hub()
    else:
        print(f"Le modèle est sauvegardé localement dans: {OUTPUT_MODEL}")
    
    print("Fine-tuning terminé avec succès !")
    if training_args.push_to_hub:
        print(f"Votre modèle est disponible à l'adresse: https://huggingface.co/{MODEL_ID}")
    else:
        print(f"Votre modèle est disponible localement dans: {OUTPUT_MODEL}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune a language model for construction company analysis")
    args = parser.parse_args()
    
    fine_tune_model() 