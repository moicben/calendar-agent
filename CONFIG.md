# Configuration des informations de réservation

## 📝 Configuration

Les informations de réservation doivent être fournies dans l'appel API :

### Dans l'API (`server.py`)

Tous les champs sont requis dans le body de la requête :

```bash
curl -X POST "http://localhost:8080/book-calendar" \
  -H "Content-Type: application/json" \
  -d '{
    "calendar_url": "https://calendly.com/example/30min",
    "nom": "Votre Nom",
    "email": "votre@email.com",
    "telephone": "+33612345678",
    "site_web": "votre-site.com",
    "societe": "Votre Société",
    "preference_creneau": "Premier créneau disponible dès demain dans les 7 prochains jours",
    "type_rdv": "Visio-conférence Google Meet",
    "message": "Votre message personnalisé..."
  }'
```

### Dans le script `booker.py`

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

- Dans l'API, tous les champs sont requis dans le body de la requête
- Pour `booker.py`, modifiez directement les valeurs dans le code ligne 172-181
- Les champs `headless` et `max_steps` restent optionnels dans l'API

