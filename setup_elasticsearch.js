require('dotenv').config();
const { Client } = require('@elastic/elasticsearch');
const fs = require('fs');
const path = require('path');

// Vérifier que les variables d'environnement nécessaires sont définies
if (!process.env.ELASTICSEARCH_URL) {
  console.error('Erreur: ELASTICSEARCH_URL n\'est pas définie dans le fichier .env');
  console.error('Exemple: ELASTICSEARCH_URL=http://localhost:9200');
  process.exit(1);
}

// Configuration ElasticSearch
const elasticUrl = process.env.ELASTICSEARCH_URL;
const indexName = process.env.ELASTICSEARCH_INDEX || 'batiment-documents';

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

// Données d'exemple pour le domaine du bâtiment
const buildingDocuments = [
  {
    title: "Normes d'isolation thermique RT2020",
    content: "La réglementation thermique RT2020 (ou RE2020) exige une résistance thermique minimale de R=4.5 m²K/W pour les murs, R=8 m²K/W pour les toitures et R=3 m²K/W pour les planchers bas. Ces normes visent à réduire la consommation énergétique et à améliorer le confort thermique des occupants.",
    category: "normes",
    tags: ["isolation", "thermique", "RT2020", "RE2020"]
  },
  {
    title: "Calcul de la surface habitable",
    content: "La surface habitable d'un logement se calcule en additionnant les surfaces de plancher de chaque pièce, mesurées à partir de l'intérieur des murs. On exclut les surfaces dont la hauteur sous plafond est inférieure à 1,80m, les escaliers, les combles non aménagés, les caves, les garages, ainsi que les balcons, loggias et terrasses. Cette définition est précisée dans l'article R111-2 du Code de la Construction et de l'Habitation.",
    category: "réglementation",
    tags: ["surface", "habitable", "calcul", "logement"]
  },
  {
    title: "Types de fondations dans la construction",
    content: "Les principaux types de fondations sont: 1) Les fondations superficielles (semelles filantes, semelles isolées, radier) utilisées sur des sols stables; 2) Les fondations profondes (pieux, micropieux, puits) nécessaires pour des sols instables ou des charges importantes; 3) Les fondations semi-profondes (puits courts, semelles ancrées) qui sont intermédiaires. Le choix dépend de la nature du sol, des charges du bâtiment, et des contraintes environnementales.",
    category: "technique",
    tags: ["fondations", "construction", "structure"]
  },
  {
    title: "Différence entre mur porteur et cloison",
    content: "Un mur porteur est un élément structurel qui supporte le poids des planchers et de la toiture, assurant la stabilité du bâtiment. Il est généralement plus épais (15-20cm minimum) et construit en matériaux résistants (béton, pierre, brique). Une cloison est un mur non porteur qui sert uniquement à diviser l'espace intérieur. Elle est plus légère (5-10cm d'épaisseur) et peut être déplacée sans compromettre la structure du bâtiment.",
    category: "technique",
    tags: ["mur", "porteur", "cloison", "structure"]
  },
  {
    title: "Systèmes de ventilation pour logements",
    content: "Le choix du système de ventilation dépend de plusieurs facteurs: 1) La VMC simple flux est économique mais moins efficace énergétiquement; 2) La VMC double flux offre une meilleure efficacité énergétique grâce à la récupération de chaleur mais est plus coûteuse; 3) La VMC hygroréglable s'adapte au taux d'humidité; 4) La ventilation naturelle convient aux bâtiments anciens. Ce choix doit prendre en compte le climat, l'étanchéité du bâtiment, le budget et les besoins en qualité d'air intérieur.",
    category: "équipement",
    tags: ["ventilation", "VMC", "air", "logement"]
  },
  {
    title: "Étapes d'une rénovation complète d'appartement",
    content: "Une rénovation complète d'appartement suit généralement ces étapes: 1) Diagnostic et plans (structure, électricité, plomberie); 2) Démarches administratives (autorisations, permis); 3) Démolition et curage; 4) Travaux structurels si nécessaire; 5) Réseaux (électricité, plomberie, ventilation); 6) Isolation et cloisons; 7) Menuiseries; 8) Revêtements (sols, murs, plafonds); 9) Installation sanitaires et cuisine; 10) Finitions et décoration; 11) Nettoyage final. La planification et la coordination des différents corps de métier sont essentielles pour optimiser les délais et le budget.",
    category: "rénovation",
    tags: ["rénovation", "appartement", "travaux", "planification"]
  },
  {
    title: "Réduction des ponts thermiques",
    content: "Pour réduire les ponts thermiques: 1) Utiliser l'isolation thermique par l'extérieur (ITE); 2) Assurer la continuité de l'isolation aux jonctions (murs/planchers, murs/toiture); 3) Installer des rupteurs de ponts thermiques aux liaisons façade/plancher; 4) Utiliser des menuiseries à rupture de pont thermique; 5) Isoler les tableaux de fenêtres et les coffres de volets roulants; 6) Éviter de traverser l'isolation avec des éléments conducteurs. Une conception soignée et une mise en œuvre rigoureuse sont essentielles pour garantir la performance thermique globale du bâtiment.",
    category: "isolation",
    tags: ["ponts thermiques", "isolation", "performance", "thermique"]
  },
  {
    title: "Matériaux pour construction écologique",
    content: "Pour une construction écologique, privilégiez: 1) Le bois issu de forêts gérées durablement (structure, ossature, charpente); 2) Les isolants biosourcés (fibre de bois, laine de chanvre, ouate de cellulose); 3) La terre crue (pisé, adobe, BTC) ou la paille pour les murs; 4) Les enduits à la chaux ou à l'argile; 5) Les peintures naturelles sans COV; 6) Le linoléum ou les parquets labellisés pour les sols. Ces matériaux ont un faible impact environnemental, stockent du carbone, et contribuent à créer un environnement intérieur sain avec une bonne régulation hygrothermique.",
    category: "matériaux",
    tags: ["écologique", "biosourcé", "durable", "matériaux"]
  },
  {
    title: "Dimensionnement d'un système de chauffage",
    content: "Pour dimensionner un système de chauffage: 1) Calculer les déperditions thermiques du bâtiment (selon isolation, surfaces vitrées, orientation, etc.); 2) Déterminer les besoins en puissance (généralement 80-100W/m² pour une maison bien isolée, jusqu'à 150W/m² pour une maison mal isolée); 3) Prendre en compte les apports gratuits (soleil, équipements); 4) Considérer le climat local; 5) Choisir le système adapté (pompe à chaleur, chaudière, etc.) avec une puissance légèrement supérieure aux besoins calculés. Un surdimensionnement excessif entraîne des cycles courts et une usure prématurée, tandis qu'un sous-dimensionnement ne permettra pas d'atteindre le confort souhaité.",
    category: "équipement",
    tags: ["chauffage", "dimensionnement", "puissance", "énergie"]
  },
  {
    title: "Accessibilité PMR dans les ERP",
    content: "Les Établissements Recevant du Public (ERP) doivent respecter ces règles d'accessibilité PMR: 1) Cheminements extérieurs avec largeur minimale de 1,40m; 2) Entrée principale accessible avec porte de 0,90m minimum; 3) Circulations intérieures horizontales de 1,40m minimum; 4) Ascenseur obligatoire pour les ERP de catégories 1 à 4 si étages; 5) Sanitaires adaptés avec espace de manœuvre de 1,50m; 6) Places de stationnement réservées (2% du total); 7) Signalétique adaptée; 8) Éclairage suffisant. Ces normes sont définies par l'arrêté du 20 avril 2017 et visent à garantir l'accès à tous, indépendamment du handicap.",
    category: "réglementation",
    tags: ["PMR", "accessibilité", "ERP", "handicap"]
  }
];

/**
 * Fonction pour créer l'index ElasticSearch avec le mapping approprié
 */
async function createIndex() {
  try {
    // Vérifier si l'index existe déjà
    const indexExists = await client.indices.exists({ index: indexName });
    
    if (indexExists) {
      console.log(`L'index "${indexName}" existe déjà. Suppression...`);
      await client.indices.delete({ index: indexName });
    }
    
    console.log(`Création de l'index "${indexName}"...`);
    
    // Créer l'index avec le mapping approprié pour la recherche sémantique
    await client.indices.create({
      index: indexName,
      body: {
        settings: {
          analysis: {
            analyzer: {
              french_analyzer: {
                type: 'custom',
                tokenizer: 'standard',
                filter: ['lowercase', 'french_stemmer', 'french_stop']
              }
            },
            filter: {
              french_stemmer: {
                type: 'stemmer',
                language: 'french'
              },
              french_stop: {
                type: 'stop',
                stopwords: '_french_'
              }
            }
          }
        },
        mappings: {
          properties: {
            title: { 
              type: 'text',
              analyzer: 'french_analyzer'
            },
            content: { 
              type: 'text',
              analyzer: 'french_analyzer'
            },
            category: { 
              type: 'keyword'
            },
            tags: { 
              type: 'keyword'
            },
            vector_embedding: {
              type: 'dense_vector',
              dims: 384  // Dimension pour les embeddings de sentence-transformers
            }
          }
        }
      }
    });
    
    console.log(`Index "${indexName}" créé avec succès!`);
    return true;
    
  } catch (error) {
    console.error('Erreur lors de la création de l\'index:');
    console.error(error);
    return false;
  }
}

/**
 * Fonction pour indexer les documents dans ElasticSearch
 */
async function indexDocuments() {
  try {
    console.log(`Indexation de ${buildingDocuments.length} documents...`);
    
    // Utiliser l'opération bulk pour indexer plusieurs documents à la fois
    const body = buildingDocuments.flatMap(doc => [
      { index: { _index: indexName } },
      doc
    ]);
    
    const { errors, items } = await client.bulk({ refresh: true, body });
    
    if (errors) {
      console.error('Erreurs lors de l\'indexation:');
      items.forEach((item, i) => {
        if (item.index && item.index.error) {
          console.error(`- Document ${i}: ${item.index.error.reason}`);
        }
      });
    } else {
      console.log(`${buildingDocuments.length} documents indexés avec succès!`);
    }
    
    return !errors;
    
  } catch (error) {
    console.error('Erreur lors de l\'indexation des documents:');
    console.error(error);
    return false;
  }
}

/**
 * Fonction pour tester la recherche dans ElasticSearch
 */
async function testSearch(query) {
  try {
    console.log(`Test de recherche pour: "${query}"`);
    
    const { body } = await client.search({
      index: indexName,
      body: {
        query: {
          multi_match: {
            query: query,
            fields: ['title^2', 'content', 'tags^1.5'],
            fuzziness: 'AUTO'
          }
        }
      }
    });
    
    console.log(`Résultats (${body.hits.total.value}):`);
    body.hits.hits.forEach((hit, i) => {
      console.log(`${i+1}. ${hit._source.title} (score: ${hit._score})`);
      console.log(`   ${hit._source.content.substring(0, 150)}...`);
      console.log(`   Tags: ${hit._source.tags.join(', ')}`);
      console.log('');
    });
    
    return true;
    
  } catch (error) {
    console.error('Erreur lors de la recherche:');
    console.error(error);
    return false;
  }
}

/**
 * Fonction principale
 */
async function main() {
  console.log('Configuration d\'ElasticSearch pour le RAG dans le domaine du bâtiment...');
  console.log(`URL ElasticSearch: ${elasticUrl}`);
  console.log(`Nom de l'index: ${indexName}`);
  
  try {
    // Vérifier la connexion à ElasticSearch
    const info = await client.info();
    console.log(`Connecté à ElasticSearch v${info.body.version.number}`);
    
    // Créer l'index
    const indexCreated = await createIndex();
    if (!indexCreated) {
      process.exit(1);
    }
    
    // Indexer les documents
    const documentsIndexed = await indexDocuments();
    if (!documentsIndexed) {
      process.exit(1);
    }
    
    // Tester la recherche
    console.log('\nTests de recherche:');
    await testSearch('isolation thermique');
    await testSearch('ventilation maison');
    await testSearch('rénovation appartement');
    
    console.log('\nConfiguration d\'ElasticSearch terminée avec succès!');
    console.log('Vous pouvez maintenant utiliser ElasticSearch pour le RAG dans votre chatbot.');
    
  } catch (error) {
    console.error('Erreur lors de la configuration d\'ElasticSearch:');
    console.error(error);
    process.exit(1);
  }
}

// Exécuter la fonction principale
main(); 