require('dotenv').config();
const fs = require('fs');
const path = require('path');
const fetch = require('node-fetch');

// Configuration
const OLLAMA_API = 'http://localhost:11434';
const MODEL_NAME = 'mistral-analyse-agent';
const BASE_MODEL = 'mistral:latest';

// Définir les chemins des fichiers d'entraînement
const trainingFilePaths = [
  path.join(__dirname, 'data', 'training', 'analyse_agent_data.jsonl'),
  path.join(__dirname, 'data', 'training', 'analyse_agent_data-set2.jsonl')
];

// Vérifier que les fichiers d'entraînement existent
let hasTrainingFiles = false;
for (const filePath of trainingFilePaths) {
  if (fs.existsSync(filePath)) {
    hasTrainingFiles = true;
    console.log(`Fichier d'entraînement trouvé: ${filePath}`);
  } else {
    console.log(`Fichier d'entraînement non trouvé: ${filePath}`);
  }
}

/**
 * Fonction pour vérifier si Ollama est en cours d'exécution
 */
async function checkOllamaStatus() {
  try {
    const response = await fetch(`${OLLAMA_API}/api/tags`);
    return response.ok;
  } catch (error) {
    return false;
  }
}

/**
 * Fonction pour lister les modèles disponibles localement
 */
async function listLocalModels() {
  try {
    console.log('Vérification des modèles disponibles localement...');
    const response = await fetch(`${OLLAMA_API}/api/tags`);
    const data = await response.json();
    
    console.log('Modèles disponibles localement:');
    data.models.forEach(model => {
      console.log(`- ${model.name}`);
    });
    
    return data.models;
  } catch (error) {
    console.error('Erreur lors de la récupération des modèles:', error.message);
    return [];
  }
}

/**
 * Fonction pour vérifier si un modèle existe
 */
async function modelExists(modelName) {
  const models = await listLocalModels();
  return models.some(model => model.name === modelName);
}

/**
 * Fonction pour créer et fine-tuner le modèle avec nos données
 */
async function createAndFineTuneModel() {
  console.log('Démarrage du fine-tuning...');
  
  try {
    let allTrainingData = [];
    
    // Charger tous les fichiers d'entraînement
    for (const filePath of trainingFilePaths) {
      if (fs.existsSync(filePath)) {
        console.log(`Chargement du fichier: ${filePath}`);
        // Lire le contenu du fichier
        const trainingDataContent = fs.readFileSync(filePath, 'utf8');
        
        // Parser les données au format JSONL (une ligne JSON par ligne)
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
    
    // Préparer les données pour le fine-tuning
    console.log('Préparation des données pour le fine-tuning...');
    
    // Créer un fichier temporaire pour les données d'entraînement
    const tempFilePath = path.join(__dirname, 'temp_training_data.jsonl');
    
    // Écrire les données dans le fichier temporaire
    fs.writeFileSync(tempFilePath, allTrainingData.map(item => JSON.stringify(item)).join('\n'));
    
    console.log(`Fichier temporaire créé: ${tempFilePath}`);
    
    // Lire le contenu du Modelfile ou créer un modelfile par défaut
    let modelfileContent;
    const modelfilePath = path.join(__dirname, '..', 'Modelfile');
    
    if (fs.existsSync(modelfilePath)) {
      console.log('Utilisation du Modelfile existant...');
      modelfileContent = fs.readFileSync(modelfilePath, 'utf8');
    } else {
      console.log('Création d\'un Modelfile par défaut...');
      modelfileContent = `FROM ${BASE_MODEL}

SYSTEM """
Vous êtes un assistant d'analyse pour une société de BTP spécialisée dans la construction et rénovation de bâtiments.
"""

PARAMETER temperature 0.4
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER stop "Human:"
PARAMETER stop "Assistant:"
`;
    }
    
    // Lancer le fine-tuning avec l'API Ollama
    console.log(`Création et fine-tuning du modèle ${MODEL_NAME}...`);
    
    const response = await fetch(`${OLLAMA_API}/api/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: MODEL_NAME,
        modelfile: modelfileContent,
        path: tempFilePath
      })
    });
    
    // Supprimer le fichier temporaire
    fs.unlinkSync(tempFilePath);
    console.log('Fichier temporaire supprimé');
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Erreur lors du fine-tuning');
    }
    
    return true;
    
  } catch (error) {
    console.error('Erreur lors du fine-tuning:', error.message);
    return false;
  }
}

/**
 * Fonction pour télécharger le modèle de base
 */
async function pullBaseModel() {
  console.log(`Téléchargement du modèle de base ${BASE_MODEL}...`);
  
  try {
    const response = await fetch(`${OLLAMA_API}/api/pull`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: BASE_MODEL,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Erreur lors du téléchargement du modèle de base');
    }

    console.log(`✓ Modèle de base ${BASE_MODEL} téléchargé avec succès`);
    return true;
  } catch (error) {
    console.error('Erreur lors du téléchargement du modèle de base:', error.message);
    return false;
  }
}

/**
 * Fonction pour supprimer un modèle existant
 */
async function deleteModel(modelName) {
  console.log(`Tentative de suppression du modèle ${modelName}...`);
  
  try {
    const response = await fetch(`${OLLAMA_API}/api/delete`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: modelName
      })
    });
    
    if (response.ok) {
      console.log(`Modèle ${modelName} supprimé avec succès.`);
      return true;
    } else {
      const errorData = await response.json();
      console.error(`Erreur lors de la suppression du modèle: ${errorData.error || 'Erreur inconnue'}`);
      return false;
    }
  } catch (error) {
    console.error(`Erreur lors de la suppression du modèle: ${error.message}`);
    return false;
  }
}

/**
 * Fonction principale
 */
async function main() {
  try {
    // Vérifier que Ollama est en cours d'exécution
    if (!await checkOllamaStatus()) {
      console.error('Ollama n\'est pas en cours d\'exécution. Veuillez démarrer Ollama et réessayer.');
      return;
    }
    
    // Lister les modèles disponibles
    await listLocalModels();
    
    // Vérifier si le modèle existe déjà et le supprimer si c'est le cas
    if (await modelExists(MODEL_NAME)) {
      console.log(`Le modèle ${MODEL_NAME} existe déjà.`);
      console.log(`Suppression du modèle existant pour un nouveau fine-tuning...`);
      if (!await deleteModel(MODEL_NAME)) {
        console.error(`Impossible de supprimer le modèle existant. Arrêt du processus.`);
        return;
      }
    }
    
    // Vérifier si le modèle de base existe
    console.log(`Vérification de l'existence du modèle de base ${BASE_MODEL}...`);
    if (!await modelExists(BASE_MODEL)) {
      console.log(`Le modèle de base ${BASE_MODEL} n'existe pas localement.`);
      // Télécharger le modèle de base
      if (!await pullBaseModel()) {
        console.error(`Impossible de télécharger le modèle de base. Arrêt du processus.`);
        return;
      }
    } else {
      console.log(`Le modèle de base ${BASE_MODEL} existe déjà localement.`);
    }
    
    // Démarrer le fine-tuning
    console.log('Démarrage du fine-tuning...');
    
    // Vérifier que nous avons des fichiers d'entraînement
    if (!hasTrainingFiles) {
      console.error('Aucun fichier d\'entraînement trouvé. Veuillez ajouter des fichiers d\'entraînement et réessayer.');
      return;
    }
    
    // Créer et fine-tuner le modèle
    if (!await createAndFineTuneModel()) {
      console.error('Échec du fine-tuning du modèle.');
      return;
    }
    
    console.log('\nFine-tuning terminé avec succès !');
    console.log('\nPour utiliser le modèle, exécutez: ollama run ' + MODEL_NAME);
    
  } catch (error) {
    console.error('Erreur lors du processus de fine-tuning:', error.message);
  }
}

// Exécuter la fonction principale
main(); 