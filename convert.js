const fs = require('fs');

function readJSONLFile(filePath) {
    const content = fs.readFileSync('./data/training/building_qa_training.jsonl', 'utf-8');
    return content.trim().split('\n').map(line => JSON.parse(line));
}

function convertToModelfileFormat(data) {
    let modelfileContent = `FROM mistral:latest
PARAMETER temperature 0.7

SYSTEM """Vous êtes un assistant spécialisé dans le domaine du bâtiment, capable de répondre aux questions techniques et réglementaires."""\n\n`;

    data.forEach(item => {
        if (item.messages && Array.isArray(item.messages)) {
            const question = item.messages.find(m => m.role === 'user')?.content || '';
            const answer = item.messages.find(m => m.role === 'assistant')?.content || '';
            
            modelfileContent += `MESSAGE "Question: ${question.replace(/"/g, '\\"')}"\n`;
            modelfileContent += `MESSAGE "Réponse: ${answer.replace(/"/g, '\\"')}"\n\n`;
        }
    });

    return modelfileContent;
}

try {
    const data = readJSONLFile();
    const modelfileContent = convertToModelfileFormat(data);
    fs.writeFileSync('Modelfile', modelfileContent);
    console.log('Modelfile généré avec succès !');
    
    // Afficher un aperçu du contenu généré
    console.log('\nAperçu du Modelfile généré (premières lignes) :');
    console.log(modelfileContent.split('\n').slice(0, 10).join('\n'));
} catch (error) {
    console.error('Erreur:', error);
}