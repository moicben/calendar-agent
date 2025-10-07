#!/usr/bin/env python3
# coding: utf-8
"""
Script de test pour vérifier le lancement de Chrome
Navigue vers christopeit-sport.fr et attend 30 secondes
"""

import os
import sys
import time
import json
import tempfile
import os.path
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def build_proxy_auth_extension(host: str, port: int, username: str, password: str, scheme: str = "https") -> str:
    """Crée une extension Chrome MV3 (non zippée) qui configure le proxy + auth.
    Retourne le chemin du dossier de l'extension à passer à --load-extension.
    """
    manifest = {
        "manifest_version": 3,
        "name": "Proxy Auth Helper",
        "version": "1.0",
        "permissions": [
            "proxy",
            "storage",
            "webRequest",
            "webRequestBlocking",
            "webRequestAuthProvider"
        ],
        "host_permissions": ["<all_urls>"],
        "background": {"service_worker": "background.js"}
    }

    background_js = f"""
async function applyProxy() {{
  try {{
    await chrome.proxy.settings.set({{
      value: {{
        mode: "fixed_servers",
        rules: {{ singleProxy: {{ scheme: "{scheme}", host: "{host}", port: {port} }} }}
      }},
      scope: "regular"
    }});
    console.log('Proxy settings applied');
  }} catch (e) {{
    console.error('Failed to apply proxy', e);
  }}
}}

applyProxy();
chrome.runtime.onStartup.addListener(applyProxy);
chrome.runtime.onInstalled.addListener(applyProxy);

chrome.webRequest.onAuthRequired.addListener(
  (details, callback) => callback({{ authCredentials: {{ username: "{username}", password: "{password}" }} }}),
  {{ urls: ["<all_urls>"] }},
  ["blocking"]
);
"""

    ext_dir = tempfile.mkdtemp(prefix="proxy_ext_")
    with open(os.path.join(ext_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f)
    with open(os.path.join(ext_dir, "background.js"), "w", encoding="utf-8") as f:
        f.write(background_js)
    return ext_dir

def get_chrome_path():
    """Récupère le chemin Chrome depuis CHROME_PATH."""
    chrome_path = os.getenv("CHROME_PATH")
    
    print("🔍 Vérification de CHROME_PATH...")
    
    if not chrome_path:
        print("❌ CHROME_PATH non définie dans .env")
        print("💡 Ajoutez CHROME_PATH=/chemin/vers/chrome dans votre fichier .env")
        return None
    
    if not os.path.exists(chrome_path):
        print(f"❌ Chrome non trouvé à: {chrome_path}")
        print("💡 Vérifiez que le chemin dans CHROME_PATH est correct")
        return None
    
    print(f"✅ Chrome trouvé: {chrome_path}")
    return chrome_path

def launch_chrome_with_proxy():
    """Lance Chrome avec configuration proxy."""
    print(f"\n🚀 Lancement Chrome...")
    
    try:
        # Configuration Chrome
        chrome_options = Options()
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-sync")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        
        chrome_options.add_argument("--proxy-bypass-list=<-loopback>")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--disable-quic")
        chrome_options.add_argument("--dns-prefetch-disable")
        chrome_options.add_argument("--disable-async-dns")
        # Forcer WebRTC via proxy (évite les fuites d'IP locales)
        chrome_options.add_argument("--force-webrtc-ip-handling-policy=disable_non_proxied_udp")
        chrome_options.add_argument("--webrtc-ip-handling-policy=disable_non_proxied_udp")
        chrome_options.add_argument("--enable-features=WebRtcHideLocalIpsWithMdns")

        # Extension d'authentification proxy
        proxy_zip = build_proxy_auth_extension(
            host="geo.g-w.info",
            port=10443,
            username="p8lTvBbFDHV3PtLu",
            password="dajXL25Is4I91Cnm",
            scheme="https"
        )
        chrome_options.add_argument(f"--load-extension={proxy_zip}")
        
        print("📋 Configuration Chrome appliquée...")
        
        # Lancer Chrome
        print("🔧 Lancement du driver Chrome...")
        driver = webdriver.Chrome(options=chrome_options)
        
        print("✅ Chrome lancé avec succès")
        print(f"📄 URL actuelle: {driver.current_url}")
        return driver
        
    except Exception as e:
        print(f"❌ Erreur lors du lancement de Chrome: {e}")
        print(f"🔍 Type d'erreur: {type(e).__name__}")
        return None

def navigate_and_wait(driver):
    """Navigue vers mylocation.org, vérifie le pays et attend 30 secondes."""
    print("\n🌐 Navigation vers mylocation.org...")
    
    try:
        # Aller sur le site
        print("🔗 Chargement de https://www.mylocation.org...")
        driver.get("https://www.mylocation.org")
        
        print("⏳ Attente de 8 secondes pour le chargement...")
        time.sleep(8)
        
        current_url = driver.current_url
        page_title = driver.title
        print(f"✅ Navigation réussie")
        print(f"📄 URL actuelle: {current_url}")
        print(f"📝 Titre de la page: {page_title}")

        # Essayer de lire le pays depuis la page
        country_text = None
        try:
            country_text = driver.execute_script(
                "const el = document.querySelector('#mycountry, .country, [data-country]'); return el ? (el.innerText || el.textContent || el.getAttribute('data-country')) : '';"
            )
        except Exception:
            pass
        if country_text:
            print(f"📍 Pays détecté: {country_text.strip()}")
        else:
            print("⚠️ Impossible de lire le pays depuis le DOM")
        
        # Vérifier via API IP (ipapi)
        print("🔎 Verification pays via https://ipapi.co/json/ ...")
        try:
            js = """
const done = arguments[0];
fetch('https://ipapi.co/json/')
  .then(r => r.json())
  .then(d => done(JSON.stringify(d)))
  .catch(e => done(JSON.stringify({error: String(e)})));
"""
            raw = driver.execute_async_script(js)
            data = json.loads(raw) if isinstance(raw, str) else raw
            if isinstance(data, dict):
                country_name = data.get('country_name') or data.get('country') or ''
                ip_addr = data.get('ip') or ''
                print(f"🌍 IP détectée: {ip_addr}")
                print(f"📍 Pays API: {country_name}")
                if isinstance(country_name, str) and country_name.strip().lower() in ("france", "fr"):
                    print("✅ Vérification: le pays est France")
                else:
                    print("⚠️ Vérification: le pays n'est pas France")
            else:
                print(f"⚠️ Réponse API inattendue: {data}")
        except Exception as api_e:
            print(f"⚠️ Échec vérification API: {api_e}")

        # Attendre 30 secondes pour inspection manuelle
        print("⏳ Attente de 30 secondes...")
        time.sleep(30)
        print("✅ Attente terminée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la navigation: {e}")
        print(f"🔍 Type d'erreur: {type(e).__name__}")
        return False

def main():
    """Fonction principale de test."""
    print("🧪 Test Chrome avec navigation vers christopeit-sport.fr")
    print("=" * 60)
    
    try:
        # Récupérer le chemin Chrome
        print("🔍 Étape 1: Récupération du chemin Chrome...")
        chrome_path = get_chrome_path()
        if not chrome_path:
            print("❌ Échec de récupération du chemin Chrome")
            sys.exit(1)
        
        # Lancer Chrome avec proxy
        print("🚀 Étape 2: Lancement de Chrome...")
        driver = launch_chrome_with_proxy()
        if not driver:
            print("❌ Échec du lancement de Chrome")
            sys.exit(1)
        
        # Naviguer et attendre
        print("🌐 Étape 3: Navigation vers le site...")
        nav_success = navigate_and_wait(driver)
        if not nav_success:
            print("⚠️ Navigation échouée")
        
        # Nettoyage
        print("🧹 Étape 4: Nettoyage...")
        try:
            driver.quit()
            print("✅ Chrome fermé proprement")
        except Exception as e:
            print(f"⚠️ Erreur lors de la fermeture: {e}")
        
        print("\n" + "=" * 60)
        print("✅ Test terminé!")
        print("🌐 Proxy utilisé: geo.g-w.info:10443")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        print(f"🔍 Type d'erreur: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
