# coding: utf-8
# Agent de prise de rendez-vous automatique
# Utilise les URLs de calendars/new pour réserver des créneaux
# Sauvegarde les URLs réservées dans calendars/booked

import os
import random
from typing import List, Optional, Dict
from browser_use import Agent, ChatOpenAI, Browser
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


def load_calendar_urls(file_path: str) -> List[str]:
    """Charge les URLs depuis un fichier de calendrier."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]
        return urls
    except FileNotFoundError:
        print(f"Fichier {file_path} non trouvé")
        return []


def load_proxies(file_path: str) -> List[Dict[str, str]]:
    """Charge les proxies depuis le fichier proxies."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            proxies = []
            for line in f.readlines():
                line = line.strip()
                if line and ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 4:
                        host, port, username, password = parts[0], parts[1], parts[2], parts[3]
                        proxies.append({
                            'host': host,
                            'port': port,
                            'username': username,
                            'password': password
                        })
        return proxies
    except FileNotFoundError:
        print(f"Fichier {file_path} non trouvé")
        return []


def get_random_proxy(proxies: List[Dict[str, str]], exclude_proxies: List[Dict[str, str]] = None) -> Optional[Dict[str, str]]:
    """Retourne un proxy aléatoire depuis la liste, en excluant ceux déjà utilisés."""
    if not proxies:
        return None
    
    if exclude_proxies is None:
        exclude_proxies = []
    
    # Filtrer les proxies déjà utilisés
    available_proxies = [p for p in proxies if p not in exclude_proxies]
    
    if not available_proxies:
        print("⚠️ Tous les proxies ont été testés, retour au début de la liste")
        return random.choice(proxies)
    
    return random.choice(available_proxies)


def save_booked_url(url: str, booked_file: str) -> None:
    """Sauvegarde une URL réservée dans le fichier booked."""
    try:
        with open(booked_file, 'a', encoding='utf-8') as f:
            f.write(f"{url}\n")
        print(f"URL réservée sauvegardée: {url}")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde: {e}")


def create_booking_prompt(url: str, user_info: dict) -> str:
    """Crée le prompt pour la réservation avec les informations utilisateur."""
    return f"""
Tu es un agent de prise de rendez-vous automatique. Ta mission est de réserver un créneau sur cette page de calendrier : {url}

INFORMATIONS DE RÉSERVATION :
- Nom : {user_info.get('nom', 'Non spécifié')}
- Email : {user_info.get('email', 'Non spécifié')}
- Téléphone : {user_info.get('telephone', 'Non spécifié')}
- Préférence de créneau : {user_info.get('preference_creneau', 'Premier créneau disponible')}
- Type de rendez-vous : {user_info.get('type_rdv', 'Appel découverte')}
- Message additionnel : {user_info.get('message', 'Appel pour discuter de collaboration')}

INSTRUCTIONS :
1. Va sur la page {url}
2. Trouve le premier créneau disponible qui correspond aux préférences
3. Remplis le formulaire avec les informations fournies
4. Confirme la réservation
5. Une fois la réservation confirmée, retourne l'URL complète de la page de confirmation ou de la page de calendrier

IMPORTANT : 
- Sois poli et professionnel
- Si aucun créneau n'est disponible, retourne "AUCUN_CRENEAU_DISPONIBLE"
- Si une erreur survient, retourne "ERREUR_RESERVATION"
- Attends la confirmation avant de considérer la réservation comme réussie
"""


def main(num_calendars: int = 1) -> None:
    """
    Fonction principale pour traiter les réservations de calendriers.
    
    Args:
        num_calendars (int): Nombre de calendriers à traiter (par défaut: 1)
    """
    # Chemins des fichiers
    new_calendars_file = "calendars/new"
    booked_calendars_file = "calendars/booked"
    proxies_file = "proxies"
    
    # Informations de réservation (à personnaliser selon vos besoins)
    user_info = {
        "nom": "Thibault Ressy",
        "email": "carbone.developpement@gmail.com", 
        "telephone": "+447446162797",
        "preference_creneau": "Premier créneau disponible cette semaine",
        "type_rdv": "Visioconférence",
        "message": "Bonjour, je souhaite réserver un créneau pour discuter d'une collaboration potentielle."
    }

    # Charger les URLs disponibles
    available_urls = load_calendar_urls(new_calendars_file)
    
    if not available_urls:
        print("Aucune URL de calendrier disponible dans calendars/new")
        return

    # Charger les proxies disponibles
    available_proxies = load_proxies(proxies_file)
    
    if not available_proxies:
        print("Aucun proxy disponible dans proxies")
        return

    print(f"URLs disponibles: {len(available_urls)}")
    print(f"Proxies disponibles: {len(available_proxies)}")
    print(f"Nombre de calendriers à traiter: {num_calendars}")
    
    # Limiter le nombre de calendriers à traiter
    urls_to_process = available_urls[:num_calendars]
    
    successful_bookings = 0
    failed_bookings = 0
    
    for i, selected_url in enumerate(urls_to_process, 1):
        print(f"\n--- Traitement {i}/{len(urls_to_process)} ---")
        print(f"Tentative de réservation sur: {selected_url}")

        # Liste des proxies déjà testés pour cette URL
        tested_proxies = []
        max_proxy_attempts = min(5, len(available_proxies))  # Maximum 5 tentatives ou tous les proxies
        booking_successful = False
        
        for proxy_attempt in range(max_proxy_attempts):
            # Sélectionner un proxy aléatoire pour ce calendrier
            selected_proxy = get_random_proxy(available_proxies, tested_proxies)
            print(f"Proxy utilisé (tentative {proxy_attempt + 1}/{max_proxy_attempts}): {selected_proxy['host']}:{selected_proxy['port']}")
            
            # Ajouter ce proxy à la liste des testés
            tested_proxies.append(selected_proxy)

            # Configuration Chrome depuis les variables d'environnement
            chrome_path = os.getenv("CHROME_PATH")

            browser = Browser(
                executable_path=chrome_path,
                headless=False,
                devtools=True,
                enable_default_extensions=False,
                # user_data_dir="../browseruse-profile",  # Temporairement désactivé
                proxy={
                    "server": f"http://{selected_proxy['host']}:{selected_proxy['port']}",
                    "username": selected_proxy['username'],
                    "password": selected_proxy['password']
                },
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
                wait_for_network_idle_page_load_time=3,  # Augmenté de 1 à 3
                minimum_wait_page_load_time=1,  # Augmenté de 0.5 à 1
            )

            # Créer le prompt de réservation
            booking_task = create_booking_prompt(selected_url, user_info)

            agent = Agent(
                task=booking_task,
                llm=ChatOpenAI(model="gpt-4o-mini"),  # Changé de gpt-5-nano à gpt-4o-mini
                browser=browser,
            )

            try:
                result = agent.run_sync()
                result_str = str(result).strip()
                
                print(f"Résultat de la réservation: {result_str}")
                
                # Vérifier si la réservation a réussi
                if result_str and result_str not in ["AUCUN_CRENEAU_DISPONIBLE", "ERREUR_RESERVATION"]:
                    # Sauvegarder l'URL réservée
                    save_booked_url(selected_url, booked_calendars_file)
                    print("✅ Réservation réussie!")
                    successful_bookings += 1
                    booking_successful = True
                    break  # Sortir de la boucle proxy
                else:
                    print("❌ Réservation échouée ou aucun créneau disponible")
                    if proxy_attempt < max_proxy_attempts - 1:
                        print("🔄 Tentative avec un autre proxy...")
                    
            except Exception as e:
                print(f"Erreur lors de l'exécution de l'agent: {e}")
                if proxy_attempt < max_proxy_attempts - 1:
                    print("🔄 Tentative avec un autre proxy...")
            finally:
                # Fermer proprement le browser
                try:
                    browser.close()
                    print("🧹 Browser fermé proprement")
                except:
                    pass
        
        # Si aucune tentative n'a réussi
        if not booking_successful:
            print("❌ Échec avec tous les proxies testés")
            failed_bookings += 1
    
    # Résumé final
    print(f"\n=== RÉSUMÉ ===")
    print(f"Réservations réussies: {successful_bookings}")
    print(f"Réservations échouées: {failed_bookings}")
    print(f"Total traité: {successful_bookings + failed_bookings}")


if __name__ == "__main__":
    import sys
    
    # Permettre de spécifier le nombre de calendriers via argument en ligne de commande
    num_calendars = 1
    if len(sys.argv) > 1:
        try:
            num_calendars = int(sys.argv[1])
            if num_calendars <= 0:
                print("Le nombre de calendriers doit être positif")
                sys.exit(1)
        except ValueError:
            print("Veuillez fournir un nombre valide")
            print("Usage: python booker.py [nombre_de_calendriers]")
            sys.exit(1)
    
    main(num_calendars)