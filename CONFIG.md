# Configuration des informations de réservation

## 📝 Fichier de configuration centralisé

Les informations de réservation sont maintenant centralisées dans **`config.py`**.

## 🎯 Modification des valeurs par défaut

### Option 1 : Modifier directement `config.py`

Ouvrez `config.py` et modifiez les valeurs par défaut :

```python
def get_booking_defaults():
    return {
        "nom": "Votre Nom",
        "email": "votre@email.com",
        # ... etc
    }
```

### Option 2 : Utiliser des variables d'environnement (recommandé)

Créez un fichier `.env` à la racine du projet :

```bash
# Configuration de réservation
BOOKING_NOM=Votre Nom
BOOKING_EMAIL=votre@email.com
BOOKING_TELEPHONE=+33612345678
BOOKING_SITE_WEB=votre-site.com
BOOKING_SOCIETE=Votre Société
BOOKING_PREFERENCE_CRENEAU=Premier créneau disponible dès demain dans les 7 prochains jours
BOOKING_TYPE_RDV=Visio-conférence Google Meet
BOOKING_MESSAGE=Votre message personnalisé...
```

## 🔄 Utilisation

### Dans le script `booker.py`

Les valeurs sont automatiquement chargées depuis `config.py` :

```bash
python agents/booker.py 1
```

### Dans l'API (`server.py`)

Les valeurs par défaut sont utilisées automatiquement. Vous pouvez les surcharger dans votre requête :

```bash
curl -X POST "http://localhost:8080/book-calendar" \
  -H "Content-Type: application/json" \
  -d '{
    "calendar_url": "https://calendly.com/example/30min",
    "nom": "Nom Personnalisé",  # Optionnel : surcharge la valeur par défaut
    "email": "email@perso.com"  # Optionnel : surcharge la valeur par défaut
  }'
```

## 📋 Champs configurables

- `nom` : Nom complet
- `email` : Adresse email
- `telephone` : Numéro de téléphone
- `site_web` : Site web
- `societe` : Nom de la société
- `preference_creneau` : Préférence de créneau
- `type_rdv` : Type de rendez-vous
- `message` : Message personnalisé

## ✨ Avantages

✅ **Centralisation** : Une seule source de vérité  
✅ **Flexibilité** : Variables d'environnement ou fichier Python  
✅ **Compatibilité** : Fonctionne avec `booker.py` et l'API  
✅ **Facilité** : Modification simple et rapide

