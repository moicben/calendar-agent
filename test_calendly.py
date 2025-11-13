import os
from dotenv import load_dotenv
from browser_use import Agent, ChatOpenAI, Browser
from pydantic import BaseModel
from enum import Enum

load_dotenv()

# Configuration statique
linux_path = "/usr/bin/google-chrome"
calendar_url = "https://calendly.com/designetfonctionnel/j-ai-une-question"

# Données utilisateur statiques
user_info = {
    'nom': 'Test User',
    'email': 'test@example.com',
    'telephone': '+33123456789',
    'site_web': 'https://example.com',
    'societe': 'Test Company',
    'preference_creneau': 'Matin',
    'type_rdv': 'Consultation',
    'message': 'Bonjour, je souhaite prendre rendez-vous pour une consultation.'
}

# Arguments du navigateur pour Linux
browser_args = [
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-background-networking",
    "--disable-sync",
    "--new-window",
    "--remote-debugging-address=127.0.0.1",
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-gpu",
]

# Prompt simplifié pour la réservation
booking_prompt = f"""Va sur {calendar_url} et réserve un rendez-vous Calendly avec:
Nom: {user_info.get('nom')}
Email: {user_info.get('email')}
Téléphone: {user_info.get('telephone')}
Message: {user_info.get('message')}"""

class BookingStatus(str, Enum):
    SUCCESS_RESERVATION = "SUCCESS_RESERVATION"
    AUCUN_CRENEAU_DISPONIBLE = "AUCUN_CRENEAU_DISPONIBLE"
    ERREUR_RESERVATION = "ERREUR_RESERVATION"

class BookingOutput(BaseModel):
    status: BookingStatus

def serialize_result(obj):
    """Sérialise le résultat pour JSON."""
    try:
        if hasattr(obj, 'model_dump'):
            return obj.model_dump()
        elif hasattr(obj, 'dict'):
            return obj.dict()
        elif isinstance(obj, list):
            return [serialize_result(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: serialize_result(v) for k, v in obj.items()}
        else:
            return str(obj)
    except Exception:
        return str(obj)

if __name__ == "__main__":
    try:
        # Créer le navigateur sans proxy (comme test.py)
        browser = Browser(
            executable_path=linux_path,
            headless=False,
            args=browser_args,
        )
        
        # Créer l'agent immédiatement (pas de sleep)
        agent = Agent(
            task=booking_prompt,
            llm=ChatOpenAI(model="gpt-4o-mini"),
            browser=browser,
            output_model_schema=BookingOutput,
        )
        
        # Exécuter la réservation
        print(f"Démarrage de la réservation sur {calendar_url}")
        result = agent.run_sync(max_steps=20)
        
        # Afficher le résultat
        serialized_result = serialize_result(result)
        print("\n=== Résultat ===")
        print(serialized_result)
        
        # Nettoyer
        try:
            browser.close()
        except Exception:
            pass
            
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
