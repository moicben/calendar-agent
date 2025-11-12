# Module Python pour la réservation de calendriers
# Utilisé par agi-engine/services/booker/book.js

import os
import time
import random
import logging
import sys
from typing import Optional

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
from browser_use.browser import ProxySettings


load_dotenv()

# Récupère une variable d'environnement en booléen
def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}

# Récupère une variable d'environnement en float
def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(str(raw).strip())
    except Exception:
        return default

# Résout le chemin du navigateur Chrome
def _resolve_chrome_path() -> str:
    # Priority: explicit env → common macOS → common Linux
    env_path = os.environ.get("CHROME_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    # macOS default install
    mac_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(mac_path):
        return mac_path

    # Linux common paths
    for p in [
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ]:
        if os.path.exists(p):
            return p

    # Fallback to env or mac path even if not present; Browser will raise useful error
    return env_path or mac_path


def _create_browser(headless: bool, proxy: Optional[ProxySettings] = None) -> Browser:
    chrome_path = _resolve_chrome_path()
    devtools_enabled = _env_bool("BROWSERUSE_DEVTOOLS", not headless)

    browser_args = [
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-sync",
    ]
    
    # Ajouter des arguments supplémentaires pour les VM si proxy est utilisé
    if proxy:
        browser_args.extend([
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--window-size=960,1080",
        ])

    return Browser(
        executable_path=chrome_path,
        headless=headless,
        devtools=devtools_enabled,
        enable_default_extensions=False,
        proxy=proxy,
        args=browser_args,
        wait_for_network_idle_page_load_time=5,
        minimum_wait_page_load_time=10,
    )

# Charge un proxy aléatoire depuis le fichier proxies
def _load_random_proxy(proxies_file: str = "proxies") -> Optional[ProxySettings]:
    """Charge un proxy aléatoire depuis le fichier proxies."""
    try:
        with open(proxies_file, 'r', encoding='utf-8') as f:
            proxy_lines = [line.strip() for line in f.readlines() if line.strip()]
        
        if not proxy_lines:
            return None
        
        # Sélectionner un proxy aléatoire
        random_proxy_line = random.choice(proxy_lines)
        
        # Parser le format: host:port:username:password
        parts = random_proxy_line.split(':')
        if len(parts) != 4:
            return None
        
        host, port, username, password = parts
        
        proxy_config = ProxySettings(
            server=f'https://{host}:{port}',
            username=username,
            password=password,
            bypass='localhost,127.0.0.1'
        )
        
        return proxy_config
        
    except FileNotFoundError:
        return None
    except Exception:
        return None

# Prompt concis pour la réservation
def _create_booking_prompt(url: str, user_info: dict) -> str:
    """Crée un prompt concis pour la réservation."""
    return f"""
Mission: Réserver un rendez-vous Calendly sur l'URL suivante: {url}.

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

Étapes explicites à suivre (sans rien modifier):
1) Lance le navigateur, ouvre un nouvel onglet, attends que le navigateur soit prêt
2) Rends-toi sur l'URL du calendrier : "{url}". Si page introuvable/404 ou si le widget Calendly ne charge pas, retourne ERREUR_RESERVATION et ARRÊTE.
3) Cherche des jours disponibles sur les 7 prochains jours. Si aucun créneau disponible, retourne AUCUN_CRENEAU_DISPONIBLE et ARRÊTE immédiatement.
4) Clique sur le premier jour disponible dans le calendrier que tu as trouvé.
5) Clique sur le premier créneau horaire disponible dans le jour que tu as sélectionné.
6) Clique sur "Suivant"ou "Next" pour accéder au formulaire de réservation.
7) Une fois le formulaire affiché, analyse-le pour identifier les champs obligatoires
8) Remplis les champs obligatoires identifiés avec parcimonie les informations suivantes:
   - Nom complet: {user_info.get('nom')}
   - Email: {user_info.get('email')}
   - Téléphone: {user_info.get('telephone')} (adapter le format si requis)
   - Site/Société: {user_info.get('site_web')} / {user_info.get('societe')}
   - Message/Notes: {user_info.get('message')}
   - Listes déroulantes obligatoires: première option raisonnable.
   - Cases à cocher obligatoires: cocher.
   - Type de RDV: {user_info.get('type_rdv')}
9) En cas d'erreur de validation, corrige puis réessaie jusqu'à 5 fois.
10) Clique sur "Confirmer l'événement", "Envoyer", "Soumettre" ou "Submit" pour soumettre le formulaire.
11) Si confirmation visible "You are scheduled" ou "Vous avez rendez-vous" ou "Réservation confirmée" → retourne SUCCESS_RESERVATION et ARRÊTE, sinon → retourne ERREUR_RESERVATION et ARRÊTE

Contraintes:
- Agis de façon autonome; n'attends aucune confirmation manuelle.
- Ne change pas le fuseau horaire; conversion mentale seulement si nécessaire.
- N'essaie pas de forcer une disponibilité via refresh/navigation annexe.
- Privilégier toujours la visioconférence à l'appel par téléphone, dans le lieu du RDV ou option de réservation. (Google Meet de préférence).
- Dans le message/Notes du RDV utiliser des retours en appui de "Entrer" pour chaque ligne de texte.
- Si champ avec demande d'informations complèmentaires ou autres champs similaires, se servir de {user_info.get('message')}
- CRITIQUE: Dès que tu as déterminé plusieurs fois le statut final (SUCCESS_RESERVATION, AUCUN_CRENEAU_DISPONIBLE, ou ERREUR_RESERVATION), retourne ce statut comme résultat final de la tâche et ARRÊTE immédiatement. Ne continue pas à vérifier ou à boucler.
"""

# Fonction principale de réservation de calendrier
def book_calendar(calendar_url: str, user_info: dict, headless: Optional[bool] = None, max_steps: int = 20) -> dict:
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
    headless_default = _env_bool("BROWSERUSE_HEADLESS", False)
    headless = headless_default if headless is None else bool(headless)
    
    try:
        # Charger un proxy aléatoire
        proxy_config = _load_random_proxy()
        
        # Créer le navigateur en utilisant la fonction helper
        browser = _create_browser(headless=headless, proxy=proxy_config)
        
        # Créer le prompt de réservation
        booking_task = _create_booking_prompt(calendar_url, user_info)
        
        # Créer l'agent avec le modèle de sortie
        # Note: On garde BookingOutput pour structurer la sortie, mais on retourne le résultat brut
        from pydantic import BaseModel
        from enum import Enum
        
        class BookingStatus(str, Enum):
            SUCCESS_RESERVATION = "SUCCESS_RESERVATION"
            AUCUN_CRENEAU_DISPONIBLE = "AUCUN_CRENEAU_DISPONIBLE"
            ERREUR_RESERVATION = "ERREUR_RESERVATION"
        
        class BookingOutput(BaseModel):
            status: BookingStatus
        
        agent = Agent(
            task=booking_task,
            llm=ChatOpenAI(model="gpt-4o-mini"),
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
