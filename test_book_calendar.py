#!/usr/bin/env python3
# coding: utf-8
"""
Script de test pour l'endpoint de réservation de calendrier
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8080"
BOOK_ENDPOINT = f"{BASE_URL}/book-calendar"

# Exemple de données de réservation minimales (tous les champs sauf calendar_url sont optionnels)
booking_data = {
    "calendar_url": "https://calendly.com/example/30min",  # Remplacez par une vraie URL
    # Tous les autres champs sont optionnels et utiliseront les valeurs par défaut
    # Par défaut, le navigateur est visible (headless=False)
    # Pour activer le mode headless, ajoutez: "headless": True
}

# Exemple avec des données personnalisées (décommentez pour utiliser)
# booking_data = {
#     "calendar_url": "https://calendly.com/example/30min",
#     "nom": "Cyril Moriou",
#     "email": "lexpertisedunotaire@gmail.com",
#     "telephone": "+33774334897",
#     "site_web": "etude-lyon-bugeaud.notaires.fr",
#     "societe": "Étude Lyon Bugeaud",
#     "preference_creneau": "Premier créneau disponible dès demain dans les 7 prochains jours",
#     "type_rdv": "Visio-conférence Google Meet",
#     "message": "Dans le cadre du (re)lancement de notre stratégie de comm...",
#     "headless": False,
#     "max_steps": 20
# }


def test_book_calendar():
    """Teste l'endpoint de réservation de calendrier"""
    print("🚀 Test de réservation de calendrier")
    print(f"URL du serveur: {BASE_URL}")
    print(f"Endpoint: {BOOK_ENDPOINT}")
    print(f"\n📋 Données de réservation:")
    print(json.dumps(booking_data, indent=2, ensure_ascii=False))
    
    try:
        print("\n⏳ Envoi de la requête...")
        response = requests.post(BOOK_ENDPOINT, json=booking_data, timeout=300)
        
        print(f"\n📊 Statut HTTP: {response.status_code}")
        print(f"📄 Réponse:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                status = result.get("status")
                if status == "SUCCESS_RESERVATION":
                    print("\n✅ Réservation réussie!")
                elif status == "AUCUN_CRENEAU_DISPONIBLE":
                    print("\n⚠️  Aucun créneau disponible")
                elif status == "ERREUR_RESERVATION":
                    print("\n❌ Erreur lors de la réservation")
            else:
                print(f"\n❌ Erreur: {result.get('error')}")
        else:
            print(f"\n❌ Erreur HTTP: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Erreur: Impossible de se connecter au serveur")
        print("Assurez-vous que le serveur est démarré avec: python server.py")
    except requests.exceptions.Timeout:
        print("\n⏱️  Timeout: La requête a pris trop de temps")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")


if __name__ == "__main__":
    test_book_calendar()

