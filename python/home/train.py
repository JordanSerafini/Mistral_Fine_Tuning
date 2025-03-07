from lora import trainer

if __name__ == "__main__":
    print("🚀 Lancement de l'entraînement LoRA sur Mistral...")
    trainer.train()
    trainer.save_model("./models/mistral-btp")
    print("✅ Modèle sauvegardé avec succès !")
