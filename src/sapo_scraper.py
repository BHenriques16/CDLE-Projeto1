import requests
import re
from bs4 import BeautifulSoup
import json
import logging
import os
from datetime import datetime

# Configure logging as required by the project guidelines [cite: 68]
logging.basicConfig(
    filename='logs/extraction.log', 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def scrape_sapo_tek():
    url_base = "https://tek.sapo.pt"
    
    try:
        response = requests.get(url_base)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error accessing main page: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    new_articles = []

    article_links = soup.select('a[href*="/artigos/"]') 
    print(f"Number of links found: {len(article_links)}")

    for link in article_links[:1]:
        article_url = link.get('href')
        if not article_url.startswith('http'):
            article_url = url_base + article_url

        try:
            article_resp = requests.get(article_url)
            article_soup = BeautifulSoup(article_resp.text, 'html.parser')
            
            # 1. Title 
            title_tag = article_soup.select_one('.wp-block-post-title')
            title = title_tag.get_text(strip=True) if title_tag else "No title"
            
            # 2. Summary
            excerpt_tag = article_soup.select_one('.wp-block-post-excerpt__excerpt')
            excerpt = excerpt_tag.get_text(strip=True) if excerpt_tag else ""
            
            # 3. Author 
            author = "Unknown"
            for strong in article_soup.find_all("strong"):
                text = strong.get_text(" ", strip=True)
                print(repr(text))
                if "Por " in text and "(*)" in text:
                    author = text.replace("(*)", "").replace("Por ", "", 1).strip()
                    print(f"Author found: {author}")
                    break
            
            # 4. Date
            date_tag = article_soup.select_one('.article-date, time')
            pub_date = date_tag.get_text(strip=True) if date_tag else "Unknown"
            
            # 5. Full Text 
            content_div = article_soup.select_one('.entry-content')
            full_text = " ".join([p.get_text(strip=True) for p in content_div.find_all('p')]) if content_div else ""
            
            # 6. Tags
            tags_elements = article_soup.select('a[rel="tag"]')
            tags = [tag.get_text(strip=True) for tag in tags_elements]

            article_data = {
                "id_interno": article_url,
                "fonte": "SAPO Notícias / TEK",
                "titulo": title,
                "resumo": excerpt,
                "autor": author,
                "url": article_url,
                "data_publicacao": pub_date,
                "data_extracao": datetime.now().isoformat(),
                "categoria": "Tecnologia",
                "tags": tags,
                "texto_completo": full_text
            }
            
            new_articles.append(article_data)
            logging.info(f"Successfully extracted: {article_url}")
            print(json.dumps(article_data, indent=4, ensure_ascii=False))

        except Exception as e:
            logging.warning(f"Error extracting {article_url}: {e}")

    return new_articles

def save_data(new_articles, json_file='data/sapo.json'):
    # Load existing data to avoid duplicates
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            existing_data = []
    else:
        existing_data = []

    # Filter to only add unique articles
    existing_ids = {article['id_interno'] for article in existing_data}
    articles_to_add = [n for n in new_articles if n['id_interno'] not in existing_ids]

    if articles_to_add:
        existing_data.extend(articles_to_add)
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
        logging.info(f"Saved {len(articles_to_add)} new articles.")
    else:
        logging.info("No new articles to save.")

if __name__ == "__main__":
    logging.info("Starting scraper job.")
    data = scrape_sapo_tek()
    save_data(data)
    logging.info("Scraper job finished.\n---")