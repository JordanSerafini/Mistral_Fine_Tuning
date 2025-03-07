from transformers import AutoTokenizer, AutoModelForCausalLM

def load_finetuned_model():
    model_path = "./models/mistral-btp"
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path)
    return model, tokenizer

def generate_response(prompt):
    model, tokenizer = load_finetuned_model()
    
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_length=150)

    return tokenizer.decode(outputs[0], skip_special_tokens=True)

if __name__ == "__main__":
    print("🔍 Chargement du modèle fine-tuné...")
    prompt = input("Posez votre question : ")
    response = generate_response(prompt)
    print("💬 Réponse de l'IA :", response)
