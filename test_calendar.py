#!/usr/bin/env python3
"""
Script de test simple pour naviguer vers Google Calendar avec Playwright
"""

import asyncio
from playwright.async_api import async_playwright

async def test_calendar_navigation():
    """Test de navigation vers Google Calendar"""
    
    async with async_playwright() as p:
        # Lancer le navigateur
        browser = await p.chromium.launch(headless=False)  # headless=True pour mode sans interface
        page = await browser.new_page()
        
        try:
            # URL de Google Calendar
            calendar_url = "https://calendar.app.google/8MHoQbiDt5iXxgrP6"
            
            print(f"Navigation vers: {calendar_url}")
            
            # Naviguer vers la page
            await page.goto(calendar_url)
            
            # Attendre que la page se charge
            await page.wait_for_load_state('networkidle')
            
            # Prendre une capture d'écran
            await page.screenshot(path="calendar_screenshot.png")
            print("Capture d'écran sauvegardée: calendar_screenshot.png")
            
            # Attendre quelques secondes pour voir la page
            await asyncio.sleep(3)
            
            # Obtenir le titre de la page
            title = await page.title()
            print(f"Titre de la page: {title}")
            
            # Obtenir l'URL actuelle
            current_url = page.url
            print(f"URL actuelle: {current_url}")
            
        except Exception as e:
            print(f"Erreur lors de la navigation: {e}")
            
        finally:
            # Fermer le navigateur
            await browser.close()

if __name__ == "__main__":
    print("Démarrage du test de navigation Google Calendar...")
    asyncio.run(test_calendar_navigation())
    print("Test terminé!")
