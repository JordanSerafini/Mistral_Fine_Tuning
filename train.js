const fs = require('fs');
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

async function trainModel() {
    // Lire le fichier JSONL
    const data = fs.readFileSync('./data/training/building_qa_training.jsonl', 'utf8');
    const lines = data.trim().split('\n');
    
    console.log(`Chargement de ${lines.length} exemples d'entraînement...`);

    // Pour chaque ligne du fichier
    for (let i = 0; i < lines.length; i++) {
        const example = JSON.parse(lines[i]);
        const userMessage = example.messages.find(m => m.role === 'user').content;
        const assistantMessage = example.messages.find(m => m.role === 'assistant').content;
        
        try {
            // Construire le prompt d'entraînement
            const prompt = `Tu es un expert en construction et bâtiment. Voici un exemple d'interaction :
Question: ${userMessage}
Réponse: ${assistantMessage}

Maintenant, réponds à cette question comme je viens de le faire.
Question: ${userMessage}`;

            // Échapper les caractères spéciaux pour la ligne de commande
            const escapedPrompt = prompt.replace(/"/g, '\\"');

            // Utiliser la commande ollama directement
            const command = `ollama run batiment-expert "${escapedPrompt}"`;
            const { stdout, stderr } = await execPromise(command);

            if (stderr) {
                console.error(`Attention pour l'exemple ${i + 1}:`, stderr);
            }

            console.log(`Exemple ${i + 1}/${lines.length} traité avec succès`);
            console.log(`Réponse du modèle:`, stdout);
            console.log(`Progression: ${((i + 1) / lines.length * 100).toFixed(2)}%`);
            console.log('-------------------');

        } catch (error) {
            console.error(`Erreur lors du traitement de l'exemple ${i + 1}:`, error);
        }

        // Pause entre chaque exemple
        await new Promise(resolve => setTimeout(resolve, 2000));
    }

    console.log('Entraînement terminé !');
}

// Lancer l'entraînement
trainModel().catch(console.error); 