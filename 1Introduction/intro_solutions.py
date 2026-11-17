import random
import time
from urllib.parse import urlparse, urljoin, parse_qs
import requests
from bs4 import BeautifulSoup

class HttpClient:
    """Client à User-Agent fixe ; retries récursifs bornés."""
    def __init__(self, user_agent="DataEngineerTools/1.0 (educational)"):
        self.user_agent = user_agent
        self.session = requests.Session()

    def get(self, url, timeout=10, retries=2, **kwargs):
        if not 0 <= retries <= 10:
            raise ValueError("retries doit être compris entre 0 et 10")
        headers = dict(kwargs.pop("headers", {}))
        headers["User-Agent"] = self.user_agent
        try:
            response = self.session.get(url, timeout=timeout, headers=headers, **kwargs)
            response.raise_for_status()
            return response
        except (requests.Timeout, requests.ConnectionError):
            if retries == 0:
                raise
        except requests.HTTPError as error:
            # Pas de nouvelle tentative sur une erreur client (403, 404...).
            if error.response.status_code not in (500, 502, 503, 504) or retries == 0:
                raise
        time.sleep(1)
        return self.get(url, timeout=timeout, retries=retries-1, headers=headers, **kwargs)

    def close(self):
        self.session.close()


def clean_spaces(text):
    """Réduit espaces, tabulations et retours à la ligne à un espace."""
    return " ".join(text.split())

def clean_html(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    # BeautifulSoup décode aussi les entités (&amp;, &nbsp;...).
    return clean_spaces(soup.get_text(" ", strip=True))

def get_domain(url):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Une URL absolue HTTP(S) est attendue")
    return parsed.hostname.lower()

assert clean_spaces("  Bonjour\n  Fami\t ! ") == "Bonjour Fami !"
assert clean_html("<p>Café &amp; thé</p><script>bad()</script>") == "Café & thé"
assert get_domain("https://example.org:443/article") == "example.org"


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0",
]

class Scraper(HttpClient):
    def get(self, url, **kwargs):
        # Rotation demandée par l'exercice 3 ; la classe de base reste fixe.
        self.user_agent = random.choice(USER_AGENTS)
        return super().get(url, **kwargs)

    def get_soup(self, url, **kwargs):
        response = self.get(url, **kwargs)
        return BeautifulSoup(response.content, "html.parser")

    def parse_page(self, html, url):
        soup = BeautifulSoup(html, "html.parser")
        def absolute(value):
            result = urljoin(url, value)
            return result if urlparse(result).scheme in ("http", "https") else None
        images = list(dict.fromkeys(filter(None, (absolute(img['src']) for img in soup.select('img[src]')))))
        links = list(dict.fromkeys(filter(None, (absolute(a['href']) for a in soup.select('a[href]')))))
        main = soup.find('article') or soup.find('main') or soup.body or soup
        # Heuristique : article, puis main ; sinon corps sans navigation.
        main = BeautifulSoup(str(main), "html.parser")
        for tag in main.select('nav, header, footer, aside, script, style, noscript'):
            tag.decompose()
        return {
            'url': url, 'domain': get_domain(url),
            'title': clean_spaces(soup.title.get_text()) if soup.title else '',
            'h1': [clean_spaces(h.get_text(' ', strip=True)) for h in soup.find_all('h1')],
            'images': images,
            'outgoing_links': [link for link in links if get_domain(link) != get_domain(url)],
            'text': clean_html(str(main)),
        }

    def scrape(self, url):
        response = self.get(url)
        return self.parse_page(response.content, response.url)

scraper = Scraper()
example_html = '<title>Exemple</title><main><h1>Bonjour</h1><p>Un article.</p><img src="/photo.jpg"><a href="https://other.org">Lien</a></main>'
scraper.parse_page(example_html, 'https://example.org/article')


def parse_google_results(html, base_url="https://www.google.com/search", limit=5):
    soup = BeautifulSoup(html, "html.parser")
    results, seen = [], set()
    for heading in soup.find_all('h3'):
        anchor = heading.find_parent('a', href=True)
        if not anchor:
            continue
        href = urljoin(base_url, anchor['href'])
        parsed = urlparse(href)
        if parsed.path == '/url':
            params = parse_qs(parsed.query)
            href = (params.get('q') or params.get('url') or [''])[0]
        parsed = urlparse(href)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname:
            continue
        if parsed.hostname == 'google.com' or parsed.hostname.endswith('.google.com'):
            continue
        if href in seen:
            continue
        results.append({'title': clean_spaces(heading.get_text(' ', strip=True)), 'url': href})
        seen.add(href)
        if len(results) >= limit:
            break
    return results

def google_search(query, limit=5):
    if limit <= 0:
        return []
    response = scraper.get('https://www.google.com/search', params={'q': query, 'num': limit})
    results = parse_google_results(response.content, response.url, limit)
    if not results:
        raise RuntimeError("Aucun résultat exploitable : consentement, CAPTCHA ou HTML modifié. Ne pas contourner le blocage.")
    return results

# À lancer séparément pour une requête réelle :
# google_search('data engineering ESIEE')
parse_google_results('<a href="/url?q=https%3A%2F%2Fexample.org"><h3>Exemple</h3></a>')


import json
from pathlib import Path
from xml.etree import ElementTree as ET

def collect_news(feed_url, category, limit=3, delay=1):
    """Lit un flux RSS 2.0 puis visite au maximum limit articles publics."""
    if limit <= 0:
        return {'articles': [], 'errors': []}
    response = scraper.get(feed_url)
    feed = ET.fromstring(response.content)
    articles, errors, seen = [], [], set()
    for item in feed.findall('./channel/item'):
        url = (item.findtext('link') or '').strip()
        if not url or url in seen:
            continue
        seen.add(url)
        if len(seen) > limit:
            break
        time.sleep(delay)
        try:
            data = scraper.scrape(url)
            if not data['text']:
                raise ValueError('Texte principal vide')
            articles.append({
                'text': data['text'], 'url': data['url'], 'domain': data['domain'],
                'category': item.findtext('category') or category,
                'article_title': data['h1'][0] if data['h1'] else clean_spaces(item.findtext('title') or ''),
                'page_title': data['title'], 'images': data['images'],
            })
        except (requests.RequestException, ValueError) as error:
            errors.append({'url': url, 'error': str(error)})
    return {'articles': articles, 'errors': errors}

# Exécution réseau volontairement séparée : vérifier les règles du média.
# Pas de contournement des pages réservées aux abonnés.
# news = collect_news('https://www.lemonde.fr/sciences/rss_full.xml', 'Sciences')
# Path('news.json').write_text(json.dumps(news, ensure_ascii=False, indent=2), encoding='utf-8')

