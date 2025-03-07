require('dotenv').config();
const { Client } = require('@elastic/elasticsearch');
const axios = require('axios');

// Vérifier que les variables d'environnement nécessaires sont définies
if (!process.env.ELASTICSEARCH_URL) {
  console.error('Erreur: ELASTICSEARCH_URL n\'est pas définie dans le fichier .env');
  process.exit(1);
}

if (!process.env.HUGGINGFACE_API_KEY) {
  console.error('Erreur: HUGGINGFACE_API_KEY n\'est pas définie dans le fichier .env');
  process.exit(1);
}

// Configuration
const elasticUrl = process.env.ELASTICSEARCH_URL;
const indexName = process.env.ELASTICSEARCH_INDEX || 'batiment-documents';
const modelId = process.env.MODEL_ID || 'mistralai/Mistral-7B-v0.1'; // Ou votre modèle fine-tuné
const HF_API_KEY = process.env.HUGGINGFACE_API_KEY;

// Créer un client ElasticSearch
const client = new Client({
  node: elasticUrl,
  auth: process.env.ELASTICSEARCH_USERNAME && process.env.ELASTICSEARCH_PASSWORD
    ? {
        username: process.env.ELASTICSEARCH_USERNAME,
        password: process.env.ELASTICSEARCH_PASSWORD
      }
    : undefined
});

/**
 * Fonction pour rechercher des documents pertinents dans ElasticSearch
 */
async function searchDocuments(query, maxResults = 3) {
  try {
    const { body } = await client.search({
      index: indexName,
      body: {
        query: {
          multi_match: {
            query: query,
            fields: ['title^2', 'content', 'tags^1.5'],
            fuzziness: 'AUTO'
          }
        },
        size: maxResults
      }
    });
    
    return body.hits.hits.map(hit => ({
      title: hit._source.title,
      content: hit._source.content,
      score: hit._score
    }));
    
  } catch (error) {
    console.error('Erreur lors de la recherche de documents:');
    console.error(error);
    return [];
  }
}

/**
 * Fonction pour générer une réponse avec le modèle Mistral
 */
async function generateResponse(query, context) {
  try {
    // Construire le prompt avec le contexte récupéré
    const contextText = context.map(doc => 
      `Document: ${doc.title}\n${doc.content}`
    ).join('\n\n');
    
    const prompt = `Tu es un assistant spécialisé dans le domaine du bâtiment. Utilise le contexte suivant pour répondre à la question de l'utilisateur.
    
Contexte:
${contextText}

Question: ${query}

Réponse:`;
    
    // Appeler l'API Hugging Face pour générer une réponse
    const response = await axios.post(
      `https://api-inference.huggingface.co/models/${modelId}`,
      {
        inputs: prompt,
        parameters: {
          max_new_tokens: 500,
          temperature: 0.7,
          top_p: 0.9,
          do_sample: true
        }
      },
      {
        headers: {
          'Authorization': `Bearer ${HF_API_KEY}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    return response.data[0].generated_text.split('Réponse:')[1].trim();
    
  } catch (error) {
    console.error('Erreur lors de la génération de réponse:');
    if (error.response) {
      console.error('Réponse de l\'API:', error.response.data);
    } else {
      console.error(error.message);
    }
    return "Désolé, je n'ai pas pu générer une réponse. Veuillez réessayer plus tard.";
  }
}

/**
 * Fonction principale pour le RAG
 */
async function ragQuery(userQuery) {
  console.log(`Question: ${userQuery}`);
  
  // Étape 1: Rechercher des documents pertinents
  console.log('Recherche de documents pertinents...');
  const relevantDocs = await searchDocuments(userQuery);
  
  if (relevantDocs.length === 0) {
    console.log('Aucun document pertinent trouvé.');
    return "Je n'ai pas trouvé d'informations spécifiques sur ce sujet dans ma base de connaissances sur le bâtiment. Pourriez-vous reformuler votre question ou demander sur un autre aspect du domaine du bâtiment?";
  }
  
  console.log(`${relevantDocs.length} documents pertinents trouvés.`);
  
  // Étape 2: Générer une réponse basée sur les documents récupérés
  console.log('Génération de la réponse...');
  const answer = await generateResponse(userQuery, relevantDocs);
  
  return answer;
}

// Exemple d'utilisation
async function testRAG() {
  const questions = [
    "Comment isoler un mur extérieur?",
    "Quelles sont les normes pour la ventilation d'une salle de bain?",
    "Quelle est la différence entre un mur porteur et une cloison?"
  ];
  
  for (const question of questions) {
    console.log('\n---------------------------------------------------');
    const answer = await ragQuery(question);
    console.log('\nRéponse:');
    console.log(answer);
    console.log('---------------------------------------------------\n');
  }
}

// Si le script est exécuté directement, tester le RAG
if (require.main === module) {
  testRAG().catch(error => {
    console.error('Erreur lors du test RAG:');
    console.error(error);
  });
}

// Exporter les fonctions pour utilisation dans d'autres modules
module.exports = {
  searchDocuments,
  generateResponse,
  ragQuery
}; 