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
  learning_rate: 5e-5,
  per_device_train_batch_size: 4,
  gradient_accumulation_steps: 4,
  optim: 'adamw_torch',
  save_steps: 200,
  logging_steps: 100,
  evaluation_strategy: 'steps',
  eval_steps: 200,
  warmup_steps: 100,
  max_grad_norm: 0.5,
  weight_decay: 0.01,
  fp16: true,
  bf16: true,
  trust_remote_code: true,
  max_length: 32768,
  temperature: 0.6,
  top_p: 0.95,
  peft_config: {
    peft_type: 'lora',
    r: 16,
    lora_alpha: 32,
    lora_dropout: 0.05,
    bias: 'none',
    task_type: 'CAUSAL_LM',
    target_modules: ["q_proj", "k_proj", "v_proj", "o_proj"]
  }
};

/**
 * Fonction pour lancer le fine-tuning via l'API Hugging Face
 */
async function startFineTuning() {
  console.log('Démarrage du fine-tuning de DeepSeek pour le domaine du bâtiment...');
  console.log(`Modèle de base: ${BASE_MODEL}`);
  console.log(`Modèle de sortie: ${OUTPUT_MODEL}`);
  
  try {
    // Vérifier la connexion à Hugging Face
    try {
      await axios.get('https://api-inference.huggingface.co/status');
      console.log('✓ Connexion à l\'API Hugging Face établie');
    } catch (error) {
      throw new Error('Impossible de se connecter à l\'API Hugging Face. Vérifiez votre connexion Internet.');
    }

    // Vérifier la clé API
    try {
      const response = await axios.get(`https://api-inference.huggingface.co/models/${BASE_MODEL}`, {
        headers: { 'Authorization': `Bearer ${HF_API_KEY}` }
      });
      console.log('✓ Clé API valide et modèle accessible');
    } catch (error) {
      if (error.response && error.response.status === 403) {
        throw new Error('Clé API invalide ou droits insuffisants. Vérifiez votre clé sur https://huggingface.co/settings/tokens');
      } else {
        throw new Error('Modèle non accessible. Vérifiez que vous avez accepté les conditions d\'utilisation du modèle.');
      }
    }
    
    // Préparer les données pour l'API
    const trainingData = {
      model: BASE_MODEL,
      inputs: fs.readFileSync(trainingDataPath, 'utf8'),
      parameters: {
        ...trainingConfig,
        task: 'text-generation',
        do_sample: true,
        max_new_tokens: 32768,
        temperature: 0.6,
        top_p: 0.95
      }
    };
    
    // Appel à l'API Hugging Face pour le fine-tuning
    const response = await axios.post(
      `https://api-inference.huggingface.co/models/${BASE_MODEL}/train`,
      trainingData,
      {
        headers: {
          'Authorization': `Bearer ${HF_API_KEY}`,
          'Content-Type': 'application/json'
        },
        timeout: 60000 // 60 secondes de timeout
      }
    );
    
    console.log('Fine-tuning démarré avec succès!');
    console.log('ID de la tâche:', response.data.task_id);
    console.log('Statut:', response.data.status);
    console.log('Vous pouvez suivre la progression sur Hugging Face.');
    
    // Enregistrer les informations de la tâche
    fs.writeFileSync(
      path.join(__dirname, 'fine_tuning_task.json'),
      JSON.stringify(response.data, null, 2)
    );
    
  } catch (error) {
    console.error('Erreur lors du démarrage du fine-tuning:');
    if (error.response) {
      console.error('Code d\'erreur:', error.response.status);
      console.error('Message:', error.response.data);
      
      if (error.response.status === 403) {
        console.error('\nERREUR 403 - Solutions possibles:');
        console.error('1. Vérifiez que votre clé API est correcte');
        console.error('2. Assurez-vous d\'avoir les droits nécessaires sur votre compte Hugging Face');
        console.error('3. Vérifiez que vous avez accepté les conditions d\'utilisation du modèle');
        console.error('\nVous pouvez vérifier votre clé API sur: https://huggingface.co/settings/tokens');
      }
    } else {
      console.error('Erreur:', error.message);
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
      `https://api-inference.huggingface.co/models/${OUTPUT_MODEL}/tasks/${taskId}`,
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
      console.error('Code d\'erreur:', error.response.status);
      console.error('Message:', error.response.data);
    } else {
      console.error('Erreur:', error.message);
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