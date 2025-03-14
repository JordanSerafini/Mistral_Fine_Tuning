#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour déployer le modèle Mistral 7B Instruct fine-tuné sur un endpoint FastAPI.
"""

import os
import torch
import argparse
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Modèle et tokenizer globaux
MODEL = None
TOKENIZER = None

class GenerationRequest(BaseModel):
    prompt: str
    max_new_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    
class GenerationResponse(BaseModel):
    generated_text: str
    processing_time_ms: float

def parse_args():
    parser = argparse.ArgumentParser(description="Déploiement du modèle Mistral 7B Instruct fine-tuné")
    parser.add_argument("--base_model", type=str, default="mistralai/Mistral-7B-Instruct-v0.2",
                      help="Modèle de base utilisé pour le fine-tuning")
    parser.add_argument("--adapter_path", type=str, default="./output/final",
                      help="Chemin vers le modèle fine-tuné (adaptateur LoRA)")
    parser.add_argument("--use_4bit", action="store_true",
                      help="Utiliser la quantification 4-bit pour l'inférence")
    parser.add_argument("--port", type=int, default=8000,
                      help="Port sur lequel déployer l'API")
    parser.add_argument("--host", type=str, default="0.0.0.0",
                      help="Host sur lequel déployer l'API")
    return parser.parse_args()

def format_prompt(prompt):
    """
    Format the prompt in the style expected by Mistral 7B Instruct
    """
    return f"<s>[INST] {prompt} [/INST]"

def generate_response(prompt, max_new_tokens=512, temperature=0.7, top_p=0.9, top_k=50):
    """
    Generate a response from the model given a prompt
    """
    global MODEL, TOKENIZER
    
    if MODEL is None or TOKENIZER is None:
        raise ValueError("Le modèle et le tokenizer n'ont pas été chargés")
    
    formatted_prompt = format_prompt(prompt)
    
    inputs = TOKENIZER(formatted_prompt, return_tensors="pt").to(MODEL.device)
    
    # Generate response
    with torch.no_grad():
        output = MODEL.generate(
            inputs.input_ids,
            attention_mask=inputs.attention_mask,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            do_sample=True,
            pad_token_id=TOKENIZER.eos_token_id
        )
    
    # Decode the response, skip the prompt
    decoded_output = TOKENIZER.decode(output[0], skip_special_tokens=True)
    response = decoded_output.split("[/INST]", 1)[1].strip() if "[/INST]" in decoded_output else decoded_output
    
    return response

def load_model(args):
    """
    Load the fine-tuned model
    """
    global MODEL, TOKENIZER
    
    logger.info(f"Chargement du modèle de base: {args.base_model}")
    
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
        MODEL = AutoModelForCausalLM.from_pretrained(
            args.base_model,
            device_map="auto",
            quantization_config=quantization_config,
            trust_remote_code=True
        )
    else:
        MODEL = AutoModelForCausalLM.from_pretrained(
            args.base_model,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True
        )
    
    # Charger l'adaptateur LoRA
    if os.path.exists(args.adapter_path):
        logger.info(f"Chargement de l'adaptateur: {args.adapter_path}")
        MODEL = PeftModel.from_pretrained(MODEL, args.adapter_path)
    else:
        logger.warning(f"ATTENTION: L'adaptateur n'a pas été trouvé à {args.adapter_path}. Utilisation du modèle de base.")
    
    # Charger le tokenizer
    TOKENIZER = AutoTokenizer.from_pretrained(args.base_model)
    
    # Mettre le modèle en mode évaluation
    MODEL.eval()
    
    logger.info("Modèle chargé avec succès!")

def create_app():
    """
    Create the FastAPI app
    """
    app = FastAPI(
        title="API Mistral 7B Fine-tuné",
        description="API pour le modèle Mistral 7B Instruct fine-tuné",
        version="1.0.0"
    )
    
    # Configuration CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        return {"message": "Bienvenue sur l'API Mistral 7B Fine-tuné", "status": "active"}
    
    @app.post("/generate", response_model=GenerationResponse)
    async def generate(request: GenerationRequest):
        import time
        
        try:
            start_time = time.time()
            
            response = generate_response(
                request.prompt,
                max_new_tokens=request.max_new_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                top_k=request.top_k
            )
            
            processing_time = (time.time() - start_time) * 1000  # en ms
            
            return GenerationResponse(
                generated_text=response,
                processing_time_ms=processing_time
            )
        except Exception as e:
            logger.error(f"Erreur lors de la génération: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/health")
    async def health_check():
        if MODEL is None or TOKENIZER is None:
            raise HTTPException(status_code=503, detail="Le modèle n'est pas chargé")
        return {"status": "healthy"}
    
    return app

def main():
    args = parse_args()
    
    # Charger le modèle
    load_model(args)
    
    # Créer l'application FastAPI
    app = create_app()
    
    # Lancer le serveur
    logger.info(f"Démarrage du serveur sur {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main() 