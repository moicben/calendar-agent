# coding: utf-8
# Agent de prise de rendez-vous automatique
# Utilise les URLs de calendars/new pour réserver des créneaux
# Sauvegarde les URLs réservées dans calendars/booked

import os
import random
from typing import List, Optional
from browser_use import Agent, ChatOpenAI, Browser
from browser_use.browser import ProxySettings
from dotenv import load_dotenv
from pydantic import BaseModel
from enum import Enum

# Charger les variables d'environnement
load_dotenv()


class BookingStatus(str, Enum):
    SUCCESS_RESERVATION = "SUCCESS_RESERVATION"
    AUCUN_CRENEAU_DISPONIBLE = "AUCUN_CRENEAU_DISPONIBLE"
    ERREUR_RESERVATION = "ERREUR_RESERVATION"


class BookingOutput(BaseModel):
    status: BookingStatus


def load_calendar_urls(file_path: str) -> List[str]:
    """Charge les URLs depuis un fichier de calendrier."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]
        return urls
    except FileNotFoundError:
        print(f"Fichier {file_path} non trouvé")
        return []


def save_booked_url(url: str, booked_file: str) -> None:
    """Sauvegarde une URL réservée dans le fichier booked."""
    try:
        with open(booked_file, 'a', encoding='utf-8') as f:
            f.write(f"{url}\n")
        print(f"URL réservée sauvegardée: {url}")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde: {e}")


def remove_url_from_new(url: str, new_file: str) -> None:
    """Retire une URL du fichier new après traitement."""
    try:
        with open(new_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]
        
        # Retirer l'URL traitée
        if url in urls:
            urls.remove(url)
            
            # Réécrire le fichier sans l'URL traitée
            with open(new_file, 'w', encoding='utf-8') as f:
                for remaining_url in urls:
                    f.write(f"{remaining_url}\n")
            print(f"URL retirée de calendars/new: {url}")
        else:
            print(f"URL non trouvée dans calendars/new: {url}")
    except Exception as e:
        print(f"Erreur lors de la suppression de l'URL: {e}")


def create_booking_prompt(url: str, user_info: dict) -> str:
    """Crée le prompt pour la réservation avec les informations utilisateur."""
    return f"""
Tu es un agent de prise de rendez-vous automatique. Ta mission est de réserver un créneau sur cette page de calendrier : {url}

INFORMATIONS DE RÉSERVATION :
- Nom : {user_info.get('nom')}
- Email : {user_info.get('email')}
- Téléphone : {user_info.get('telephone')}
- Préférence de créneau : {user_info.get('preference_creneau')}
- Type de rendez-vous : {user_info.get('type_rdv')}
- Message additionnel : {user_info.get('message')}

INSTRUCTIONS :
1. Va sur la page {url}
2. Vérifie si le calendrier est disponible et s'il y a des créneaux sur les 5 prochains jours
3. CONTRÔLES D'ARRÊT IMMÉDIAT (ne pas continuer si l'une des conditions est vraie) :
   3.1. Si la page affiche « Page not found », « Not Found », « page introuvable », un code 404, ou un gabarit d'erreur → retourne UNIQUEMENT "ERREUR_RESERVATION" et ARRÊTE IMMÉDIATEMENT.
   3.2. S'il n'y a AUCUNE disponibilité (aucun créneau affiché sur les 5 prochains jours ou message d'indisponibilité explicite) → retourne UNIQUEMENT "AUCUN_CRENEAU_DISPONIBLE" et ARRÊTE IMMÉDIATEMENT.
4. Si aucune condition d'arrêt n'est déclenchée, trouve le premier créneau disponible qui correspond aux préférences (sans changer le fuseau horaire)
5. Remplis le formulaire avec les informations fournies
6. Confirme la réservation
7. Une fois la réservation confirmée, retourne UNIQUEMENT "SUCCESS_RESERVATION"

CONTRAINTES :
•	Ne change pas le fuseau horaire du calendrier fait seulement la conversion du décalage horaires entre le fuseau du calendrier et celui d'Europe Central (Paris) 
•	N'attends pas de confirmation explicite avant de valider une réservation, tu es 100% autonome.
•	Tu DOIS t'arrêter immédiatement dès qu'une des conditions d'arrêt du point 3 est détectée.
•	Retourne UNIQUEMENT l'une de ces valeurs finales: "SUCCESS_RESERVATION", "AUCUN_CRENEAU_DISPONIBLE", "ERREUR_RESERVATION".
•	N'essaie pas de contourner une indisponibilité ou une erreur par des navigations ou des rafraîchissements supplémentaires.
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
    
    # Informations de réservation (à personnaliser selon vos besoins)
    user_info = {
        "nom": "Thibault Ressy",
        "email": "carbone.developpement@gmail.com", 
        "telephone": "+447446162797",
        "preference_creneau": "Premier créneau disponible dans les 5 prochains jours",
        "type_rdv": "Visioconférence",
        "message": "Dans le cadre de la création de notre nouveau site, et l’update de nos réseaux. Je cherche un(e) expert(e) fiable pour m’accompagner sur la création et mise en forme de contenus. TR-ARCHITECTE.FR\nMerci, Thibault Ressy"
    }

    # Charger les URLs disponibles
    available_urls = load_calendar_urls(new_calendars_file)
    
    if not available_urls:
        print("Aucune URL de calendrier disponible dans calendars/new")
        return

    print(f"URLs disponibles: {len(available_urls)}")
    print(f"Nombre de calendriers à traiter: {num_calendars}")
    
    # Limiter le nombre de calendriers à traiter
    urls_to_process = available_urls[:num_calendars]
    
    successful_bookings = 0
    failed_bookings = 0
    
    for i, selected_url in enumerate(urls_to_process, 1):
        print(f"\n--- Traitement {i}/{len(urls_to_process)} ---")
        print(f"Tentative de réservation sur: {selected_url}")

        # Configuration Chrome depuis les variables d'environnement
        chrome_path = os.getenv("CHROME_PATH")

        # Configuration du proxy HTTPS
        proxy_config = ProxySettings(
            server='https://geo.g-w.info:10443',
            username='p8lTvBbFDHV3PtLu',
            password='dajXL25Is4I91Cnm',
            bypass='localhost,127.0.0.1'
        )

        browser = Browser(
            executable_path=chrome_path,
            headless=False,
            devtools=True,
            enable_default_extensions=False,
            proxy=proxy_config,
            # user_data_dir="../browseruse-profile",  # Temporairement désactivé
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
                "--window-size=960,1080",
            ],
            wait_for_network_idle_page_load_time=3,  # Augmenté de 1 à 3
            minimum_wait_page_load_time=1,  # Augmenté de 0.5 à 1
        )

        # Créer le prompt de réservation
        booking_task = create_booking_prompt(selected_url, user_info)

        agent = Agent(
            task=booking_task,
            llm=ChatOpenAI(model="gpt-4o-mini"),
            browser=browser,
            max_steps=16,
            output_model_schema=BookingOutput,
        )

        try:
            result = agent.run_sync()
            status = result.status.value
            
            print(f"Résultat de la réservation: {status}")
            
            # Déplacer l'URL vers booked dans tous les cas
            save_booked_url(selected_url, booked_calendars_file)
            # Retirer l'URL de calendars/new
            remove_url_from_new(selected_url, new_calendars_file)
            
            # Vérifier si la réservation a réussi
            if status == "SUCCESS_RESERVATION":
                print("✅ Réservation réussie!")
                successful_bookings += 1
            else:
                print("❌ Réservation échouée ou aucun créneau disponible")
                failed_bookings += 1
                
        except Exception as e:
            print(f"Erreur lors de l'exécution de l'agent: {e}")
            # Déplacer l'URL vers booked même en cas d'erreur
            save_booked_url(selected_url, booked_calendars_file)
            # Retirer l'URL de calendars/new même en cas d'erreur
            remove_url_from_new(selected_url, new_calendars_file)
            failed_bookings += 1
        finally:
            # Fermer proprement le browser
            try:
                browser.close()
                print("🧹 Browser fermé proprement")
            except:
                pass
    
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