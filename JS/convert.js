const fs = require('fs');

function readJSONLFile(filePath) {
    const content = fs.readFileSync('./data/training/building_qa_training.jsonl', 'utf-8');
    return content.trim().split('\n').map(line => JSON.parse(line));
}

function convertToModelfileFormat(data) {
    // Format simple qui fonctionne avec Ollama
    let modelfileContent = `FROM mistral:latest
PARAMETER temperature 0.7
SYSTEM "Vous êtes un assistant spécialisé dans le domaine du bâtiment, capable de répondre aux questions techniques et réglementaires."
`;

    // Limiter à 50 exemples pour éviter un fichier trop volumineux
    const limitedData = data.slice(0, 50);
    console.log(`Utilisation des ${limitedData.length} premiers exemples`);

    limitedData.forEach(item => {
        if (item.messages && Array.isArray(item.messages)) {
            const question = item.messages.find(m => m.role === 'user')?.content || '';
            const answer = item.messages.find(m => m.role === 'assistant')?.content || '';
            
            // Échapper les guillemets et les retours à la ligne
            const escapedQuestion = question.replace(/"/g, '\\"').replace(/\n/g, ' ');
            const escapedAnswer = answer.replace(/"/g, '\\"').replace(/\n/g, ' ');
            
            modelfileContent += `MESSAGE "Question: ${escapedQuestion}"\n`;
            modelfileContent += `MESSAGE "Réponse: ${escapedAnswer}"\n`;
        }
    });

    return modelfileContent;
}

try {
    const data = readJSONLFile();
    console.log(`Nombre total d'entrées lues : ${data.length}`);
    
    const modelfileContent = convertToModelfileFormat(data);
    fs.writeFileSync('Modelfile.fixed', modelfileContent);
    console.log('Modelfile généré avec succès !');
    
    // Afficher un aperçu du contenu généré
    console.log('\nAperçu du Modelfile généré (premières lignes) :');
    console.log(modelfileContent.split('\n').slice(0, 10).join('\n'));
} catch (error) {
    console.error('Erreur:', error);
}