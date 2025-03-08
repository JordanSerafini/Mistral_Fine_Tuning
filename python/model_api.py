#!/usr/bin/env python3
"""
API FastAPI pour exposer le modèle fine-tuné
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel, PeftConfig
import os
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Modèle Fine-tuné", description="API pour le modèle Mistral fine-tuné")

# Configuration
MODEL_PATH = os.getenv("MODEL_PATH", "jordanS/analyse_agent")
BASE_MODEL = os.getenv("BASE_MODEL", "mistralai/Mistral-7B-v0.1")

# Variables globales pour le modèle et le tokenizer
model = None
tokenizer = None

class QueryRequest(BaseModel):
    prompt: str
    system_prompt: str = "Tu es un assistant IA expert en analyse de documents pour une entreprise de construction."
    max_length: int = 1024
    temperature: float = 0.7

@app.on_event("startup")
async def startup_event():
    global model, tokenizer
    logger.info(f"Chargement du modèle depuis {MODEL_PATH}...")
    
    try:
        # Vérifier si le modèle est un modèle PEFT (LoRA)
        config = PeftConfig.from_pretrained(MODEL_PATH)
        is_peft_model = True
        base_model_path = BASE_MODEL or config.base_model_name_or_path
        logger.info(f"Modèle PEFT détecté, chargement du modèle de base: {base_model_path}")
        
        # Configurer la quantification 4-bit
        from transformers import BitsAndBytesConfig
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16
        )
        
        # Charger le tokenizer
        tokenizer = AutoTokenizer.from_pretrained(base_model_path)
        
        # Charger le modèle de base
        model_base = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            quantization_config=quantization_config,
            device_map="auto",
            torch_dtype=torch.float16
        )
        
        # Charger les adaptateurs LoRA
        model = PeftModel.from_pretrained(model_base, MODEL_PATH)
        logger.info("Modèle chargé avec succès!")
        
    except Exception as e:
        logger.error(f"Erreur lors du chargement du modèle: {e}")
        raise e

@app.get("/")
async def root():
    return {"message": "API du modèle fine-tuné", "status": "active"}

@app.get("/status")
async def status():
    return {"model_loaded": model is not None, "model_path": MODEL_PATH}

@app.post("/generate")
async def generate(request: QueryRequest):
    global model, tokenizer
    
    if model is None or tokenizer is None:
        raise HTTPException(status_code=500, detail="Le modèle n'est pas chargé")
    
    try:
        logger.info(f"Génération pour prompt: {request.prompt[:50]}...")
        
        # Formater le prompt avec le format Mistral
        formatted_prompt = f"<s>[INST] {request.system_prompt}\n\n{request.prompt} [/INST]"
        
        # Tokeniser le prompt
        inputs = tokenizer(formatted_prompt, return_tensors="pt").to(model.device)
        
        # Générer la réponse
        with torch.no_grad():
            outputs = model.generate(
                inputs.input_ids,
                max_length=request.max_length,
                temperature=request.temperature,
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
        
        logger.info(f"Réponse générée: {response[:50]}...")
        return {"response": response}
    
    except Exception as e:
        logger.error(f"Erreur lors de la génération: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("model_api:app", host="0.0.0.0", port=8000, reload=False) 