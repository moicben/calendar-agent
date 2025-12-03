# Se rendre sur mylocation.org avec le navigateur playwright et faire une capture d'écran de la page

import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://mylocation.org")
    page.screenshot(path="screenshot.png")
    browser.close()
