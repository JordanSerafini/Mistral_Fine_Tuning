from peft import LoraConfig, get_peft_model
from transformers import TrainingArguments, Trainer
from datasets import load_dataset
from load_model import load_mistral_model

# Charger le modèle de base
model, tokenizer = load_mistral_model()

# Charger le dataset d'entraînement (avec un petit échantillon)
dataset = load_dataset("json", data_files={"train": "./data/training/data.jsonl"})
# Limiter à 50 exemples pour l'entraînement sur CPU
small_dataset = dataset["train"].select(range(min(50, len(dataset["train"]))))

# Configuration de LoRA minimale
lora_config = LoraConfig(
    r=2,  # Rang minimal
    lora_alpha=16,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

# Appliquer LoRA au modèle
model = get_peft_model(model, lora_config)

# Définir les arguments d'entraînement pour CPU
training_args = TrainingArguments(
    output_dir="./models/mistral-btp",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    max_steps=20,  # Très limité pour test
    save_steps=10,
    logging_steps=5,
    learning_rate=1e-4,
    fp16=False,  # Désactiver fp16 sur CPU
    save_total_limit=1,
    remove_unused_columns=False
)

# Définir l'entraîneur
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=small_dataset
)

if __name__ == "__main__":
    print("🚀 Début de l'entraînement...")
    trainer.train()
    trainer.save_model("./models/mistral-btp")
    print("✅ Entraînement terminé et modèle sauvegardé.")
