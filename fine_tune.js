require('dotenv').config();
const fs = require('fs');
const path = require('path');
const axios = require('axios');
const FormData = require('form-data');

// Vérifier que les variables d'environnement nécessaires sont définies
if (!process.env.HUGGINGFACE_API_KEY) {
  console.error('Erreur: HUGGINGFACE_API_KEY n\'est pas définie dans le fichier .env');
  process.exit(1);
}

const HF_API_KEY = process.env.HUGGINGFACE_API_KEY;
const BASE_MODEL = process.env.BASE_MODEL || 'mistralai/Mistral-7B-v0.1';
const OUTPUT_MODEL = process.env.OUTPUT_MODEL || 'mistral-batiment';

// Chemin vers les données d'entraînement
const trainingDataPath = path.join(__dirname, 'data', 'training', 'building_qa_training.jsonl');

// Vérifier que le fichier de données d'entraînement existe
if (!fs.existsSync(trainingDataPath)) {
  console.error(`Erreur: Le fichier de données d'entraînement n'existe pas: ${trainingDataPath}`);
  console.error('Exécutez d\'abord "npm run generate-data" pour générer les données d\'entraînement');
  process.exit(1);
}

// Configuration pour le fine-tuning
const trainingConfig = {
  model: BASE_MODEL,
  push_to_hub: true,
  hub_model_id: OUTPUT_MODEL,
  training_file: trainingDataPath,
  num_train_epochs: 3,
  learning_rate: 2e-5,
  per_device_train_batch_size: 4,
  gradient_accumulation_steps: 4,
  optim: 'adamw_torch',
  save_steps: 500,
  logging_steps: 100,
  evaluation_strategy: 'steps',
  eval_steps: 500,
  warmup_steps: 100,
  max_grad_norm: 1.0,
  weight_decay: 0.01,
  fp16: true,
  peft_config: {
    peft_type: 'lora',
    r: 16,
    lora_alpha: 32,
    lora_dropout: 0.05,
    bias: 'none',
    task_type: 'CAUSAL_LM'
  }
};

/**
 * Fonction pour lancer le fine-tuning via l'API Hugging Face
 */
async function startFineTuning() {
  console.log('Démarrage du fine-tuning de Mistral pour le domaine du bâtiment...');
  console.log(`Modèle de base: ${BASE_MODEL}`);
  console.log(`Modèle de sortie: ${OUTPUT_MODEL}`);
  
  try {
    // Préparer les données pour l'API
    const formData = new FormData();
    formData.append('training_file', fs.createReadStream(trainingDataPath));
    formData.append('config', JSON.stringify(trainingConfig));
    
    // Appel à l'API Hugging Face pour le fine-tuning
    const response = await axios.post(
      'https://api-inference.huggingface.co/models/fine-tune',
      formData,
      {
        headers: {
          'Authorization': `Bearer ${HF_API_KEY}`,
          ...formData.getHeaders()
        }
      }
    );
    
    console.log('Fine-tuning démarré avec succès!');
    console.log('ID de la tâche:', response.data.task_id);
    console.log('Statut:', response.data.status);
    console.log('Vous pouvez suivre la progression sur Hugging Face.');
    
    // Enregistrer les informations de la tâche pour référence future
    fs.writeFileSync(
      path.join(__dirname, 'fine_tuning_task.json'),
      JSON.stringify(response.data, null, 2)
    );
    
  } catch (error) {
    console.error('Erreur lors du démarrage du fine-tuning:');
    if (error.response) {
      console.error('Réponse de l\'API:', error.response.data);
    } else {
      console.error(error.message);
    }
    process.exit(1);
  }
}

/**
 * Fonction pour vérifier le statut d'une tâche de fine-tuning
 */
async function checkFineTuningStatus(taskId) {
  try {
    const response = await axios.get(
      `https://api-inference.huggingface.co/models/fine-tune/${taskId}`,
      {
        headers: {
          'Authorization': `Bearer ${HF_API_KEY}`
        }
      }
    );
    
    console.log('Statut de la tâche:', response.data.status);
    console.log('Détails:', response.data);
    
  } catch (error) {
    console.error('Erreur lors de la vérification du statut:');
    if (error.response) {
      console.error('Réponse de l\'API:', error.response.data);
    } else {
      console.error(error.message);
    }
  }
}

// Vérifier si un ID de tâche a été fourni en argument
const taskId = process.argv[2];
if (taskId) {
  checkFineTuningStatus(taskId);
} else {
  startFineTuning();
}

// Note: Ce script est une démonstration. L'API Hugging Face pour le fine-tuning
// peut nécessiter des ajustements selon les dernières spécifications. 