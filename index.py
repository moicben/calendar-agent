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

    # macOS default install
    mac_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(mac_path):
        return mac_path

    # Linux common paths
    linux_path = "/usr/bin/google-chrome"
    if os.path.exists(linux_path):
        return linux_path

    return linux_path | mac_path


def _create_browser(headless: bool, proxy: Optional[ProxySettings] = None) -> Browser:
    chrome_path = _resolve_chrome_path()
    devtools_enabled = False

    browser_args = [
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-sync",
        "--new-window",
        "--remote-debugging-address=127.0.0.1",
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
        args=browser_args,
        proxy=proxy,
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
Réserve un rendez-vous Calendly sur {url} avec ces informations:
Nom: {user_info.get('nom')} | Email: {user_info.get('email')} | Téléphone: {user_info.get('telephone')}
Société: {user_info.get('societe')} | Site: {user_info.get('site_web')} | Message: {user_info.get('message')}

Étapes à suivre:
1) Va-sur {url}. Patiente jusqu'à ce que la page soit chargée. Si page introuvable Calendly ou ne charge pas → ERREUR_RESERVATION
2) Cherche des créneaux disponibles sur les 7 prochains jours. Si aucun → AUCUN_CRENEAU_DISPONIBLE
3) Sélectionne le premier créneau disponible
4) Valide le créneau en cliquant sur "Suivant" ou "Next"
5) Remplis le formulaire avec les informations fournies.
6) Soumets le formulaire, Si confirmation visible -> SUCCESS_RESERVATION, sinon -> ERREUR_RESERVATION

Retourne UNE de ces valeurs: SUCCESS_RESERVATION, AUCUN_CRENEAU_DISPONIBLE, ERREUR_RESERVATION
Préfère visioconférence (Google Meet) si option disponible.
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
        
        # Laisse 4 secondes au navigateur pour se charger
        time.sleep(4)

        
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
