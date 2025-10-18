# Test Google Calendar avec Playwright

## Installation

1. Installer les dépendances :
```bash
pip install -r requirements.txt
```

2. Installer Playwright et ses navigateurs :
```bash
python setup_playwright.py
```

## Utilisation

Exécuter le script de test :
```bash
python test_calendar.py
```

## Fonctionnalités du script

- Navigation vers l'URL Google Calendar spécifiée
- Capture d'écran automatique
- Affichage du titre et de l'URL de la page
- Mode visible (headless=False) pour voir le navigateur

## Configuration

Pour exécuter en mode invisible (sans interface), modifier dans `test_calendar.py` :
```python
browser = await p.chromium.launch(headless=True)
```
