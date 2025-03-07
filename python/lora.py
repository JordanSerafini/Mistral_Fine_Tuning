from peft import LoraConfig, get_peft_model
from transformers import TrainingArguments, Trainer
from datasets import load_dataset
from load_model import load_mistral_model  # Charger la fonction du fichier précédent

# Charger le modèle de base
model, tokenizer = load_mistral_model()

# Charger le dataset d'entraînement
dataset = load_dataset("json", data_files={"train": "./data/training/data.jsonl"})

# Configuration de LoRA
lora_config = LoraConfig(
    r=8,  # Rank de la matrice de décomposition (8 = optimal pour RAM limitée)
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

# Appliquer LoRA au modèle
model = get_peft_model(model, lora_config)

# Définir les arguments d'entraînement
training_args = TrainingArguments(
    output_dir="./models/mistral-btp",
    per_device_train_batch_size=1,  # Ajuster selon la RAM
    gradient_accumulation_steps=4,
    warmup_steps=100,
    save_steps=500,
    logging_steps=100,
    learning_rate=2e-4,
    fp16=True,  # Utiliser le format 16-bit pour économiser la RAM
    num_train_epochs=3,
    save_total_limit=2
)

# Définir l'entraîneur
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"]
)

if __name__ == "__main__":
    print("🚀 Début de l'entraînement...")
    trainer.train()
    trainer.save_model("./models/mistral-btp")
    print("✅ Entraînement terminé et modèle sauvegardé.")
