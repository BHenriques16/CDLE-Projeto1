import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import logging

def scrape_exame_informatica(existing_urls: set = None) -> list[dict]:
    if existing_urls is None:
        existing_urls = set()

    logging.info("Starting Exame Informática extraction...")
    extracted_articles = []
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    base_url = "https://visao.pt/exameinformatica/"
    
    try:
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error accessing Exame Informática: {e}")
        return extracted_articles

    soup = BeautifulSoup(response.text, 'html.parser')
    article_links = []
    
    for a_tag in soup.find_all('a', href=True):
        link = a_tag['href']
        
        # Skip navigation and taxonomy links
        if any(x in link for x in ['/tag/', '/author/', '/page/', '/category/']):
            continue
        
        # Article URLs typically contain multiple hyphens
        if "visao.pt/exameinformatica/" in link and link != base_url and link.count('-') >= 3:
            if link not in article_links and link not in existing_urls:
                article_links.append(link)

    for url in article_links[:100]:
        try:
            time.sleep(1) 
                        
            article_response = requests.get(url, headers=headers, timeout=10)
            article_response.raise_for_status()
            article_soup = BeautifulSoup(article_response.text, 'html.parser')
            
            # Skip pages without a title (not a real article)
            title_tag = article_soup.find('h1')
            if not title_tag:
                continue
            
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
            
            extracted_articles.append({
                "id_interno": url,
                "fonte": "Exame Informática",
                "titulo": title,
                "resumo": summary,
                "autor": author,
                "url": url,
                "data_publicacao": pub_date,
                "data_extracao": datetime.now().isoformat(),
                "categoria": "Technology",
                "tags": [],
                "texto_completo": full_text
            })
            
        except Exception as e:
            logging.warning(f"Error extracting article {url}: {e}")
            continue

    return extracted_articles