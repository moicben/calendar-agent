import os
from browser_use import Agent, ChatOpenAI, Browser
from dotenv import load_dotenv
from pydantic import BaseModel
from enum import Enum

load_dotenv()

linux_path = "/usr/bin/google-chrome"
calendar_url = "https://calendly.com/designetfonctionnel/j-ai-une-question"

user_info = {
    'nom': 'Test User',
    'email': 'test@example.com',
    'telephone': '+33123456789',
    'message': 'Bonjour, je souhaite prendre rendez-vous pour une consultation.'
}

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

class BookingStatus(str, Enum):
    SUCCESS_RESERVATION = "SUCCESS_RESERVATION"
    AUCUN_CRENEAU_DISPONIBLE = "AUCUN_CRENEAU_DISPONIBLE"
    ERREUR_RESERVATION = "ERREUR_RESERVATION"

class BookingOutput(BaseModel):
    status: BookingStatus

if __name__ == "__main__":
    try:
        browser = Browser(
            executable_path=linux_path,
            headless=False,
            args=browser_args,
        )
        
        task = f"""Va sur {calendar_url} et réserve un rendez-vous Calendly avec ces informations:
- Nom: {user_info.get('nom')}
- Email: {user_info.get('email')}
- Téléphone: {user_info.get('telephone')}
- Message: {user_info.get('message')}

Remplis le formulaire et confirme la réservation. Si aucun créneau disponible, indique-le."""
        
        agent = Agent(
            task=task,
            llm=ChatOpenAI(model="gpt-4o-mini"),
            browser=browser,
            output_model_schema=BookingOutput,
        )
        
        result = agent.run_sync(max_steps=20)
        print(result)
        
        browser.close()
        
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
