require('dotenv').config();
const fs = require('fs');
const path = require('path');
const fetch = require('node-fetch');

// Configuration
const OLLAMA_API = 'http://localhost:11434';
const MODEL_NAME = 'batiment-expert';
const BASE_MODEL = 'mistral';

// Chemin vers les données d'entraînement
const trainingDataPath = path.join(__dirname, 'data', 'training', 'building_qa_training.jsonl');

// Vérifier que le fichier de données d'entraînement existe
if (!fs.existsSync(trainingDataPath)) {
  console.error(`Erreur: Le fichier de données d'entraînement n'existe pas: ${trainingDataPath}`);
  console.error('Exécutez d\'abord "npm run generate-data" pour générer les données d\'entraînement');
  process.exit(1);
}

/**
 * Fonction pour vérifier si Ollama est en cours d'exécution
 */
async function checkOllamaStatus() {
  try {
    const response = await fetch(`${OLLAMA_API}/api/tags`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return true;
  } catch (error) {
    console.error('Erreur: Impossible de se connecter à Ollama. Assurez-vous qu\'Ollama est installé et en cours d\'exécution.');
    console.error('Pour installer Ollama: https://ollama.ai/download/windows');
    return false;
  }
}

/**
 * Fonction pour créer le modèle personnalisé
 */
async function createCustomModel() {
  console.log(`Création du modèle personnalisé ${MODEL_NAME}...`);
  
  try {
    // Lire le contenu du Modelfile
    const modelfile = fs.readFileSync('Modelfile', 'utf8');
    
    // Créer le modèle via l'API Ollama
    const response = await fetch(`${OLLAMA_API}/api/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: MODEL_NAME,
        modelfile: modelfile
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Erreur lors de la création du modèle');
    }

    console.log(`✓ Modèle ${MODEL_NAME} créé avec succès`);
    return true;
  } catch (error) {
    console.error('Erreur lors de la création du modèle:', error.message);
    return false;
  }
}

/**
 * Fonction pour fine-tuner le modèle avec nos données
 */
async function fineTuneModel() {
  console.log('Démarrage du fine-tuning...');
  
  try {
    // Lire et parser les données d'entraînement
    const trainingData = fs.readFileSync(trainingDataPath, 'utf8')
      .split('\n')
      .filter(line => line.trim())
      .map(line => JSON.parse(line));
    
    console.log(`Chargement de ${trainingData.length} exemples d'entraînement`);
    
    // Pour chaque exemple d'entraînement
    for (const [index, example] of trainingData.entries()) {
      console.log(`\nTraitement de l'exemple ${index + 1}/${trainingData.length}`);
      
      try {
        const response = await fetch(`${OLLAMA_API}/api/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            model: MODEL_NAME,
            messages: [
              {
                role: 'user',
                content: example.question
              },
              {
                role: 'assistant',
                content: example.answer
              }
            ],
            stream: false
          })
        });

        if (!response.ok) {
          console.error(`Erreur pour l'exemple ${index + 1}:`, await response.text());
          continue;
        }

        const result = await response.json();
        console.log('✓ Exemple traité avec succès');
        
      } catch (error) {
        console.error(`Erreur pour l'exemple ${index + 1}:`, error.message);
      }
    }

    console.log('\nFine-tuning terminé !');
    console.log(`\nPour utiliser le modèle, exécutez: ollama run ${MODEL_NAME}`);
    
  } catch (error) {
    console.error('Erreur lors du fine-tuning:', error.message);
    process.exit(1);
  }
}

/**
 * Fonction principale
 */
async function main() {
  // Vérifier qu'Ollama est en cours d'exécution
  if (!await checkOllamaStatus()) {
    process.exit(1);
  }

  // Créer le modèle personnalisé
  if (!await createCustomModel()) {
    process.exit(1);
  }

  // Lancer le fine-tuning
  await fineTuneModel();
}

// Lancer le processus
main().catch(console.error); 