# Module Python pour la réservation de calendriers
# Utilisé par agi-engine/services/booker/book.js

import os
import time
import random
import logging
import sys
from typing import Optional 
from enum import Enum
from pydantic import BaseModel

from dotenv import load_dotenv

# Configuration du logging pour browser-use
# Rediriger tous les logs vers stdout pour PM2
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True  # Force la reconfiguration même si déjà configuré
)

# Configurer spécifiquement browser-use pour qu'il logge vers stdout
browser_use_logger = logging.getLogger('browser_use')
browser_use_logger.setLevel(logging.INFO)
browser_use_logger.propagate = True

# Runtime deps from browser-use
from browser_use import Agent, ChatOpenAI, Browser


load_dotenv()

# Modèles de sortie pour l'agent
class BookingStatus(str, Enum):
    SUCCESS_RESERVATION = "SUCCESS_RESERVATION"
    AUCUN_CRENEAU_DISPONIBLE = "AUCUN_CRENEAU_DISPONIBLE"
    ERREUR_RESERVATION = "ERREUR_RESERVATION"

class BookingOutput(BaseModel):
    status: BookingStatus


# Prompt concis pour la réservation
def _create_booking_prompt(url: str, user_info: dict) -> str:
    """Crée un prompt concis pour la réservation."""
    return f"""
    Réserve un rendez-vous sur le calendrier {url} avec ces informations:
    Nom: {user_info.get('nom')} | Email: {user_info.get('email')} | Téléphone: {user_info.get('telephone')}
    Société: {user_info.get('societe')} | Site: {user_info.get('site_web')} | Message: {user_info.get('message')}

    RÈGLES IMPORTANTES:
    - Le calendrier est une application SPA (Single Page Application) qui peut prendre 10-15 secondes à charger complètement
    - Si la page semble vide au début, ATTENDS au moins 15 secondes avant de prendre une décision
    - NE JAMAIS ouvrir un nouvel onglet si la page est en cours de chargement
    - Attends que les éléments interactifs apparaissent (boutons, calendrier, créneaux)
    - Si après 20 secondes la page est toujours vide, alors → ERREUR_RESERVATION

    Étapes à suivre:
    1) Va sur {url}. ATTENDS 15 secondes minimum pour que le calendrier charge complètement. Ne crée JAMAIS un nouvel onglet pendant le chargement.
    2) Cherche {user_info.get('preference_creneau')}. Si aucun → AUCUN_CRENEAU_DISPONIBLE
    3) Sélectionne le premier créneau disponible
    4) Valide le créneau sélectionné pour afficher le formulaire de réservation.
    5) Remplis le formulaire avec les informations fournies (respecte le format des champs).
    6) Soumets le formulaire, si confirmation visible "Rendez-vous réservé" ou "Confirmation". -> SUCCESS_RESERVATION, sinon -> ERREUR_RESERVATION

    Retourne UNE de ces valeurs: SUCCESS_RESERVATION, AUCUN_CRENEAU_DISPONIBLE, ERREUR_RESERVATION
    """

# Fonction principale de réservation de calendrier
def book_calendar(calendar_url: str, user_info: dict, headless: Optional[bool] = None, max_steps: int = 15) -> dict:
    """
    Réserve un créneau sur un calendrier donné.
    
    Args:
        calendar_url: URL du calendrier à réserver
        user_info: Dictionnaire contenant les informations utilisateur:
            - nom: str
            - email: str
            - telephone: str
            - site_web: str
            - societe: str
            - preference_creneau: str
            - type_rdv: str
            - message: str
        headless: Mode headless du navigateur (None = utiliser env var)
        max_steps: Nombre maximum d'étapes pour l'agent
        
    Returns:
        dict: {"raw_result": <résultat agent>, "error": None} ou {"raw_result": None, "error": "<message>"}
    """
    # Par défaut, afficher le navigateur
    headless_default = False
    headless = headless_default if headless is None else bool(headless)
    
    try:
        
        # Connexion CDP au browser
        browser = Browser(
            cdp_url="http://localhost:9222",
        )
        
        # Créer le prompt de réservation
        booking_task = _create_booking_prompt(calendar_url, user_info)
        
        # Créer l'agent avec le modèle de sortie
        agent = Agent(
            task=booking_task,
            llm=ChatOpenAI(model="gpt-5-mini"),
            browser=browser,
            output_model_schema=BookingOutput,
        )
        
        # Exécuter la réservation
        result = agent.run_sync(max_steps=max_steps)
        
        # Nettoyer le navigateur
        try:
            browser.close()
        except Exception:
            pass
        
        # Convertir le résultat en format sérialisable pour JSON
        # Le résultat peut être un objet Pydantic, une liste, ou autre
        import json as json_module
        
        def serialize_result(obj):
            """Sérialise le résultat pour JSON."""
            try:
                # Si c'est un modèle Pydantic, convertir en dict
                if hasattr(obj, 'model_dump'):
                    return obj.model_dump()
                elif hasattr(obj, 'dict'):
                    return obj.dict()
                # Si c'est une liste, sérialiser chaque élément
                elif isinstance(obj, list):
                    return [serialize_result(item) for item in obj]
                # Si c'est un dict, sérialiser récursivement
                elif isinstance(obj, dict):
                    return {k: serialize_result(v) for k, v in obj.items()}
                # Sinon, convertir en string
                else:
                    return str(obj)
            except Exception:
                return str(obj)
        
        serialized_result = serialize_result(result)
        
        # Retourner le résultat brut (sans extraction de statut)
        return {"raw_result": serialized_result, "error": None}
        
    except Exception as e:
        return {"raw_result": None, "error": str(e)}
