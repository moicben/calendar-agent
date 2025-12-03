#!/usr/bin/env python3
"""
Script Python utilisant Browseruse pour analyser une page déjà chargée
dans un navigateur via CDP (Chrome DevTools Protocol).
"""

import sys
import logging
from dotenv import load_dotenv
from browser_use import Agent, ChatOpenAI, Browser

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)

load_dotenv()

def analyze_page_with_browseruse():
    """Analyse la page déjà chargée dans le navigateur via Browseruse."""
    try:
        print("[Browseruse] Connexion au navigateur via CDP...")
        browser = Browser(cdp_url="http://localhost:9222")
        
        print("[Browseruse] Analyse de la page...")
        task = """
        La page est DÉJÀ CHARGÉE. NE PAS naviguer.
        Utiliser "read" pour lire le contenu de la page actuelle.
        Afficher un récap écrit avec: titre, contenu principal, géolocalisation, éléments interactifs, résumé.
        """
        
        agent = Agent(
            task=task,
            llm=ChatOpenAI(model="gpt-4o-mini"),
            browser=browser,
        )
        
        result = agent.run_sync(max_steps=15)
        
        try:
            browser.close()
        except:
            pass
        
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"[Browseruse] Erreur: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    analyze_page_with_browseruse()