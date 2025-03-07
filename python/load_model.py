from transformers import AutoModelForCausalLM, AutoTokenizer

def load_mistral_model():
    # Utiliser un modèle plus petit
    model_name = "mistralai/Mistral-7B-Instruct-v0.2"
    
    print(f"Chargement du modèle {model_name} sur CPU...")
    
    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    # Charger le modèle sur CPU sans quantification
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",  # Utiliser le type par défaut
        device_map="cpu",    # Forcer l'utilisation du CPU
        low_cpu_mem_usage=True  # Optimisation pour CPU
    )
    
    print("✅ Modèle chargé avec succès")
    return model, tokenizer

if __name__ == "__main__":
    model, tokenizer = load_mistral_model()
