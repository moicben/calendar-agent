# Calendar Agent - Guide d'utilisation

## Installation

1. Installer les dépendances :
```bash
pip install -r requirements.txt
```

2. Installer Playwright et ses navigateurs :
```bash
python setup_playwright.py
```

## Utilisation du serveur API

### Démarrer le serveur

```bash
python server.py
```

Le serveur démarre sur `http://0.0.0.0:8080` par défaut.

### Endpoint de réservation de calendrier

#### POST `/book-calendar`

Réserve automatiquement un créneau sur un calendrier donné.

**Exemple de requête minimale (cURL) :**

```bash
curl -X POST "http://localhost:8080/book-calendar" \
  -H "Content-Type: application/json" \
  -d '{
    "calendar_url": "https://calendly.com/example/30min"
  }'
```

**Exemple de requête complète (cURL) :**

```bash
curl -X POST "http://localhost:8080/book-calendar" \
  -H "Content-Type: application/json" \
  -d '{
    "calendar_url": "https://calendly.com/example/30min",
    "nom": "Cyril Moriou",
    "email": "lexpertisedunotaire@gmail.com",
    "telephone": "+33774334897",
    "site_web": "etude-lyon-bugeaud.notaires.fr",
    "societe": "Étude Lyon Bugeaud",
    "preference_creneau": "Premier créneau disponible dès demain dans les 7 prochains jours",
    "type_rdv": "Visio-conférence Google Meet",
    "message": "Dans le cadre du (re)lancement de notre stratégie de comm...",
    "headless": false,
    "max_steps": 20
  }'
```

**Exemple de requête minimale (Python) :**

```python
import requests

response = requests.post(
    "http://localhost:8080/book-calendar",
    json={
        "calendar_url": "https://calendly.com/example/30min"
    }
)

print(response.json())
```

**Exemple de requête complète (Python) :**

```python
import requests

response = requests.post(
    "http://localhost:8080/book-calendar",
    json={
        "calendar_url": "https://calendly.com/example/30min",
        "nom": "Cyril Moriou",
        "email": "lexpertisedunotaire@gmail.com",
        "telephone": "+33774334897",
        "site_web": "etude-lyon-bugeaud.notaires.fr",
        "societe": "Étude Lyon Bugeaud",
        "preference_creneau": "Premier créneau disponible dès demain dans les 7 prochains jours",
        "type_rdv": "Visio-conférence Google Meet",
        "message": "Dans le cadre du (re)lancement de notre stratégie de comm...",
        "headless": False,
        "max_steps": 20
    }
)

print(response.json())
```

**Réponse :**

```json
{
  "ok": true,
  "status": "SUCCESS_RESERVATION",
  "error": null
}
```

**Statuts possibles :**
- `SUCCESS_RESERVATION` : Réservation réussie
- `AUCUN_CRENEAU_DISPONIBLE` : Aucun créneau disponible
- `ERREUR_RESERVATION` : Erreur lors de la réservation

**Paramètres :**
- `calendar_url` (requis) : URL du calendrier à utiliser
- `nom` (optionnel) : Nom complet (par défaut: "Cyril Moriou")
- `email` (optionnel) : Adresse email (par défaut: "lexpertisedunotaire@gmail.com")
- `telephone` (optionnel) : Numéro de téléphone (par défaut: "+33774334897")
- `site_web` (optionnel) : Site web (par défaut: "etude-lyon-bugeaud.notaires.fr")
- `societe` (optionnel) : Nom de la société (par défaut: "Étude Lyon Bugeaud")
- `preference_creneau` (optionnel) : Préférence de créneau (par défaut: "Premier créneau disponible dès demain dans les 7 prochains jours")
- `type_rdv` (optionnel) : Type de rendez-vous (par défaut: "Visio-conférence Google Meet")
- `message` (optionnel) : Message personnalisé (par défaut: message standard)
- `headless` (optionnel) : Mode headless (par défaut: False - navigateur visible)
- `max_steps` (optionnel) : Nombre maximum d'étapes (par défaut: 20)

## Utilisation en ligne de commande

### Script de réservation direct

```bash
python agents/booker.py 1
```

Réserve 1 calendrier depuis `calendars/proceed.txt` et sauvegarde dans `calendars/booked`.

## Fonctionnalités

- Navigation automatique vers les calendriers (Calendly, cal.com, Google Calendar, etc.)
- Remplissage automatique des formulaires
- Support des proxies (fichier `proxies`)
- Sauvegarde des URLs réservées
- Gestion des erreurs et retry automatique
