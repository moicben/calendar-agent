import argparse
import json
import logging
import os
import re
import sys
from typing import Iterable, List, Set

import requests
from dotenv import load_dotenv


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[scraper] %(asctime)s %(levelname)s - %(message)s",
    )


def project_path(*parts: str) -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, *parts)


def read_lines(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        # Conserve l'ordre, ignore lignes vides/commentaires
        return [ln.strip() for ln in f.readlines() if ln.strip() and not ln.strip().startswith("#")]


def write_lines(path: str, lines: Iterable[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(f"{line}\n")


def append_lines(path: str, lines: Iterable[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for line in lines:
            f.write(f"{line}\n")


def canonicalize(item: str) -> str:
    s = item.strip()
    # Enlever protocole inutile
    s = re.sub(r'^(?:https?://)?(?:www\.)?', '', s, flags=re.IGNORECASE)
    # Retirer slash final simple
    if s.endswith('/'):
        s = s[:-1]
    # Retirer ponctuation finale courante
    s = s.rstrip('.,);:!?')
    # Repasser le domaine en minuscule (avant le premier /)
    parts = s.split('/', 1)
    parts[0] = parts[0].lower()
    s = '/'.join(parts)
    return s


def unique_preserve_order(items: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    result: List[str] = []
    duplicates = []
    
    for it in items:
        canonical_it = canonicalize(it)
        if canonical_it not in seen:
            seen.add(canonical_it)
            result.append(it)
        else:
            duplicates.append(it)
    
    if duplicates:
        logging.info("Doublons détectés et filtrés: %d", len(duplicates))
        logging.debug("URLs en doublon: %s", duplicates)
    
    return result


def fetch_serper(query: str, api_key: str, endpoint: str, num: int, page: int = 1) -> dict:
    if endpoint == "news":
        url = "https://google.serper.dev/news"
        payload = {"q": query, "num": num, "page": page, "gl": "fr", "hl": "fr"}
    else:
        url = "https://google.serper.dev/search"
        payload = {"q": query, "num": num, "page": page, "gl": "fr", "hl": "fr"}

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }

    logging.debug("Requête Serper.dev: %s %s", url, json.dumps(payload, ensure_ascii=False))
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    try:
        resp.raise_for_status()
    except Exception as e:  # noqa: BLE001
        logging.error("Appel Serper a échoué: status=%s body=%s", resp.status_code, resp.text)
        raise e
    return resp.json()


def extract_calendar_urls_from_snippet(snippet: str) -> List[str]:
    """Extrait les URLs de calendriers depuis un snippet de texte."""
    if not snippet:
        return []
    
    # Pattern pour détecter les URLs de calendriers (avec ou sans protocole, avec ou sans www)
    calendar_patterns = [
        r'(?:https?://)?(?:www\.)?calendly\.com/[^\s<>"\']+',
        r'(?:https?://)?(?:www\.)?cal\.com/[^\s<>"\']+',
        #r'(?:https?://)?(?:www\.)?calendar\.app\.google/[^\s<>"\']+',
    ]
    
    urls = []
    for pattern in calendar_patterns:
        matches = re.findall(pattern, snippet, re.IGNORECASE)
        if matches:
            logging.debug("Pattern '%s' a trouvé %d URLs dans le snippet", pattern, len(matches))
            urls.extend(matches)
    
    if urls:
        logging.debug("Snippet contenait %d URLs de calendriers: %s", len(urls), urls)
    
    return urls


def extract_links(payload: dict, endpoint: str) -> List[str]:
    """Extrait les URLs de calendriers depuis les snippets des résultats Serper."""
    calendar_urls: List[str] = []
    
    if endpoint == "news":
        items = payload.get("news", []) or []
    else:
        items = payload.get("organic", []) or []
    
    for item in items:
        snippet = item.get("snippet", "")
        if snippet:
            urls = extract_calendar_urls_from_snippet(snippet)
            calendar_urls.extend(urls)
    
    return calendar_urls


def fetch_all_pages(query: str, api_key: str, endpoint: str, max_pages: int) -> List[str]:
    """Récupère le nombre spécifié de pages, s'arrête si aucune URL trouvée."""
    all_urls = []
    page_size = 10  # Toujours 10 résultats par page
    page_num = 1
    
    logging.info("📄 Pagination automatique: maximum %d pages, %d par page", max_pages, page_size)
    
    while page_num <= max_pages:
        logging.info("📖 Page %d/%d (page=%d):", page_num, max_pages, page_num)
        
        try:
            data = fetch_serper(query, api_key, endpoint, page_size, page_num)
            page_urls = extract_links(data, endpoint)
            
            if page_urls:
                logging.info("  ✅ URLs trouvées sur cette page: %d", len(page_urls))
                logging.info("  📊 Total accumulé: %d URLs", len(all_urls) + len(page_urls))
                if page_urls:
                    logging.debug("  🔗 URLs de cette page: %s", page_urls)
            else:
                logging.info("  ❌ Aucune URL trouvée sur la page %d", page_num)
                logging.info("🛑 Arrêt de la pagination pour cette requête.")
                break
            
            all_urls.extend(page_urls)
            page_num += 1
            
        except Exception as e:
            logging.error("❌ Erreur lors de la récupération de la page %d: %s", page_num, e)
            break
    
    logging.info("🏁 Pagination terminée: %d pages scrapées, %d URLs trouvées", page_num - 1, len(all_urls))
    return all_urls


def run(query: str, endpoint: str, num: int, verbose: bool) -> int:
    configure_logging(verbose)
    load_dotenv()

    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        logging.error("SERPER_API_KEY manquant. Renseignez-le dans .env (voir ENV.sample).")
        return 2

    # Recherches automatiques pour chaque domaine de calendrier
    calendar_domains = ["calendly.com/", "cal.com/", "calendar.app.google/"]
    all_links = []
    
    logging.info("🚀 Démarrage des recherches automatiques pour: %s", query)
    logging.info("🔍 Domaines de calendriers recherchés: %s", ", ".join(calendar_domains))
    logging.info("📋 Nombre de pages à scraper par requête: %d", num)
    logging.info("=" * 60)

    for domain in calendar_domains:
        search_query = f'"{query}" "{domain}"'
        logging.info("🔎 Recherche Serper.dev: query=\"%s\" endpoint=%s pages=%d", search_query, endpoint, num)
        
        try:
            # Utilise la pagination automatique pour scraper le nombre de pages spécifié
            domain_links_raw = fetch_all_pages(search_query, api_key, endpoint, num)
            domain_links = [canonicalize(l) for l in domain_links_raw if l]
            
            logging.info("📈 Résultats pour %s: %d URLs trouvées", domain, len(domain_links))
            if domain_links:
                logging.info("📝 URLs détectées pour %s:", domain)
                for i, url in enumerate(domain_links, 1):
                    logging.info("  %d. %s", i, url)
            
            all_links.extend(domain_links)
            logging.info("-" * 40)
            
        except Exception as e:
            logging.error("❌ Erreur lors de la recherche pour %s: %s", domain, e)
            continue

    # Consolidation des résultats
    logging.info("=" * 60)
    logging.info("📊 Consolidation des résultats:")
    logging.info("📥 Total URLs brutes avant dédoublonnage: %d", len(all_links))
    links = unique_preserve_order(all_links)
    logging.info("📤 Total URLs de calendriers trouvées (après dédoublonnage): %d", len(links))
    
    if links:
        logging.info("📋 Toutes les URLs détectées:")
        for i, url in enumerate(links, 1):
            logging.info("  %d. %s", i, url)

    calendars_dir = project_path("../calendars")
    path_historic = project_path("../calendars", "historic")
    path_new = project_path("../calendars", "new")

    historic = read_lines(path_historic)
    historic_set = {canonicalize(x) for x in historic}

    # Séparation des URLs nouvelles et déjà connues
    new_items = []
    already_known_items = []
    
    for link in links:
        canonical_link = canonicalize(link)
        if canonical_link not in historic_set:
            new_items.append(link)
        else:
            already_known_items.append(link)

    logging.info("=" * 60)
    logging.info("🔍 Filtrage des URLs:")
    logging.info("📚 URLs déjà connues (filtrées): %d", len(already_known_items))
    if already_known_items:
        logging.info("📖 URLs déjà dans l'historique:")
        for i, url in enumerate(already_known_items, 1):
            logging.info("  %d. %s", i, url)

    logging.info("🆕 Nouveaux calendriers détectés: %d", len(new_items))
    if new_items:
        logging.info("✨ Nouveaux URLs de calendriers:")
        for i, url in enumerate(new_items, 1):
            logging.info("  %d. %s", i, url)
        
        os.makedirs(calendars_dir, exist_ok=True)
        # Ecrit les nouveaux du run courant dans `new` (remplacement)
        write_lines(path_new, new_items)
        # Ajoute aussi dans l'historique (append)
        append_lines(path_historic, new_items)
        logging.info("💾 Ecriture effectuée: %s (new), %s (historic)", path_new, path_historic)
    else:
        # Aucun nouveau; vide le fichier `new` pour refléter l'absence de nouveautés
        write_lines(path_new, [])
        logging.info("📭 Aucun nouveau calendrier détecté. `new` a été vidé.")

    # Résumé clair pour usage shell
    print(json.dumps({
        "query": query,
        "endpoint": endpoint,
        "found": len(links),
        "new": len(new_items),
        "paths": {"new": path_new, "historic": path_historic},
    }, ensure_ascii=False))

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Scraper de calendriers via Serper.dev.\n"
            "- Exécute automatiquement 3 recherches: '{query}' \"calendly.com/\", '{query}' \"cal.com/\", '{query}' \"calendar.app.google/\"\n"
            "- Scrape le nombre de pages spécifié par requête (--num pages par requête).\n"
            "- S'arrête pour une requête si aucune URL trouvée sur une page.\n"
            "- Recherche les URLs de calendriers dans les snippets des résultats.\n"
            "- Ecrit les nouvelles URLs dans `calendars/new` (uniquement celles non vues).\n"
            "- Ajoute aussi ces nouvelles URLs à `calendars/historic`.\n"
            "- Si déjà vues, elles ne sont ajoutées ni à new ni à historic."
        )
    )
    parser.add_argument("query", help="Requête à envoyer à Serper.dev")
    parser.add_argument("--endpoint", choices=["search", "news"], default="search", help="Endpoint Serper: search ou news (defaut: search)")
    parser.add_argument("--num", type=int, default=1, help="Nombre de pages à scraper par requête (defaut: 1)")
    parser.add_argument("--verbose", action="store_true", help="Active les logs DEBUG")

    args = parser.parse_args()

    exit_code = run(query=args.query, endpoint=args.endpoint, num=args.num, verbose=args.verbose)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()