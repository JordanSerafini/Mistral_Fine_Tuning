const fs = require('fs');
const path = require('path');

// Exemples de questions-réponses dans le domaine du bâtiment
const buildingQA = [
  {
    question: "Quelles sont les normes d'isolation thermique pour un bâtiment résidentiel neuf?",
    answer: "Pour les bâtiments résidentiels neufs, la réglementation thermique RT2020 (ou RE2020) exige une résistance thermique minimale de R=4.5 m²K/W pour les murs, R=8 m²K/W pour les toitures et R=3 m²K/W pour les planchers bas. Ces normes visent à réduire la consommation énergétique et à améliorer le confort thermique des occupants."
  },
  {
    question: "Comment calculer la surface habitable d'un logement?",
    answer: "La surface habitable d'un logement se calcule en additionnant les surfaces de plancher de chaque pièce, mesurées à partir de l'intérieur des murs. On exclut les surfaces dont la hauteur sous plafond est inférieure à 1,80m, les escaliers, les combles non aménagés, les caves, les garages, ainsi que les balcons, loggias et terrasses. Cette définition est précisée dans l'article R111-2 du Code de la Construction et de l'Habitation."
  },
  {
    question: "Quels sont les différents types de fondations utilisés dans la construction?",
    answer: "Les principaux types de fondations sont: 1) Les fondations superficielles (semelles filantes, semelles isolées, radier) utilisées sur des sols stables; 2) Les fondations profondes (pieux, micropieux, puits) nécessaires pour des sols instables ou des charges importantes; 3) Les fondations semi-profondes (puits courts, semelles ancrées) qui sont intermédiaires. Le choix dépend de la nature du sol, des charges du bâtiment, et des contraintes environnementales."
  },
  {
    question: "Quelle est la différence entre un mur porteur et une cloison?",
    answer: "Un mur porteur est un élément structurel qui supporte le poids des planchers et de la toiture, assurant la stabilité du bâtiment. Il est généralement plus épais (15-20cm minimum) et construit en matériaux résistants (béton, pierre, brique). Une cloison est un mur non porteur qui sert uniquement à diviser l'espace intérieur. Elle est plus légère (5-10cm d'épaisseur) et peut être déplacée sans compromettre la structure du bâtiment."
  },
  {
    question: "Comment choisir le type de ventilation adapté à un logement?",
    answer: "Le choix du système de ventilation dépend de plusieurs facteurs: 1) La VMC simple flux est économique mais moins efficace énergétiquement; 2) La VMC double flux offre une meilleure efficacité énergétique grâce à la récupération de chaleur mais est plus coûteuse; 3) La VMC hygroréglable s'adapte au taux d'humidité; 4) La ventilation naturelle convient aux bâtiments anciens. Ce choix doit prendre en compte le climat, l'étanchéité du bâtiment, le budget et les besoins en qualité d'air intérieur."
  },
  {
    question: "Quelles sont les étapes d'une rénovation complète d'un appartement?",
    answer: "Une rénovation complète d'appartement suit généralement ces étapes: 1) Diagnostic et plans (structure, électricité, plomberie); 2) Démarches administratives (autorisations, permis); 3) Démolition et curage; 4) Travaux structurels si nécessaire; 5) Réseaux (électricité, plomberie, ventilation); 6) Isolation et cloisons; 7) Menuiseries; 8) Revêtements (sols, murs, plafonds); 9) Installation sanitaires et cuisine; 10) Finitions et décoration; 11) Nettoyage final. La planification et la coordination des différents corps de métier sont essentielles pour optimiser les délais et le budget."
  },
  {
    question: "Comment réduire les ponts thermiques dans une construction?",
    answer: "Pour réduire les ponts thermiques: 1) Utiliser l'isolation thermique par l'extérieur (ITE); 2) Assurer la continuité de l'isolation aux jonctions (murs/planchers, murs/toiture); 3) Installer des rupteurs de ponts thermiques aux liaisons façade/plancher; 4) Utiliser des menuiseries à rupture de pont thermique; 5) Isoler les tableaux de fenêtres et les coffres de volets roulants; 6) Éviter de traverser l'isolation avec des éléments conducteurs. Une conception soignée et une mise en œuvre rigoureuse sont essentielles pour garantir la performance thermique globale du bâtiment."
  },
  {
    question: "Quels matériaux utiliser pour une construction écologique?",
    answer: "Pour une construction écologique, privilégiez: 1) Le bois issu de forêts gérées durablement (structure, ossature, charpente); 2) Les isolants biosourcés (fibre de bois, laine de chanvre, ouate de cellulose); 3) La terre crue (pisé, adobe, BTC) ou la paille pour les murs; 4) Les enduits à la chaux ou à l'argile; 5) Les peintures naturelles sans COV; 6) Le linoléum ou les parquets labellisés pour les sols. Ces matériaux ont un faible impact environnemental, stockent du carbone, et contribuent à créer un environnement intérieur sain avec une bonne régulation hygrothermique."
  },
  {
    question: "Comment dimensionner un système de chauffage pour une maison?",
    answer: "Pour dimensionner un système de chauffage: 1) Calculer les déperditions thermiques du bâtiment (selon isolation, surfaces vitrées, orientation, etc.); 2) Déterminer les besoins en puissance (généralement 80-100W/m² pour une maison bien isolée, jusqu'à 150W/m² pour une maison mal isolée); 3) Prendre en compte les apports gratuits (soleil, équipements); 4) Considérer le climat local; 5) Choisir le système adapté (pompe à chaleur, chaudière, etc.) avec une puissance légèrement supérieure aux besoins calculés. Un surdimensionnement excessif entraîne des cycles courts et une usure prématurée, tandis qu'un sous-dimensionnement ne permettra pas d'atteindre le confort souhaité."
  },
  {
    question: "Quelles sont les obligations en matière d'accessibilité PMR dans les ERP?",
    answer: "Les Établissements Recevant du Public (ERP) doivent respecter ces règles d'accessibilité PMR: 1) Cheminements extérieurs avec largeur minimale de 1,40m; 2) Entrée principale accessible avec porte de 0,90m minimum; 3) Circulations intérieures horizontales de 1,40m minimum; 4) Ascenseur obligatoire pour les ERP de catégories 1 à 4 si étages; 5) Sanitaires adaptés avec espace de manœuvre de 1,50m; 6) Places de stationnement réservées (2% du total); 7) Signalétique adaptée; 8) Éclairage suffisant. Ces normes sont définies par l'arrêté du 20 avril 2017 et visent à garantir l'accès à tous, indépendamment du handicap."
  }
];

// Exemples de requêtes API spécifiques au secteur du bâtiment
const apiQA = [
  {
    question: "Comment récupérer la liste des devis en attente via l'API?",
    answer: "Effectuez une requête GET sur `/api/devis?statut=en-attente`. Cela retournera la liste complète des devis ayant le statut 'en-attente'."
  },
  {
    question: "Quelle requête utiliser pour créer un nouveau chantier via l'API?",
    answer: "Utilisez une requête POST sur `/api/chantiers` avec dans le corps JSON les informations nécessaires telles que le nom, l'adresse, la date de début, et le responsable du chantier."
  },
  {
    question: "Comment modifier le statut d'un chantier à 'terminé' par API?",
    answer: "Envoyez une requête PATCH sur `/api/chantiers/{id}` avec le corps JSON `{\"statut\": \"terminé\"}` où `{id}` est l'identifiant du chantier concerné."
  },
  {
    question: "Comment récupérer les informations d'un chantier spécifique via l'API?",
    answer: "Effectuez une requête GET sur `/api/chantiers/{id}` où `{id}` est l'identifiant du chantier concerné."
  },
  {
    question: "Quelle est la structure JSON pour un nouveau devis?",
    answer: "Voici un exemple de JSON pour un nouveau devis: `{\"client\": \"John Doe\", \"adresse\": \"123 Rue de la Paix\", \"date\": \"2024-01-01\", \"montant\": 15000, \"statut\": \"en-attente\"}`"
  },
  {
    question: "Quelle est la structure JSON pour un nouveau chantier?",
    answer: "Voici un exemple de JSON pour un nouveau chantier: `{\"nom\": \"Chantier de la Paix\", \"adresse\": \"123 Rue de la Paix\", \"date_debut\": \"2024-01-01\", \"responsable\": \"John Doe\"}`"
  },
  {
    question: "Comment récupérer la liste des devis en attente via l'API?",
    answer: "Utilisez une requête GET sur `/api/devis?statut=en_attente` pour obtenir tous les devis ayant le statut 'en attente'."
  },
  {
    question: "Comment créer un nouveau devis via l'API?",
    answer: "Effectuez une requête POST sur `/api/devis` avec un corps JSON contenant les champs obligatoires tels que `project_id`, `created_date`, `total`, et `status`."
  },
  {
    question: "Quelle requête utiliser pour récupérer tous les projets actifs via l'API?",
    answer: "Envoyez une requête GET sur `/api/projects?status=en_cours` pour obtenir les projets actuellement actifs."
  },
  {
    question: "Comment modifier le statut d'un projet via l'API?",
    answer: "Envoyez une requête PATCH sur `/api/projects/{id}` avec le corps JSON `{\"status\": \"termine\"}`, où `{id}` est l'identifiant du projet."
  },
  {
    question: "Quelle est la structure JSON recommandée pour créer un nouveau client via l'API?",
    answer: "Voici un exemple de JSON pour un nouveau client: `{\"firstname\": \"Jean\", \"lastname\": \"Dupont\", \"email\": \"jean.dupont@example.com\", \"phone\": \"0612345678\", \"city\": \"Paris\"}`."
  }
];

// Questions-réponses basées sur le schéma de base de données
const databaseQA = [
  {
    question: "Quelles sont les différentes tables disponibles dans la base de données du système de gestion de bâtiment?",
    answer: "La base de données comprend plusieurs tables principales: users (utilisateurs), staff (personnel), clients, projects (projets), materials (matériaux), suppliers (fournisseurs), products (produits), equipment (équipements), quotations (devis), invoices (factures), stages (étapes de projet), calendar_events (événements de calendrier), payments (paiements), expenses (dépenses), et timesheet_entries (feuilles de temps). Ces tables sont reliées entre elles pour former un système complet de gestion de projets de construction."
  },
  {
    question: "Quels sont les statuts possibles pour un projet?",
    answer: "Un projet peut avoir l'un des statuts suivants: 'prospect' (nouveau prospect), 'en_cours' (projet actif en cours de réalisation), 'termine' (projet achevé), 'en_pause' (projet temporairement suspendu), ou 'annule' (projet annulé). Ces statuts sont définis comme un type ENUM 'project_status' dans la base de données."
  },
  {
    question: "Comment sont structurés les devis dans la base de données?",
    answer: "Les devis (quotations) sont structurés avec une table principale 'quotations' qui contient les informations générales comme le projet associé, la date de création, le montant total, le statut (en_attente, accepté, refusé), la date de validité et les conditions de paiement. Les produits inclus dans le devis sont stockés dans une table séparée 'quotation_products' qui détaille chaque élément avec son nom, sa description, sa quantité, son prix unitaire et sa catégorie (matériaux, main_doeuvre, transport, autres)."
  },
  {
    question: "Comment sont gérés les équipements dans le système?",
    answer: "Les équipements sont gérés via plusieurs tables: 'equipment' stocke les informations de base sur chaque équipement (nom, référence, catégorie, fournisseur, date d'achat, prix, statut, emplacement). 'equipment_reservations' permet de réserver des équipements pour des projets spécifiques. 'maintenance_records' suit l'historique de maintenance de chaque équipement. 'equipment_categories' permet de classer les équipements par type. Ce système permet de suivre la disponibilité, l'utilisation et l'entretien de tous les équipements de l'entreprise."
  },
  {
    question: "Comment fonctionne le système de facturation?",
    answer: "Le système de facturation utilise plusieurs tables interconnectées: 'invoices' contient les informations générales de la facture (projet associé, référence, dates d'émission et d'échéance, montants HT et TTC, statut). 'invoice_items' détaille chaque élément facturé avec sa description, quantité et prix. 'payments' enregistre tous les paiements reçus pour chaque facture. Les statuts possibles pour une facture incluent: brouillon, envoyée, payée_partiellement, payée, en_retard, et annulée."
  },
  {
    question: "Comment sont gérés les fournisseurs et les produits?",
    answer: "Les fournisseurs sont enregistrés dans la table 'suppliers' avec leurs coordonnées et conditions de paiement. Les produits qu'ils fournissent sont stockés dans la table 'products', liée aux fournisseurs et aux catégories de produits. Les commandes passées aux fournisseurs sont gérées via 'supplier_orders' et 'order_items'. Ce système permet de suivre l'inventaire, les prix et les délais de livraison pour tous les matériaux et produits utilisés dans les projets."
  },
  {
    question: "Comment fonctionne le système de planification des projets?",
    answer: "La planification des projets repose sur plusieurs tables: 'projects' contient les informations générales du projet. 'stages' définit les différentes étapes du projet avec leur durée et ordre. 'project_staff' assigne le personnel aux projets. 'calendar_events' gère tous les rendez-vous et événements liés aux projets. 'timesheet_entries' enregistre le temps passé par chaque membre du personnel sur les projets. Ce système permet de planifier, suivre et ajuster l'avancement de chaque projet."
  },
  {
    question: "Comment sont calculés les budgets des projets?",
    answer: "Les budgets des projets sont gérés via la table 'project_budgets' qui définit le budget total et sa répartition entre matériaux, main d'œuvre, équipements, sous-traitants et autres dépenses. Les dépenses réelles sont suivies dans la table 'expenses'. Les coûts de main d'œuvre sont calculés à partir des 'timesheet_entries'. Les coûts des matériaux proviennent de 'project_materials'. Ce système permet de comparer le budget prévisionnel aux dépenses réelles et d'identifier les écarts."
  },
  {
    question: "Comment fonctionne le système de suivi des activités?",
    answer: "Le suivi des activités utilise la table 'activity_logs' qui enregistre toutes les actions effectuées dans le système (création, modification, consultation, suppression, etc.). Cette table est partitionnée par mois pour optimiser les performances. Chaque entrée contient l'utilisateur, le type d'action, l'entité concernée, les détails de l'action et l'adresse IP. Ce système permet de suivre qui a fait quoi et quand, assurant ainsi la traçabilité et la sécurité."
  },
  {
    question: "Comment sont gérés les clients et leurs projets?",
    answer: "Les clients sont enregistrés dans la table 'clients' avec leurs coordonnées complètes. Chaque client peut avoir plusieurs projets dans la table 'projects'. Les projets sont liés aux devis ('quotations'), factures ('invoices') et témoignages ('testimonials'). Ce système permet de suivre l'historique complet de chaque client, ses projets en cours et passés, ainsi que son niveau de satisfaction."
  },
  {
    question: "Comment fonctionne le système de gestion des connaissances pour le chatbot?",
    answer: "Le système de gestion des connaissances pour le chatbot utilise plusieurs tables: 'knowledge_base' stocke des paires question-réponse avec des catégories et tags. 'technical_glossary' contient des définitions de termes techniques. 'standard_services' décrit les services standards avec leurs prix et durées. 'chat_history' enregistre toutes les conversations. 'user_intents' suit les intentions fréquentes des utilisateurs. Ces tables sont optimisées pour la recherche full-text et permettent au chatbot de fournir des réponses précises et contextuelles."
  },
  {
    question: "Quels types d'événements peuvent être enregistrés dans le calendrier?",
    answer: "Le calendrier peut enregistrer plusieurs types d'événements définis par le type ENUM 'event_type': appel_telephonique, reunion_chantier, visite_technique, rendez_vous_client, reunion_interne, formation, livraison_materiaux, intervention_urgente, maintenance, absence, et autre. Chaque événement est lié à un projet, un membre du personnel et/ou un client, avec une date et heure de début et de fin, une description et un lieu."
  },
  {
    question: "Comment sont gérées les factures en retard?",
    answer: "Les factures en retard sont identifiées par leur statut 'en_retard' dans la table 'invoices'. Une vue matérialisée 'overdue_invoices_report' fournit un rapport actualisé des factures en retard. Le système peut automatiquement changer le statut d'une facture à 'en_retard' lorsque la date d'échéance est dépassée sans paiement complet. Des notifications peuvent être envoyées aux clients et à l'équipe de gestion pour suivre ces retards."
  },
  {
    question: "Comment sont calculés les coûts de main d'œuvre pour un projet?",
    answer: "Les coûts de main d'œuvre sont calculés à partir de la table 'timesheet_entries' qui enregistre les heures travaillées par chaque membre du personnel sur un projet, avec leur taux horaire. Le système multiplie les heures par le taux pour obtenir le coût. Ces données sont utilisées pour facturer les clients, suivre les coûts réels par rapport au budget, et analyser la rentabilité des projets."
  },
  {
    question: "Comment sont gérés les devis et leur conversion en factures?",
    answer: "Les devis sont créés dans la table 'quotations' avec leurs produits détaillés dans 'quotation_products'. Lorsqu'un devis est accepté (statut 'accepté'), il peut être converti en facture dans la table 'invoices' avec ses éléments dans 'invoice_items'. Le système maintient la relation entre le devis d'origine et la facture résultante, permettant de suivre le taux de conversion des devis et d'analyser les modifications entre devis et facture finale."
  }
];

// Questions-réponses sur l'API du système
const systemApiQA = [
  {
    question: "Comment récupérer la liste des projets en cours via l'API?",
    answer: "Pour récupérer la liste des projets en cours, effectuez une requête GET sur `/api/projects?status=en_cours`. Cela retournera tous les projets dont le statut est 'en_cours' avec leurs informations de base comme l'ID, le nom, le client, les dates de début et de fin, et l'adresse."
  },
  {
    question: "Comment créer un nouveau client via l'API?",
    answer: "Pour créer un nouveau client, envoyez une requête POST à `/api/clients` avec un corps JSON contenant les informations du client: `{\"firstname\": \"Prénom\", \"lastname\": \"Nom\", \"street_number\": \"123\", \"street_name\": \"Rue Example\", \"zip_code\": \"75000\", \"city\": \"Paris\", \"email\": \"client@example.com\", \"phone\": \"+33123456789\"}`."
  },
  {
    question: "Comment mettre à jour le statut d'un projet via l'API?",
    answer: "Pour mettre à jour le statut d'un projet, envoyez une requête PATCH à `/api/projects/{id}` avec un corps JSON `{\"status\": \"termine\"}` où `{id}` est l'identifiant du projet et le statut peut être l'une des valeurs suivantes: 'prospect', 'en_cours', 'termine', 'en_pause', 'annule'."
  },
  {
    question: "Comment récupérer les détails d'un devis spécifique via l'API?",
    answer: "Pour récupérer les détails complets d'un devis, effectuez une requête GET sur `/api/quotations/{id}` où `{id}` est l'identifiant du devis. Cela retournera toutes les informations du devis, y compris les produits associés, le projet lié, les dates, montants et statut."
  },
  {
    question: "Comment créer une nouvelle facture via l'API?",
    answer: "Pour créer une nouvelle facture, envoyez une requête POST à `/api/invoices` avec un corps JSON contenant les informations de la facture: `{\"project_id\": 123, \"reference\": \"FACT-2023-001\", \"issue_date\": \"2023-12-01\", \"due_date\": \"2023-12-31\", \"total_ht\": 10000, \"tva_rate\": 20, \"total_ttc\": 12000, \"status\": \"envoyée\", \"items\": [{\"description\": \"Travaux de maçonnerie\", \"quantity\": 1, \"unit_price\": 10000, \"total_price\": 10000}]}`."
  },
  {
    question: "Comment enregistrer un paiement pour une facture via l'API?",
    answer: "Pour enregistrer un paiement, envoyez une requête POST à `/api/payments` avec un corps JSON: `{\"invoice_id\": 123, \"amount\": 5000, \"payment_date\": \"2023-12-15\", \"payment_method\": \"virement\", \"reference\": \"VIR-2023-123\"}`. Le système mettra automatiquement à jour le statut de la facture en fonction du montant payé par rapport au total."
  },
  {
    question: "Comment récupérer le calendrier des événements d'un projet via l'API?",
    answer: "Pour récupérer tous les événements liés à un projet, effectuez une requête GET sur `/api/calendar-events?project_id={id}` où `{id}` est l'identifiant du projet. Vous pouvez également filtrer par période avec les paramètres `start_date` et `end_date`, par exemple: `/api/calendar-events?project_id=123&start_date=2023-12-01&end_date=2023-12-31`."
  },
  {
    question: "Comment ajouter un nouvel équipement via l'API?",
    answer: "Pour ajouter un nouvel équipement, envoyez une requête POST à `/api/equipment` avec un corps JSON: `{\"name\": \"Perceuse à percussion\", \"reference\": \"PP-2023-001\", \"category_id\": 3, \"supplier_id\": 2, \"purchase_date\": \"2023-11-15\", \"purchase_price\": 450, \"status\": \"disponible\", \"location\": \"Entrepôt principal\", \"maintenance_interval\": 90}`."
  },
  {
    question: "Comment récupérer les statistiques financières d'un projet via l'API?",
    answer: "Pour récupérer les statistiques financières d'un projet, effectuez une requête GET sur `/api/projects/{id}/financial-stats` où `{id}` est l'identifiant du projet. Cela retournera un résumé incluant le budget total, les dépenses actuelles, les factures émises, les paiements reçus, et le pourcentage de réalisation financière."
  },
  {
    question: "Comment rechercher des clients par nom ou ville via l'API?",
    answer: "Pour rechercher des clients, utilisez une requête GET sur `/api/clients/search?q={terme}` où `{terme}` est votre terme de recherche. Le système cherchera dans les noms, prénoms, villes et autres champs pertinents. Vous pouvez également filtrer par ville spécifique avec `/api/clients?city={ville}`."
  }
];

// Combiner toutes les questions-réponses
const allQA = [...buildingQA, ...apiQA, ...databaseQA, ...systemApiQA];

// Générer plus de données en variant les questions existantes
function generateVariations(qaList, numberOfVariations = 5) {
  const variations = [];
  
  qaList.forEach(qa => {
    // Ajouter l'original
    variations.push(qa);
    
    // Préfixes pour varier les questions
    const prefixes = [
      "Pouvez-vous m'expliquer ",
      "J'aimerais savoir ",
      "Pourriez-vous détailler ",
      "Je cherche des informations sur ",
      "Expliquez-moi ",
      "Je voudrais comprendre ",
      "Informez-moi sur "
    ];
    
    // Générer des variations
    for (let i = 0; i < numberOfVariations; i++) {
      if (i < prefixes.length) {
        // Variation avec préfixe
        const questionBase = qa.question.charAt(0).toLowerCase() + qa.question.slice(1);
        const questionWithoutPunctuation = questionBase.replace(/[?.,]/g, '');
        const newQuestion = `${prefixes[i]}${questionWithoutPunctuation}?`;
        
        variations.push({
          question: newQuestion,
          answer: qa.answer
        });
      } else {
        // Autres variations possibles ici
      }
    }
  });
  
  return variations;
}

// Convertir les données au format JSONL pour fine-tuning
function convertToJSONL(data) {
  return data.map(item => {
    // Format pour le fine-tuning de modèles comme Mistral
    return {
      messages: [
        { role: "user", content: item.question },
        { role: "assistant", content: item.answer }
      ]
    };
  });
}

// Générer les données avec variations
const expandedData = generateVariations(allQA);
const jsonlData = convertToJSONL(expandedData);

// Écrire les données dans un fichier JSONL
const outputDir = path.join(__dirname, 'data', 'training');
const outputFile = path.join(outputDir, 'building_qa_training.jsonl');

// S'assurer que le répertoire existe
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

// Écrire chaque objet JSON sur une ligne séparée
fs.writeFileSync(
  outputFile, 
  jsonlData.map(item => JSON.stringify(item)).join('\n')
);

console.log(`Données d'entraînement générées avec succès: ${jsonlData.length} exemples`);
console.log(`Fichier sauvegardé: ${outputFile}`); 