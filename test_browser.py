#!/usr/bin/env python3
# coding: utf-8
"""
Script de test pour vérifier le lancement de Chrome sur Ubuntu VM
Teste la configuration browser-use avec /usr/bin/google-chrome
"""

import os
import sys
import time
from browser_use import Browser, Agent, ChatOpenAI
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def test_chrome_installation():
    """Teste si Chrome est installé et accessible."""
    chrome_paths = [
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable", 
        "/usr/bin/chromium-browser",
        "/snap/bin/chromium"
    ]
    
    print("🔍 Vérification de l'installation Chrome...")
    
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✅ Chrome trouvé: {path}")
            return path
    
    print("❌ Chrome non trouvé dans les chemins standards")
    print("💡 Installez Chrome avec:")
    print("   wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -")
    print("   echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | sudo tee /etc/apt/sources.list.d/google-chrome.list")
    print("   sudo apt update && sudo apt install google-chrome-stable")
    return None

def test_browser_launch(chrome_path):
    """Teste le lancement du navigateur."""
    print(f"\n🚀 Test de lancement Chrome: {chrome_path}")
    
    try:
        browser = Browser(
            executable_path=chrome_path,
            headless=False,  # Mode graphique pour voir le navigateur
            devtools=True,
            enable_default_extensions=False,
            args=[
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-background-networking",
                "--disable-sync",
                "--disable-dev-shm-usage",  # Important pour VM
                "--no-sandbox",  # Important pour VM
                "--disable-gpu",  # Important pour VM
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--window-size=1920,1080",
            ],
            wait_for_network_idle_page_load_time=3,
            minimum_wait_page_load_time=1,
        )
        
        print("✅ Browser configuré avec succès")
        return browser
        
    except Exception as e:
        print(f"❌ Erreur lors de la configuration du browser: {e}")
        return None

def test_page_navigation(browser):
    """Teste la navigation vers une page simple."""
    print("\n🌐 Test de navigation...")
    
    try:
        # Navigation vers une page simple
        browser.go_to("https://httpbin.org/get")
        time.sleep(2)
        
        # Vérifier que la page s'est chargée
        page_content = browser.get_page_content()
        
        if "httpbin" in page_content.lower():
            print("✅ Navigation réussie")
            return True
        else:
            print("❌ Page non chargée correctement")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la navigation: {e}")
        return False

def test_agent_creation():
    """Teste la création d'un agent simple."""
    print("\n🤖 Test de création d'agent...")
    
    try:
        # Vérifier la clé API OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY non définie dans .env")
            return False
        
        print("✅ Clé API OpenAI trouvée")
        
        # Créer un agent simple
        agent = Agent(
            task="Va sur https://httpbin.org/get et retourne le statut de la page",
            llm=ChatOpenAI(model="gpt-4o-mini"),  # Modèle valide
            browser=None,  # Pas de browser pour ce test
        )
        
        print("✅ Agent créé avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'agent: {e}")
        return False

def main():
    """Fonction principale de test."""
    print("🧪 Test de configuration browser-use pour Ubuntu VM")
    print("=" * 60)
    
    # Test 1: Installation Chrome
    chrome_path = test_chrome_installation()
    if not chrome_path:
        sys.exit(1)
    
    # Test 2: Lancement Browser
    browser = test_browser_launch(chrome_path)
    if not browser:
        sys.exit(1)
    
    # Test 3: Navigation
    nav_success = test_page_navigation(browser)
    if not nav_success:
        print("⚠️ Navigation échouée, mais browser fonctionne")
    
    # Test 4: Création Agent
    agent_success = test_agent_creation()
    if not agent_success:
        print("⚠️ Agent non testé, vérifiez OPENAI_API_KEY")
    
    # Nettoyage
    try:
        browser.close()
        print("\n🧹 Browser fermé proprement")
    except:
        pass
    
    print("\n" + "=" * 60)
    print("✅ Tests terminés!")
    print(f"💡 Utilisez ce chemin Chrome dans votre .env: CHROME_PATH={chrome_path}")
    print("💡 Modèle recommandé: gpt-4o-mini")

if __name__ == "__main__":
    main()
