from transformers import AutoModelForCausalLM, AutoTokenizer

def load_mistral_model():
    model_name = "mistralai/Mistral-7B-v0.1"

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Charger le modèle avec optimisation mémoire
    model = AutoModelForCausalLM.from_pretrained(
        model_name, 
        load_in_8bit=True, 
        device_map="auto"
    )

    print("✅ Modèle chargé avec succès")
    return model, tokenizer

if __name__ == "__main__":
    model, tokenizer = load_mistral_model()
