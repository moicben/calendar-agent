# Configuration des informations de réservation

## 📝 Configuration

Les informations de réservation peuvent être configurées de deux façons :

### 1. Dans l'API (`server.py`)

Les valeurs par défaut sont définies dans `BookingRequest` et peuvent être surchargées dans l'appel API :

```bash
curl -X POST "http://localhost:8080/book-calendar" \
  -H "Content-Type: application/json" \
  -d '{
    "calendar_url": "https://calendly.com/example/30min",
    "nom": "Votre Nom",  # Optionnel : surcharge la valeur par défaut
    "email": "votre@email.com"  # Optionnel : surcharge la valeur par défaut
  }'
```

### 2. Dans le script `booker.py`

Les valeurs sont définies directement dans le code. Modifiez `agents/booker.py` :

```python
user_info = {
    "nom": "Votre Nom",
    "email": "votre@email.com",
    "telephone": "+33612345678",
    # ... etc
}
```

Puis exécutez :
```bash
python agents/booker.py 1
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

## ✨ Notes

- Les valeurs par défaut sont définies dans `server.py` pour l'API
- Pour `booker.py`, modifiez directement les valeurs dans le code
- Dans l'API, tous les champs sauf `calendar_url` sont optionnels et ont des valeurs par défaut

