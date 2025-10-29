import os
import sys
import time
import random
from typing import Optional, Any

from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from enum import Enum

# Runtime deps from browser-use
from browser_use import Agent, ChatOpenAI, Browser
from browser_use.browser import ProxySettings
from uuid import uuid4
from threading import Thread, Lock
from typing import Dict


load_dotenv()

app = FastAPI(title="BrowserUse API", version="0.1.0")


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(str(raw).strip())
    except Exception:
        return default


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
    # user_data_dir = os.environ.get("BROWSERUSE_USER_DATA_DIR", "./browseruse-profile")
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
        #user_data_dir=user_data_dir,
        enable_default_extensions=False,
        proxy=proxy,
        args=browser_args,
        wait_for_network_idle_page_load_time=3 if proxy else 0.5,
        minimum_wait_page_load_time=1 if proxy else 0.25,
    )


def _wait_for_browseruse_ready() -> None:
    # Attente simple et configurable pour laisser BrowserUse initialiser ses composants
    delay_s = _env_float("BROWSERUSE_STARTUP_DELAY_S", 1.5)
    if delay_s > 0:
        time.sleep(delay_s)


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


def _create_booking_prompt(url: str, user_info: dict) -> str:
    """Crée un prompt concis pour la réservation."""
    return f"""
Mission: Réserver un créneau sur {url}.

Données:
- Nom: {user_info.get('nom')}
- Email: {user_info.get('email')}
- Téléphone: {user_info.get('telephone')}
- Site web: {user_info.get('site_web')}
- Société: {user_info.get('societe')}
- Préférence: {user_info.get('preference_creneau')}
- Type de RDV: {user_info.get('type_rdv')}
- Message: {user_info.get('message')}

Sortie attendue (retourne exactement UNE de ces valeurs, sans autre texte):
- SUCCESS_RESERVATION
- AUCUN_CRENEAU_DISPONIBLE
- ERREUR_RESERVATION

Étapes:
1) Lance le navigateur, ouvre un nouvel onglet, attends que le navigateur soit prêt, puis va sur {url}. Si page introuvable/404 ou si le widget calendrier (Calendly, cal.com, Google Calendar etc.) ne charge pas → ERREUR_RESERVATION.
2) Cherche des créneaux sur les 5 prochains jours. Si aucun → AUCUN_CRENEAU_DISPONIBLE.
3) Sélectionne le premier jour disponible dans le calendrier conforme aux préférences (généralement couleur plus visible ou contraste plus élevé).
4) Sélectionner le premier créneau horaire disponible dans le jour sélectionné.
4) Remplis le formulaire:
   - Nom complet: {user_info.get('nom')}
   - Email: {user_info.get('email')}
   - Téléphone: {user_info.get('telephone')} (adapter le format si requis)
   - Site/Société: {user_info.get('site_web')} / {user_info.get('societe')}
   - Message/Notes: {user_info.get('message')}
   - Listes déroulantes obligatoires: première option raisonnable.
   - Cases à cocher obligatoires: cocher.
   - Type de RDV: {user_info.get('type_rdv')}
5) En cas d'erreur de validation, corrige puis réessaie jusqu'à 3 fois.
6) Soumets. Si confirmation visible → SUCCESS_RESERVATION, sinon → ERREUR_RESERVATION.

Contraintes:
- Agis de façon autonome; n'attends aucune confirmation manuelle.
- Ne change pas le fuseau horaire; conversion mentale seulement si nécessaire.
- N'essaie pas de forcer une disponibilité via refresh/navigation annexe.
- Privilégier toujours la visioconférence à l'appel par téléphone, dans le lieu du RDV ou option de réservation. (Google Meet de préférence).
- Dans le message/Notes du RDV utiliser des retours en appui de "Entrer" pour chaque ligne de texte.
- Si champ avec demande d'informations complèmentaires ou autres champs similaires, se servir de {user_info.get('message')}
"""


class RunGoalRequest(BaseModel):
    goal: str
    start_url: Optional[str] = None
    headless: Optional[bool] = None
    max_steps: Optional[int] = None
    model: Optional[str] = None


class RunGoalResponse(BaseModel):
    ok: bool
    result: Optional[Any] = None
    error: Optional[str] = None


# -------------------
# Job store in-memory
# -------------------
_RUNS_LOCK: Lock = Lock()
_RUNS: Dict[str, dict] = {}


class CreateRunResponse(BaseModel):
    run_id: str
    status: str


class GetRunResponse(BaseModel):
    run_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None


# -------------------
# Booking models
# -------------------
class BookingStatus(str, Enum):
    SUCCESS_RESERVATION = "SUCCESS_RESERVATION"
    AUCUN_CRENEAU_DISPONIBLE = "AUCUN_CRENEAU_DISPONIBLE"
    ERREUR_RESERVATION = "ERREUR_RESERVATION"


class BookingOutput(BaseModel):
    status: BookingStatus


class BookingRequest(BaseModel):
    calendar_url: str
    nom: Optional[str] = "Cyril Moriou"
    email: Optional[str] = "lexpertisedunotaire@gmail.com"
    telephone: Optional[str] = "+33774334897"
    site_web: Optional[str] = "etude-lyon-bugeaud.notaires.fr"
    societe: Optional[str] = "Étude Lyon Bugeaud"
    preference_creneau: Optional[str] = "Premier créneau disponible dès demain dans les 7 prochains jours"
    type_rdv: Optional[str] = "Visio-conférence Google Meet"
    message: Optional[str] = "Dans le cadre du (re)lancement de notre stratégie de comm, et l'update de nos réseaux (TikTok / Instagram). Votre profil nous semble correspondre à nos besoins, pour nous accompagner sur la mise en forme de tout cela. \n Au plaisir d'en discuter.\nMerci,"
    headless: Optional[bool] = None
    max_steps: Optional[int] = 20


class BookingResponse(BaseModel):
    ok: bool
    status: Optional[str] = None
    error: Optional[str] = None


def _run_job(run_id: str, req: RunGoalRequest) -> None:
    # Mark running
    with _RUNS_LOCK:
        _RUNS[run_id]["status"] = "running"
        _RUNS[run_id]["error"] = None
        _RUNS[run_id]["result"] = None

    headless_default = _env_bool("BROWSERUSE_HEADLESS", True)
    headless = headless_default if req.headless is None else bool(req.headless)
    model = req.model or os.environ.get("BROWSERUSE_MODEL", "gpt-5-nano")

    try:
        browser = _create_browser(headless=headless)
        _wait_for_browseruse_ready()
        agent = Agent(
            task=req.goal,
            llm=ChatOpenAI(model=model),
            browser=browser,
        )
        output = agent.run_sync()
        with _RUNS_LOCK:
            _RUNS[run_id]["status"] = "succeeded"
            _RUNS[run_id]["result"] = str(output)
    except Exception as e:  # noqa: BLE001
        with _RUNS_LOCK:
            _RUNS[run_id]["status"] = "failed"
            _RUNS[run_id]["error"] = str(e)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/run-goal", response_model=RunGoalResponse)
def run_goal(req: RunGoalRequest) -> RunGoalResponse:
    headless_default = _env_bool("BROWSERUSE_HEADLESS", True)
    headless = headless_default if req.headless is None else bool(req.headless)

    model = req.model or os.environ.get("BROWSERUSE_MODEL", "gpt-5-nano")

    try:
        browser = _create_browser(headless=headless)
        _wait_for_browseruse_ready()

        agent = Agent(
            task=req.goal,
            llm=ChatOpenAI(model=model),
            browser=browser,
        )

        output = agent.run_sync()
        # Some versions return None; stringify to be safe
        return RunGoalResponse(ok=True, result=str(output))
    except Exception as e:  # noqa: BLE001 - surface error nicely over API
        return RunGoalResponse(ok=False, error=str(e))


@app.post("/runs", response_model=CreateRunResponse)
def create_run(req: RunGoalRequest) -> CreateRunResponse:
    run_id = str(uuid4())
    with _RUNS_LOCK:
        _RUNS[run_id] = {"status": "queued", "result": None, "error": None}

    t = Thread(target=_run_job, args=(run_id, req), daemon=True)
    t.start()
    return CreateRunResponse(run_id=run_id, status="queued")


@app.get("/runs/{run_id}", response_model=GetRunResponse)
def get_run(run_id: str) -> GetRunResponse:
    with _RUNS_LOCK:
        run = _RUNS.get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="run_not_found")
        return GetRunResponse(
            run_id=run_id,
            status=run.get("status", "unknown"),
            result=run.get("result"),
            error=run.get("error"),
        )


@app.post("/book-calendar", response_model=BookingResponse)
def book_calendar(req: BookingRequest) -> BookingResponse:
    """
    Endpoint pour réserver un créneau sur un calendrier donné.
    
    Args:
        req: Requête contenant l'URL du calendrier et les informations utilisateur
        
    Returns:
        BookingResponse: Résultat de la tentative de réservation
    """
    # Par défaut, afficher le navigateur (comme dans booker.py)
    headless_default = _env_bool("BROWSERUSE_HEADLESS", False)
    headless = headless_default if req.headless is None else bool(req.headless)
    
    # Construire le dictionnaire d'informations utilisateur depuis la requête
    user_info = {
        "nom": req.nom,
        "email": req.email,
        "telephone": req.telephone,
        "site_web": req.site_web or "",
        "societe": req.societe or "",
        "preference_creneau": req.preference_creneau,
        "type_rdv": req.type_rdv,
        "message": req.message or "",
    }
    
    try:
        # Charger un proxy aléatoire
        proxy_config = _load_random_proxy()
        
        # Créer le navigateur avec les mêmes paramètres que booker.py
        chrome_path = _resolve_chrome_path()
        browser = Browser(
            executable_path=chrome_path,
            headless=headless,
            devtools=True,  # Toujours activer devtools pour voir le navigateur
            enable_default_extensions=False,
            proxy=proxy_config,
            args=[
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-background-networking",
                "--disable-sync",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--window-size=960,1080",
            ],
            wait_for_network_idle_page_load_time=3,
            minimum_wait_page_load_time=1,
        )
        _wait_for_browseruse_ready()
        
        # Créer le prompt de réservation
        booking_task = _create_booking_prompt(req.calendar_url, user_info)
        
        # Créer l'agent avec le modèle de sortie
        agent = Agent(
            task=booking_task,
            llm=ChatOpenAI(model="gpt-4o-mini"),
            browser=browser,
            output_model_schema=BookingOutput,
        )
        
        # Exécuter la réservation
        result = agent.run_sync(max_steps=req.max_steps or 20)
        
        # Extraire le statut du résultat
        status = "ERREUR_RESERVATION"  # Valeur par défaut
        
        if hasattr(result, 'status'):
            status = result.status.value
        elif result:
            # Essayer d'extraire depuis le dernier élément de l'historique
            last_step = result[-1] if isinstance(result, list) else result
            if hasattr(last_step, 'status'):
                status = last_step.status.value
            elif hasattr(last_step, 'data') and isinstance(last_step.data, dict):
                status = last_step.data.get('status', 'ERREUR_RESERVATION')
            elif hasattr(last_step, 'result') and isinstance(last_step.result, dict):
                status = last_step.result.get('status', 'ERREUR_RESERVATION')
        
        # Nettoyer le navigateur
        try:
            browser.close()
        except:
            pass
        
        return BookingResponse(ok=True, status=status)
        
    except Exception as e:
        return BookingResponse(ok=False, error=str(e))


def main() -> None:
    try:
        import uvicorn  # noqa: WPS433
    except Exception as e:  # pragma: no cover
        print("[server] uvicorn non disponible, installez les dépendances (requirements.txt)", file=sys.stderr)
        raise e

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run("server:app", host=host, port=port, reload=_env_bool("UVICORN_RELOAD", False))


if __name__ == "__main__":
    main()


