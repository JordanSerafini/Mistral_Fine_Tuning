require('dotenv').config();
const fs = require('fs');
const path = require('path');
const fetch = require('node-fetch');

// Configuration
const HF_API_KEY = process.env.HUGGINGFACE_API_KEY;
const BASE_MODEL = process.env.BASE_MODEL || 'mistralai/Mistral-7B-v0.1';
const OUTPUT_MODEL = process.env.OUTPUT_MODEL || 'jordanS/analyse_agent';

// Définir les chemins des fichiers d'entraînement
const trainingFilePaths = [
  path.join(__dirname, 'data', 'training', 'analyse_agent_data.jsonl'),
  path.join(__dirname, 'data', 'training', 'analyse_agent_data-set2.jsonl')
];

/**
 * Fonction principale pour le fine-tuning avec Hugging Face
 */
async function fineTuneWithHuggingFace() {
  console.log('Démarrage du fine-tuning avec Hugging Face...');
  
  try {
    // 1. Charger et préparer les données d'entraînement
    let allTrainingData = [];
    
    for (const filePath of trainingFilePaths) {
      if (fs.existsSync(filePath)) {
        console.log(`Chargement du fichier: ${filePath}`);
        const trainingDataContent = fs.readFileSync(filePath, 'utf8');
        
        const trainingData = trainingDataContent
          .split('\n')
          .filter(line => line.trim())
          .map(line => {
            try {
              return JSON.parse(line);
            } catch (error) {
              console.error(`Erreur de parsing pour la ligne: ${line.substring(0, 50)}...`);
              return null;
            }
          })
          .filter(item => item !== null);
        
        console.log(`Chargé ${trainingData.length} exemples d'entraînement depuis ${path.basename(filePath)}`);
        allTrainingData = [...allTrainingData, ...trainingData];
      } else {
        console.warn(`Fichier non trouvé: ${filePath}`);
      }
    }
    
    console.log(`Total: ${allTrainingData.length} exemples d'entraînement chargés`);
    
    if (allTrainingData.length === 0) {
      throw new Error("Aucune donnée d'entraînement valide trouvée");
    }
    
    // 2. Convertir les données au format attendu par Hugging Face
    const formattedData = allTrainingData.map(item => {
      // Extraire les messages
      const messages = item.messages || [];
      
      // Trouver le message système, utilisateur et assistant
      const systemMessage = messages.find(msg => msg.role === 'system')?.content || '';
      const userMessage = messages.find(msg => msg.role === 'user')?.content || '';
      const assistantMessage = messages.find(msg => msg.role === 'assistant')?.content || '';
      
      return {
        instruction: userMessage,
        input: systemMessage,
        output: assistantMessage
      };
    });
    
    // 3. Écrire les données formatées dans un fichier temporaire
    const tempFilePath = path.join(__dirname, 'temp_hf_training_data.json');
    fs.writeFileSync(tempFilePath, JSON.stringify(formattedData, null, 2));
    console.log(`Fichier temporaire créé: ${tempFilePath}`);
    
    // 4. Lancer le fine-tuning avec l'API Hugging Face
    console.log(`Lancement du fine-tuning du modèle ${BASE_MODEL} vers ${OUTPUT_MODEL}...`);
    
    // Paramètres de fine-tuning
    const trainingConfig = {
      model: BASE_MODEL,
      train_file: tempFilePath,
      output_dir: OUTPUT_MODEL,
      num_train_epochs: 3,
      per_device_train_batch_size: 4,
      gradient_accumulation_steps: 4,
      learning_rate: 2e-5,
      warmup_steps: 100,
      weight_decay: 0.01,
      fp16: true,
      push_to_hub: true
    };
    
    // Appel à l'API Hugging Face pour le fine-tuning
    const response = await fetch('https://api-inference.huggingface.co/models', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${HF_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        action: 'fine-tune',
        config: trainingConfig
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(`Erreur lors du fine-tuning: ${error.error || 'Erreur inconnue'}`);
    }
    
    const result = await response.json();
    console.log('Fine-tuning lancé avec succès !');
    console.log('ID de la tâche:', result.task_id);
    console.log('Vous pouvez suivre la progression sur Hugging Face.');
    
    // 5. Supprimer le fichier temporaire
    fs.unlinkSync(tempFilePath);
    console.log('Fichier temporaire supprimé');
    
    return true;
  } catch (error) {
    console.error('Erreur lors du fine-tuning:', error.message);
    return false;
  }
}

// Exécuter la fonction principale
fineTuneWithHuggingFace().then(success => {
  if (success) {
    console.log('\nProcessus de fine-tuning avec Hugging Face terminé avec succès !');
    console.log(`\nVotre modèle sera disponible à l'adresse: https://huggingface.co/${OUTPUT_MODEL}`);
  } else {
    console.error('\nLe processus de fine-tuning a échoué.');
  }
}); 