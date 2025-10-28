# coding: utf-8
"""
Configuration centralisée pour les informations de réservation
"""


def get_booking_defaults():
    """
    Retourne les valeurs par défaut pour les réservations.
    Modifiez directement les valeurs ci-dessous selon vos besoins.
    """
    return {
        "nom": "Cyril Moriou",
        "email": "lexpertisedunotaire@gmail.com",
        "telephone": "+33774334897",
        "site_web": "etude-lyon-bugeaud.notaires.fr",
        "societe": "Étude Lyon Bugeaud",
        "preference_creneau": "Premier créneau disponible dès demain dans les 7 prochains jours",
        "type_rdv": "Visio-conférence Google Meet",
        "message": "Dans le cadre du (re)lancement de notre stratégie de comm, et l'update de nos réseaux (TikTok / Instagram). Votre profil nous semble correspondre à nos besoins, pour nous accompagner sur la mise en forme de tout cela. \n Au plaisir d'en discuter.\nMerci,",
    }

