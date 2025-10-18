#!/usr/bin/env python3
"""
Script d'installation pour Playwright
"""

import subprocess
import sys

def install_playwright():
    """Installe Playwright et ses navigateurs"""
    try:
        print("Installation de Playwright...")
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
        
        print("Installation des navigateurs Playwright...")
        subprocess.run([sys.executable, "-m", "playwright", "install"], check=True)
        
        print("Playwright installé avec succès!")
        
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'installation: {e}")
        return False
    
    return True

if __name__ == "__main__":
    install_playwright()
