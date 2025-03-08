#!/usr/bin/env python3
"""
Script pour utiliser le modèle fine-tuné pour l'inférence.
"""

import os
import argparse
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel, PeftConfig

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv()

# Configuration
MODEL_PATH = os.getenv("MODEL_PATH", "jordanS/analyse_agent")
BASE_MODEL = os.getenv("BASE_MODEL", "mistralai/Mistral-7B-v0.1")

def load_model(model_path, base_model=None, use_8bit=False, use_4bit=True):
    """Charger le modèle fine-tuné"""
    print(f"Chargement du modèle depuis {model_path}...")
    
    # Vérifier si le modèle est un modèle PEFT (LoRA)
    try:
        config = PeftConfig.from_pretrained(model_path)
        is_peft_model = True
        base_model_path = base_model or config.base_model_name_or_path
        print(f"Modèle PEFT détecté, chargement du modèle de base: {base_model_path}")
    except:
        is_peft_model = False
        base_model_path = model_path
        print(f"Modèle standard détecté: {base_model_path}")
    
    # Configurer la quantification si nécessaire
    if use_4bit:
        from transformers import BitsAndBytesConfig
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16
        )
    elif use_8bit:
        quantization_config = {"load_in_8bit": True}
    else:
        quantization_config = None
    
    # Charger le tokenizer
    tokenizer = AutoTokenizer.from_pretrained(base_model_path)
    
    # Charger le modèle de base
    if quantization_config:
        if use_4bit:
            model = AutoModelForCausalLM.from_pretrained(
                base_model_path,
                quantization_config=quantization_config,
                device_map="auto",
                torch_dtype=torch.float16
            )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                base_model_path,
                load_in_8bit=True,
                device_map="auto",
                torch_dtype=torch.float16
            )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            device_map="auto",
            torch_dtype=torch.float16
        )
    
    # Charger les adaptateurs LoRA si c'est un modèle PEFT
    if is_peft_model:
        model = PeftModel.from_pretrained(model, model_path)
    
    return model, tokenizer

def generate_response(model, tokenizer, prompt, system_prompt=None, max_length=1024, temperature=0.7):
    """Générer une réponse à partir du prompt"""
    # Formater le prompt avec le format Mistral
    if system_prompt:
        formatted_prompt = f"<s>[INST] {system_prompt}\n\n{prompt} [/INST]"
    else:
        formatted_prompt = f"<s>[INST] {prompt} [/INST]"
    
    # Tokeniser le prompt
    inputs = tokenizer(formatted_prompt, return_tensors="pt").to(model.device)
    
    # Générer la réponse
    with torch.no_grad():
        outputs = model.generate(
            inputs.input_ids,
            max_length=max_length,
            temperature=temperature,
            do_sample=True,
            top_p=0.95,
            top_k=50,
            repetition_penalty=1.1
        )
    
    # Décoder la réponse
    response = tokenizer.decode(outputs[0], skip_special_tokens=False)
    
    # Extraire la partie après [/INST]
    response = response.split("[/INST]")[-1].strip()
    
    # Supprimer le token de fin de séquence
    response = response.replace("</s>", "").strip()
    
    return response

def interactive_mode(model, tokenizer, system_prompt=None):
    """Mode interactif pour discuter avec le modèle"""
    print("\n" + "="*50)
    print("Mode interactif. Tapez 'exit' ou 'quit' pour quitter.")
    print("="*50 + "\n")
    
    if system_prompt:
        print(f"System prompt: {system_prompt}\n")
    
    while True:
        user_input = input("\nVous: ")
        
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Au revoir!")
            break
        
        print("\nRéflexion en cours...")
        response = generate_response(model, tokenizer, user_input, system_prompt)
        print(f"\nAssistant: {response}")

def main():
    parser = argparse.ArgumentParser(description="Utiliser le modèle fine-tuné pour l'inférence")
    parser.add_argument("--model_path", type=str, default=MODEL_PATH, help="Chemin vers le modèle fine-tuné")
    parser.add_argument("--base_model", type=str, default=BASE_MODEL, help="Modèle de base (pour les modèles LoRA)")
    parser.add_argument("--prompt", type=str, help="Prompt à utiliser pour l'inférence")
    parser.add_argument("--system_prompt", type=str, default="Tu es un assistant IA expert en analyse de documents pour une entreprise de construction.", help="System prompt")
    parser.add_argument("--interactive", action="store_true", help="Mode interactif")
    parser.add_argument("--use_8bit", action="store_true", help="Utiliser la quantification 8-bit")
    parser.add_argument("--use_4bit", action="store_true", default=True, help="Utiliser la quantification 4-bit")
    
    args = parser.parse_args()
    
    # Charger le modèle
    model, tokenizer = load_model(args.model_path, args.base_model, args.use_8bit, args.use_4bit)
    
    # Mode interactif ou génération unique
    if args.interactive:
        interactive_mode(model, tokenizer, args.system_prompt)
    elif args.prompt:
        response = generate_response(model, tokenizer, args.prompt, args.system_prompt)
        print(f"\nRéponse: {response}")
    else:
        print("Veuillez spécifier un prompt avec --prompt ou utiliser le mode interactif avec --interactive")

if __name__ == "__main__":
    main() 