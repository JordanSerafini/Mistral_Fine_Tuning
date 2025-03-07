require('dotenv').config();
const express = require('express');
const { ragQuery } = require('./rag');

// Créer l'application Express
const app = express();
app.use(express.json());

// Port d'écoute
const PORT = process.env.PORT || 3000;

// Route pour la page d'accueil
app.get('/', (req, res) => {
  res.send(`
    <html>
      <head>
        <title>Chatbot Bâtiment</title>
        <style>
          body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
          }
          h1 {
            color: #2c3e50;
          }
          .chat-container {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            height: 400px;
            overflow-y: auto;
            margin-bottom: 20px;
            background-color: #f9f9f9;
          }
          .message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 5px;
          }
          .user-message {
            background-color: #3498db;
            color: white;
            margin-left: 20%;
          }
          .bot-message {
            background-color: #eee;
            margin-right: 20%;
          }
          .input-container {
            display: flex;
          }
          #user-input {
            flex-grow: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
          }
          button {
            padding: 10px 20px;
            background-color: #2c3e50;
            color: white;
            border: none;
            border-radius: 4px;
            margin-left: 10px;
            cursor: pointer;
          }
          button:hover {
            background-color: #1a252f;
          }
        </style>
      </head>
      <body>
        <h1>Chatbot Spécialisé dans le Bâtiment</h1>
        <div class="chat-container" id="chat-container">
          <div class="message bot-message">
            Bonjour ! Je suis votre assistant spécialisé dans le domaine du bâtiment. Comment puis-je vous aider aujourd'hui ?
          </div>
        </div>
        <div class="input-container">
          <input type="text" id="user-input" placeholder="Posez votre question ici...">
          <button id="send-button">Envoyer</button>
        </div>

        <script>
          const chatContainer = document.getElementById('chat-container');
          const userInput = document.getElementById('user-input');
          const sendButton = document.getElementById('send-button');

          // Fonction pour ajouter un message au chat
          function addMessage(content, isUser) {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message');
            messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');
            messageDiv.textContent = content;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
          }

          // Fonction pour envoyer une question au serveur
          async function sendQuestion() {
            const question = userInput.value.trim();
            if (!question) return;

            // Afficher la question de l'utilisateur
            addMessage(question, true);
            userInput.value = '';

            // Afficher un message de chargement
            const loadingMessage = document.createElement('div');
            loadingMessage.classList.add('message', 'bot-message');
            loadingMessage.textContent = 'Recherche en cours...';
            chatContainer.appendChild(loadingMessage);

            try {
              // Envoyer la requête au serveur
              const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify({ question })
              });

              const data = await response.json();
              
              // Remplacer le message de chargement par la réponse
              chatContainer.removeChild(loadingMessage);
              addMessage(data.answer, false);
            } catch (error) {
              // En cas d'erreur, afficher un message d'erreur
              chatContainer.removeChild(loadingMessage);
              addMessage('Désolé, une erreur est survenue. Veuillez réessayer.', false);
              console.error('Erreur:', error);
            }
          }

          // Événements
          sendButton.addEventListener('click', sendQuestion);
          userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendQuestion();
          });
        </script>
      </body>
    </html>
  `);
});

// Route API pour le chat
app.post('/api/chat', async (req, res) => {
  try {
    const { question } = req.body;
    
    if (!question) {
      return res.status(400).json({ error: 'La question est requise' });
    }
    
    console.log(`Nouvelle question reçue: ${question}`);
    
    // Utiliser le RAG pour générer une réponse
    const answer = await ragQuery(question);
    
    res.json({ answer });
    
  } catch (error) {
    console.error('Erreur lors du traitement de la question:', error);
    res.status(500).json({ 
      error: 'Une erreur est survenue lors du traitement de votre question',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// Démarrer le serveur
app.listen(PORT, () => {
  console.log(`Serveur démarré sur http://localhost:${PORT}`);
  console.log('Chatbot bâtiment prêt à répondre à vos questions!');
}); 