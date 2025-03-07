def detect_database(query: str) -> str:
    """
    Détecte si une requête doit être envoyée à PostgreSQL ou Elasticsearch.
    Retourne "pg" ou "es".
    """
    # 🔍 Mots-clés pour PostgreSQL
    pg_keywords = ["facture", "devis", "paiement", "chantier", "planning", "client", "fournisseur", "commande", "matériaux"]
    
    # 🔍 Mots-clés pour Elasticsearch (recherche full-text)
    es_keywords = ["recherche", "documents", "emails", "contrat", "message", "note", "commentaire", "historique"]

    # Convertir la requête en minuscule
    query_lower = query.lower()

    # Vérifier si la requête contient un mot-clé PG
    if any(word in query_lower for word in pg_keywords):
        return "pg"

    # Vérifier si la requête contient un mot-clé ES
    if any(word in query_lower for word in es_keywords):
        return "es"

    # Si incertain, par défaut PG
    return "pg"

# Exemple d'utilisation
query1 = "Quelle est la dernière facture de M. Durand ?"
query2 = "Recherche le contrat du client Dupont"
query3 = "Quels sont les chantiers en cours ?"

print(detect_database(query1))  # ➝ "pg"
print(detect_database(query2))  # ➝ "es"
print(detect_database(query3))  # ➝ "pg"
