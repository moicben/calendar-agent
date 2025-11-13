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

# Prompt pour la réservation
booking_prompt = f"""
Va sur {calendar_url} et réserve un rendez-vous avec les informations suivantes:

Données utilisateur :
- Nom: {user_info.get('nom')}
- Email: {user_info.get('email')}
- Téléphone: {user_info.get('telephone')}
- Site web: {user_info.get('site_web')}
- Société: {user_info.get('societe')}
- Préférence: {user_info.get('preference_creneau')}
- Type de RDV: {user_info.get('type_rdv')}
- Message: {user_info.get('message')}

IMPORTANT - Sortie finale requise :
Tu DOIS retourner exactement UNE de ces valeurs comme résultat final de la tâche (utilise la fonction de retour de résultat de l'agent, pas juste evaluate) :
- SUCCESS_RESERVATION
- AUCUN_CRENEAU_DISPONIBLE  
- ERREUR_RESERVATION

Une fois que tu as déterminé le statut, RETOURNE IMMÉDIATEMENT le résultat final et ARRÊTE. Ne continue pas à boucler.

Étapes à suivre:
1) Rends-toi sur l'URL du calendrier : "{calendar_url}". Si page introuvable/404 ou si le widget Calendly ne charge pas, retourne ERREUR_RESERVATION et ARRÊTE.
2) Cherche des jours disponibles sur les 7 prochains jours. Si aucun créneau disponible, retourne AUCUN_CRENEAU_DISPONIBLE et ARRÊTE immédiatement.
3) Clique sur le premier jour disponible dans le calendrier que tu as trouvé.
4) Clique sur le premier créneau horaire disponible dans le jour que tu as sélectionné.
5) Clique sur "Suivant"ou "Next" pour accéder au formulaire de réservation.
6) Une fois le formulaire affiché, analyse-le pour identifier les champs obligatoires
7) Remplis les champs obligatoires identifiés avec parcimonie les informations suivantes:
   - Nom complet: {user_info.get('nom')}
   - Email: {user_info.get('email')}
   - Téléphone: {user_info.get('telephone')} (adapter le format si requis)
   - Site/Société: {user_info.get('site_web')} / {user_info.get('societe')}
   - Message/Notes: {user_info.get('message')}
   - Listes déroulantes obligatoires: première option raisonnable.
   - Cases à cocher obligatoires: cocher.
   - Type de RDV: {user_info.get('type_rdv')}
8) Clique sur "Confirmer l'événement", "Envoyer", "Soumettre" ou "Submit" pour soumettre le formulaire.
9) En cas d'erreur de validation, ou champs incomplets, complète et corrige les champs en question puis réessaie de soumettre le formulaire.
10) Si confirmation visible "You are scheduled" ou "Vous avez rendez-vous" ou "Réservation confirmée" → retourne SUCCESS_RESERVATION et ARRÊTE, sinon → retourne ERREUR_RESERVATION et ARRÊTE

Contraintes:
- Agis de façon autonome; n'attends aucune confirmation manuelle.
- Ne change pas le fuseau horaire; conversion mentale seulement si nécessaire.
- N'essaie pas de forcer une disponibilité via refresh/navigation annexe.
- Privilégier toujours la visioconférence à l'appel par téléphone, dans le lieu du RDV ou option de réservation. (Google Meet de préférence).
- Dans le message/Notes du RDV utiliser des retours en appui de "Entrer" pour chaque ligne de texte.
- Si champ avec demande d'informations complèmentaires ou autres champs similaires, se servir de {user_info.get('message')}
- CRITIQUE: Dès que tu as déterminé plusieurs fois le statut final (SUCCESS_RESERVATION, AUCUN_CRENEAU_DISPONIBLE, ou ERREUR_RESERVATION), retourne ce statut comme résultat final de la tâche et ARRÊTE immédiatement. Ne continue pas à vérifier ou à boucler.
"""

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
