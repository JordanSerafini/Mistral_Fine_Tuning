#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour fine-tuner le modèle Mistral 7B Instruct avec la technique LoRA/QLoRA.
"""

import os
import torch
import argparse
from datasets import load_from_disk
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    set_seed,
    logging
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer

def parse_args():
    parser = argparse.ArgumentParser(description="Fine-tuning de Mistral 7B Instruct avec LoRA/QLoRA")
    parser.add_argument("--base_model", type=str, default="mistralai/Mistral-7B-Instruct-v0.2",
                      help="Modèle de base à fine-tuner")
    parser.add_argument("--data_dir", type=str, default="./data/processed",
                      help="Répertoire contenant les données traitées")
    parser.add_argument("--output_dir", type=str, default="./output",
                      help="Répertoire où sauvegarder le modèle fine-tuné")
    parser.add_argument("--epochs", type=int, default=3,
                      help="Nombre d'époques d'entraînement")
    parser.add_argument("--batch_size", type=int, default=8,
                      help="Taille du batch pour l'entraînement")
    parser.add_argument("--lr", type=float, default=2e-4,
                      help="Taux d'apprentissage")
    parser.add_argument("--lora_r", type=int, default=8,
                      help="Rang pour LoRA")
    parser.add_argument("--lora_alpha", type=int, default=16,
                      help="Alpha pour LoRA")
    parser.add_argument("--lora_dropout", type=float, default=0.05,
                      help="Dropout pour LoRA")
    parser.add_argument("--seed", type=int, default=42,
                      help="Seed pour la reproductibilité")
    parser.add_argument("--max_seq_length", type=int, default=2048,
                      help="Longueur maximale de séquence")
    parser.add_argument("--gradient_accumulation_steps", type=int, default=4,
                      help="Nombre d'étapes pour l'accumulation du gradient")
    parser.add_argument("--use_wandb", action="store_true",
                      help="Utiliser Weights & Biases pour le suivi")
    parser.add_argument("--wandb_project", type=str, default="mistral-7b-finetune",
                      help="Nom du projet W&B")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Configuration de la reproductibilité
    set_seed(args.seed)
    
    # Configurer la journalisation
    logging.set_verbosity_info()
    
    # Créer le répertoire de sortie s'il n'existe pas
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"Chargement du modèle de base: {args.base_model}")
    
    # Configuration quantization (4 bits pour QLoRA)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16
    )
    
    # Charger le modèle de base
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )
    
    # Préparer le modèle pour l'entraînement en k-bits
    model = prepare_model_for_kbit_training(model)
    
    # Charger le tokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    
    # Assurez-vous que le tokenizer a un pad_token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Configuration LoRA
    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    # Appliquer LoRA au modèle
    model = get_peft_model(model, lora_config)
    
    # Imprimer le nombre de paramètres entraînables
    model.print_trainable_parameters()
    
    # Charger les données
    train_dataset = load_from_disk(os.path.join(args.data_dir, "train"))
    eval_dataset = load_from_disk(os.path.join(args.data_dir, "test"))
    
    print(f"Taille de l'ensemble d'entraînement: {len(train_dataset)}")
    print(f"Taille de l'ensemble d'évaluation: {len(eval_dataset)}")
    
    # Configuration de l'entraînement
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        evaluation_strategy="steps",
        eval_steps=0.1,  # Évaluer tous les 10% des étapes
        save_strategy="steps",
        save_steps=0.1,  # Sauvegarder tous les 10% des étapes
        save_total_limit=3,  # Garder seulement les 3 meilleurs checkpoints
        learning_rate=args.lr,
        weight_decay=0.01,
        fp16=True,
        load_best_model_at_end=True,
        logging_dir=os.path.join(args.output_dir, "logs"),
        logging_steps=10,
        report_to="wandb" if args.use_wandb else "tensorboard",
        run_name=f"mistral-7b-finetune-{args.seed}" if args.use_wandb else None,
        push_to_hub=False,
    )
    
    # Configurer le trainer
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        dataset_text_field="text",
        tokenizer=tokenizer,
        max_seq_length=args.max_seq_length,
        packing=True,
    )
    
    # Lancer l'entraînement
    print("Début de l'entraînement...")
    trainer.train()
    
    # Sauvegarder le modèle final
    trainer.save_model(os.path.join(args.output_dir, "final"))
    
    print(f"Entraînement terminé! Modèle sauvegardé dans {os.path.join(args.output_dir, 'final')}")

if __name__ == "__main__":
    main() 