import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

def scrape_exame_informatica(existing_urls: set = None) -> list[dict]:
    if existing_urls is None:
        existing_urls = set()

    extracted_articles = []
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    base_url = "https://visao.pt/exameinformatica/"
    
    try:
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"[Exame Informática] Error accessing the site: {e}")
        return extracted_articles

    soup = BeautifulSoup(response.text, 'html.parser')

    seen_links = set()
    article_links = []
    
    for a_tag in soup.find_all('a', href=True):
        link = a_tag['href']
        
        # Skip navigation and taxonomy links
        if any(x in link for x in ['/tag/', '/author/', '/page/', '/category/']):
            continue
        
        # Article URLs typically contain multiple hyphens
        if "visao.pt/exameinformatica/" in link and link != base_url and link.count('-') >= 3:
            if link not in seen_links and link not in existing_urls:
                seen_links.add(link)
                article_links.append(link)

    def fetch_article(url):
        time.sleep(0.3)  
        try:
            article_response = requests.get(url, headers=headers, timeout=10)
            article_response.raise_for_status()
            article_soup = BeautifulSoup(article_response.text, 'html.parser')
            
            # Skip pages without a title (not a real article)
            title_tag = article_soup.find('h1')
            if not title_tag:
                return None
            
            title = title_tag.get_text(strip=True)
            
            summary_meta = article_soup.find('meta', attrs={'property': 'og:description'})
            summary = summary_meta['content'] if summary_meta else ""
            
            author_tag = article_soup.find(class_=lambda x: x and 'author' in x.lower())
            author = author_tag.get_text(strip=True) if author_tag else "Unknown"
            
            date_tag = article_soup.find('time')
            pub_date = date_tag.get_text(strip=True) if date_tag else "Unknown"
            
            content_container = article_soup.find('div', class_=['post-content', 'entry-content', 'article-content', 'content'])
            if not content_container:
                content_container = article_soup.find('article')
                
            full_text = "Content not found."
            if content_container:
                paragraphs = content_container.find_all('p')
                full_text = " ".join([p.get_text(strip=True) for p in paragraphs])
                if not full_text.strip():
                    full_text = "Empty content."

            tags = [tag.get_text(strip=True) for tag in article_soup.select('.keyword-wrapper a')]

            return {
                "id_interno": url,
                "fonte": "Exame Informática",
                "titulo": title,
                "resumo": summary,
                "autor": author,
                "url": url,
                "data_publicacao": pub_date,
                "data_extracao": datetime.now().isoformat(),
                "categoria": "Technology",
                "tags": tags,
                "texto_completo": full_text
            }
        except Exception as e:
            logging.warning(f"[Exame Informática] Error extracting article {url}: {e}")
            return None

    # Fetch articles in parallel (5 workers)
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_article, url): url for url in article_links[:100]}
        for future in as_completed(futures):
            result = future.result()
            if result:
                extracted_articles.append(result)

    return extracted_articles