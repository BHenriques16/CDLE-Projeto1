import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging

BASE_URL = "https://tek.sapo.pt"
NUMBER_OF_ARTICLES = 100
MAX_PAGES = 10

def scrape_sapo_tek(existing_urls: set = None) -> list[dict]:
    if existing_urls is None:
        existing_urls = set()

    new_articles = []
    seen_urls = set(existing_urls)

    # Collect unique article links across multiple listing pages
    article_links = []

    for page in range(1, MAX_PAGES + 1):
        page_url = BASE_URL if page == 1 else f"{BASE_URL}/page/{page}/"

        try:
            response = requests.get(page_url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.warning(f"[SAPO TEK] Could not access page {page}: {e}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')

        for a_tag in soup.select('a[href*="/artigos/"]'):
            article_url = a_tag.get('href', '')
            if not article_url:
                continue
            if not article_url.startswith('http'):
                article_url = BASE_URL + article_url
                article_url = article_url.lower().rstrip('/')

            # Deduplicate against already-known URLs and current batch
            if article_url not in seen_urls and article_url not in article_links:
                article_links.append(article_url)

        if len(article_links) >= NUMBER_OF_ARTICLES:
            break

    # Scrape each article page, up to the defined limit
    for article_url in article_links[:NUMBER_OF_ARTICLES]:
        seen_urls.add(article_url)

        try:
            article_resp = requests.get(article_url, timeout=10)
            article_resp.raise_for_status()
            article_soup = BeautifulSoup(article_resp.text, 'html.parser')

            # Title
            title_tag = article_soup.select_one('.wp-block-post-title')
            title = title_tag.get_text(strip=True) if title_tag else "No title"

            # Summary
            excerpt_tag = article_soup.select_one('.wp-block-post-excerpt__excerpt')
            excerpt = excerpt_tag.get_text(strip=True) if excerpt_tag else ""

            # Author
            author = "Sapo Tek"
            author_tag = article_soup.select_one('h3.wp-block-heading')
            if author_tag:
                text = author_tag.get_text(strip=True)
                if "By " in text and "(*)" in text or "Por " in text:
                    author = text.replace("(*)", "").replace("Por ", "").replace("By ", "").strip()

            if author == "Sapo Tek":
                for strong in article_soup.find_all("strong"):
                    text = strong.get_text(" ", strip=True)
                    if ("Por " in text or "By " in text) and "(*)" in text:
                        author = text.replace("(*)", "").replace("Por ", "").replace("By ", "").strip()
                        break

            # Date
            date_tag = article_soup.select_one('.article-date, time')
            pub_date = date_tag.get_text(strip=True) if date_tag else "Unknown"

            # Full Text
            content_div = article_soup.select_one('.entry-content')
            full_text = (
                " ".join([p.get_text(strip=True) for p in content_div.find_all('p')])
                if content_div else ""
            )

            # Tags
            tags_elements = article_soup.select('a[rel="tag"]')
            tags = [tag.get_text(strip=True) for tag in tags_elements]

            new_articles.append({
                "id_interno": article_url,
                "fonte": "SAPO Notícias / TEK",
                "titulo": title,
                "resumo": excerpt,
                "autor": author,
                "url": article_url,
                "data_publicacao": pub_date,
                "data_extracao": datetime.now().isoformat(),
                "categoria": "Technology",
                "tags": tags,
                "texto_completo": full_text
            })

        except Exception as e:
            logging.warning(f"[SAPO TEK] Error extracting article {article_url}: {e}")
            continue

    return new_articles