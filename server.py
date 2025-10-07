import os
import sys
import time
from typing import Optional, Any

from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Runtime deps from browser-use
from browser_use import Agent, ChatOpenAI, Browser
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


def _create_browser(headless: bool) -> Browser:
    chrome_path = _resolve_chrome_path()
    # user_data_dir = os.environ.get("BROWSERUSE_USER_DATA_DIR", "./browseruse-profile")
    devtools_enabled = _env_bool("BROWSERUSE_DEVTOOLS", not headless)

    return Browser(
        executable_path=chrome_path,
        headless=headless,
        devtools=devtools_enabled,
        #user_data_dir=user_data_dir,
        enable_default_extensions=False,
        args=[
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-networking",
            "--disable-sync",
        ],
        wait_for_network_idle_page_load_time=0.5,
        minimum_wait_page_load_time=0.25,
    )


def _wait_for_browseruse_ready() -> None:
    # Attente simple et configurable pour laisser BrowserUse initialiser ses composants
    delay_s = _env_float("BROWSERUSE_STARTUP_DELAY_S", 1.5)
    if delay_s > 0:
        time.sleep(delay_s)


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


