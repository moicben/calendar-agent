# Configuration des informations de réservation

## 📝 Fichier de configuration centralisé

Les informations de réservation sont centralisées dans **`config.py`**.

## 🎯 Modification des valeurs par défaut

Ouvrez `config.py` et modifiez directement les valeurs :

```python
def get_booking_defaults():
    return {
        "nom": "Votre Nom",
        "email": "votre@email.com",
        "telephone": "+33612345678",
        "site_web": "votre-site.com",
        "societe": "Votre Société",
        "preference_creneau": "Premier créneau disponible dès demain dans les 7 prochains jours",
        "type_rdv": "Visio-conférence Google Meet",
        "message": "Votre message personnalisé...",
    }
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
✅ **Simplicité** : Modification directe dans un seul fichier  
✅ **Compatibilité** : Fonctionne avec `booker.py` et l'API  
✅ **Facilité** : Pas besoin de configuration complexe

