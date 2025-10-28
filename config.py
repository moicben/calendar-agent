# coding: utf-8
"""
Configuration centralisée pour les informations de réservation
"""

import os
from dotenv import load_dotenv

load_dotenv()


def get_booking_defaults():
    """
    Retourne les valeurs par défaut pour les réservations.
    Ces valeurs peuvent être surchargées par des variables d'environnement.
    """
    return {
        "nom": os.getenv("BOOKING_NOM", "Cyril Moriou"),
        "email": os.getenv("BOOKING_EMAIL", "lexpertisedunotaire@gmail.com"),
        "telephone": os.getenv("BOOKING_TELEPHONE", "+33774334897"),
        "site_web": os.getenv("BOOKING_SITE_WEB", "etude-lyon-bugeaud.notaires.fr"),
        "societe": os.getenv("BOOKING_SOCIETE", "Étude Lyon Bugeaud"),
        "preference_creneau": os.getenv(
            "BOOKING_PREFERENCE_CRENEAU",
            "Premier créneau disponible dès demain dans les 7 prochains jours"
        ),
        "type_rdv": os.getenv("BOOKING_TYPE_RDV", "Visio-conférence Google Meet"),
        "message": os.getenv(
            "BOOKING_MESSAGE",
            "Dans le cadre du (re)lancement de notre stratégie de comm, et l'update de nos réseaux (TikTok / Instagram). Votre profil nous semble correspondre à nos besoins, pour nous accompagner sur la mise en forme de tout cela. \n Au plaisir d'en discuter.\nMerci,"
        ),
    }

