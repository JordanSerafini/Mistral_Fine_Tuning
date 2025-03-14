#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour tester le modèle Mistral 7B Instruct fine-tuné.
"""

import os
import torch
import argparse
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel
import gradio as gr

def parse_args():
    parser = argparse.ArgumentParser(description="Test du modèle Mistral 7B Instruct fine-tuné")
    parser.add_argument("--base_model", type=str, default="mistralai/Mistral-7B-Instruct-v0.2",
                      help="Modèle de base utilisé pour le fine-tuning")
    parser.add_argument("--adapter_path", type=str, default="./output/final",
                      help="Chemin vers le modèle fine-tuné (adaptateur LoRA)")
    parser.add_argument("--use_4bit", action="store_true",
                      help="Utiliser la quantification 4-bit pour l'inférence")
    parser.add_argument("--max_new_tokens", type=int, default=512,
                      help="Nombre maximum de tokens à générer")
    parser.add_argument("--temperature", type=float, default=0.7,
                      help="Température pour la génération")
    parser.add_argument("--top_p", type=float, default=0.9,
                      help="Top-p pour la génération")
    parser.add_argument("--top_k", type=int, default=50,
                      help="Top-k pour la génération")
    parser.add_argument("--use_gradio", action="store_true",
                      help="Lancer une interface Gradio pour tester le modèle")
    return parser.parse_args()

def format_prompt(prompt):
    """
    Format the prompt in the style expected by Mistral 7B Instruct
    """
    return f"<s>[INST] {prompt} [/INST]"

def generate_response(model, tokenizer, prompt, max_new_tokens=512, temperature=0.7, top_p=0.9, top_k=50):
    """
    Generate a response from the model given a prompt
    """
    formatted_prompt = format_prompt(prompt)
    
    inputs = tokenizer(formatted_prompt, return_tensors="pt").to(model.device)
    
    # Generate response
    with torch.no_grad():
        output = model.generate(
            inputs.input_ids,
            attention_mask=inputs.attention_mask,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    # Decode the response, skip the prompt
    decoded_output = tokenizer.decode(output[0], skip_special_tokens=True)
    response = decoded_output.split("[/INST]", 1)[1].strip() if "[/INST]" in decoded_output else decoded_output
    
    return response

def load_model(args):
    """
    Load the fine-tuned model
    """
    print(f"Chargement du modèle de base: {args.base_model}")
    
    # Configuration de quantification si nécessaire
    if args.use_4bit:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )
        quantization_config = bnb_config
    else:
        quantization_config = None
    
    # Charger le modèle de base
    if quantization_config:
        model = AutoModelForCausalLM.from_pretrained(
            args.base_model,
            device_map="auto",
            quantization_config=quantization_config,
            trust_remote_code=True
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            args.base_model,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True
        )
    
    # Charger l'adaptateur LoRA
    if os.path.exists(args.adapter_path):
        print(f"Chargement de l'adaptateur: {args.adapter_path}")
        model = PeftModel.from_pretrained(model, args.adapter_path)
    else:
        print(f"ATTENTION: L'adaptateur n'a pas été trouvé à {args.adapter_path}. Utilisation du modèle de base.")
    
    # Charger le tokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    
    return model, tokenizer

def create_gradio_interface(model, tokenizer, args):
    """
    Create a Gradio interface for testing the model
    """
    def predict(message, history, max_new_tokens, temperature, top_p, top_k):
        response = generate_response(
            model, 
            tokenizer, 
            message, 
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k
        )
        return response
    
    with gr.Blocks() as demo:
        gr.Markdown("# Testeur de modèle Mistral 7B Fine-tuné")
        
        with gr.Row():
            with gr.Column(scale=4):
                chatbot = gr.Chatbot(height=500)
                message = gr.Textbox(label="Votre message", placeholder="Entrez votre message ici...")
                
                with gr.Row():
                    submit = gr.Button("Envoyer")
                    clear = gr.Button("Effacer")
            
            with gr.Column(scale=1):
                max_new_tokens = gr.Slider(
                    minimum=10, maximum=2048, step=10, value=args.max_new_tokens,
                    label="Tokens max"
                )
                temperature = gr.Slider(
                    minimum=0.1, maximum=2.0, step=0.1, value=args.temperature,
                    label="Température"
                )
                top_p = gr.Slider(
                    minimum=0.1, maximum=1.0, step=0.05, value=args.top_p,
                    label="Top-p"
                )
                top_k = gr.Slider(
                    minimum=1, maximum=100, step=1, value=args.top_k,
                    label="Top-k"
                )
        
        gr.Markdown("## À propos du modèle")
        gr.Markdown(f"**Modèle de base:** {args.base_model}")
        gr.Markdown(f"**Adaptateur LoRA:** {args.adapter_path}")
        
        # Set up interactions
        submit.click(
            predict,
            inputs=[message, chatbot, max_new_tokens, temperature, top_p, top_k],
            outputs=chatbot
        ).then(
            lambda: "", 
            outputs=message
        )
        
        message.submit(
            predict,
            inputs=[message, chatbot, max_new_tokens, temperature, top_p, top_k],
            outputs=chatbot
        ).then(
            lambda: "", 
            outputs=message
        )
        
        clear.click(lambda: None, None, chatbot)
    
    demo.launch(share=True, inbrowser=True)

def test_interactive(model, tokenizer, args):
    """
    Interactive console test mode
    """
    print("Mode test interactif. Entrez 'q' pour quitter.")
    
    while True:
        prompt = input("\nVotre message: ")
        
        if prompt.lower() in ["q", "quit", "exit"]:
            break
            
        response = generate_response(
            model, 
            tokenizer, 
            prompt, 
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            top_k=args.top_k
        )
        
        print("\nRéponse:")
        print(response)

def main():
    args = parse_args()
    
    # Charger le modèle et le tokenizer
    model, tokenizer = load_model(args)
    
    # Mode test
    if args.use_gradio:
        print("Lancement de l'interface Gradio...")
        create_gradio_interface(model, tokenizer, args)
    else:
        test_interactive(model, tokenizer, args)

if __name__ == "__main__":
    main() 