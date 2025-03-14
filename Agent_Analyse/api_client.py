#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Client exemple pour l'API Mistral 7B Fine-tuné.
Ce script montre comment utiliser l'API depuis votre application.
"""

import requests
import argparse
import json
import time

def parse_args():
    parser = argparse.ArgumentParser(description="Client pour l'API Mistral 7B Fine-tuné")
    parser.add_argument("--api_url", type=str, default="http://localhost:8000",
                      help="URL de l'API")
    parser.add_argument("--prompt", type=str, default="Explique-moi le réchauffement climatique",
                      help="Prompt à envoyer au modèle")
    parser.add_argument("--max_new_tokens", type=int, default=512,
                      help="Nombre maximum de tokens à générer")
    parser.add_argument("--temperature", type=float, default=0.7,
                      help="Température pour la génération")
    parser.add_argument("--top_p", type=float, default=0.9,
                      help="Top-p pour la génération")
    parser.add_argument("--top_k", type=int, default=50,
                      help="Top-k pour la génération")
    return parser.parse_args()

def check_api_health(api_url):
    """
    Vérifie si l'API est disponible et en bon état
    """
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            return True
        else:
            print(f"L'API n'est pas en bon état. Code de statut : {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"Erreur lors de la vérification de l'état de l'API : {e}")
        return False

def generate_text(api_url, prompt, max_new_tokens=512, temperature=0.7, top_p=0.9, top_k=50):
    """
    Envoie une requête à l'API pour générer du texte
    """
    url = f"{api_url}/generate"
    
    payload = {
        "prompt": prompt,
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("Envoi de la requête à l'API...")
        start_time = time.time()
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            
            total_time = time.time() - start_time
            
            print(f"\nRéponse générée en {total_time:.2f} secondes ({result['processing_time_ms']:.2f} ms pour le modèle):\n")
            print(result["generated_text"])
            return result["generated_text"]
        else:
            print(f"Erreur: {response.status_code}")
            print(response.text)
            return None
    except requests.RequestException as e:
        print(f"Erreur lors de la génération de texte: {e}")
        return None

def main():
    args = parse_args()
    
    if not check_api_health(args.api_url):
        print("L'API n'est pas disponible. Assurez-vous que le serveur est en cours d'exécution.")
        return
    
    generate_text(
        args.api_url,
        args.prompt,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_p=args.top_p,
        top_k=args.top_k
    )

class MistralClient:
    """
    Classe client pour l'API Mistral 7B Fine-tuné.
    Utilisez cette classe dans votre application.
    """
    
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        
    def is_healthy(self):
        """
        Vérifie si l'API est disponible et en bon état
        """
        return check_api_health(self.api_url)
    
    def generate(self, prompt, max_new_tokens=512, temperature=0.7, top_p=0.9, top_k=50):
        """
        Génère du texte à partir d'un prompt
        """
        return generate_text(
            self.api_url,
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k
        )

# Exemple d'utilisation de la classe client dans votre application
def example_usage():
    """
    Exemple d'utilisation de la classe client dans votre application
    """
    # Créer un client
    client = MistralClient(api_url="http://localhost:8000")
    
    # Vérifier si l'API est disponible
    if not client.is_healthy():
        print("L'API n'est pas disponible.")
        return
    
    # Génération simple
    response = client.generate("Explique-moi comment fonctionne l'intelligence artificielle.")
    
    # Génération avec plus de contrôle
    response = client.generate(
        "Résume l'histoire de la France en quelques paragraphes.",
        max_new_tokens=1024,  # Réponse plus longue
        temperature=0.8,  # Un peu plus de créativité
        top_p=0.92,
        top_k=50
    )
    
    # Utilisation dans une chaîne de traitement
    prompt = "Analyse le sentiment du texte suivant : 'Je suis très content du service, merci beaucoup!'"
    sentiment = client.generate(prompt)
    
    # Traiter le résultat
    if "positif" in sentiment.lower():
        print("Le sentiment est positif!")
    else:
        print("Le sentiment n'est pas positif.")

if __name__ == "__main__":
    main()
    
    # Décommentez la ligne suivante pour voir l'exemple d'utilisation
    # example_usage() 