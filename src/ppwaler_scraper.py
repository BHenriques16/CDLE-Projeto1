import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import logging

def scrape_pplware(existing_urls: set = None) -> list[dict]:
    if existing_urls is None:
        existing_urls = set()

    logging.info("Starting web scraping on Pplware...")
    extracted_articles = []
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    target_url = "https://pplware.sapo.pt/"
    
    try:
        response = requests.get(target_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error accessing Pplware: {e}")

    soup = BeautifulSoup(response.text, 'html.parser')
    
    article_links = []
    suspicious_elements = soup.find_all(['h2', 'h3', 'h4', 'h5', 'article'])
    
    allowed_categories = [
        '/apple/', '/android/', '/smartphones/', '/hardware/', 
        '/software/', '/inteligencia-artificial/', '/gadgets/', 
        '/jogos/', '/internet/', '/redes-sociais/'
    ]
    
    forbidden_keywords = [
        'fisco', 'irs', 'imposto', 'multa', 'governo', 
        'financas', 'policia', 'politica', 'transito'
    ]
    
    for element in suspicious_elements:
        a_tag = element if element.name == 'a' else element.find('a')
        
        if a_tag and a_tag.has_attr('href'):
            link = a_tag['href'].lower()
            
            if ("pplware.sapo.pt" in link and 
                link != "https://pplware.sapo.pt/" and 
                "/tag/" not in link and 
                "/author/" not in link):
                
                is_tech_category = any(category in link for category in allowed_categories)
                contains_bad_words = any(bad_word in link for bad_word in forbidden_keywords)
                
                # Check whitelist, blacklist, and global duplicates
                if is_tech_category and not contains_bad_words:
                    if link not in article_links and link not in existing_urls:
                        article_links.append(link)

    for url in article_links[:100]:
        try:
            time.sleep(1)
            article_response = requests.get(url, headers=headers, timeout=10)
            article_response.raise_for_status()
            article_soup = BeautifulSoup(article_response.text, 'html.parser')
            
            title_tag = article_soup.find('h1')
            title = title_tag.get_text(strip=True) if title_tag else "Unknown"
            
            author_tag = article_soup.find('a', href=lambda href: href and '/author/' in href)
            author = author_tag.get_text(strip=True) if author_tag else "Unknown"
            
            date_tag = article_soup.find('time')
            pub_date = date_tag.get_text(strip=True) if date_tag else "Unknown"
            
            summary_meta = article_soup.find('meta', attrs={'property': 'og:description'})
            summary = summary_meta['content'] if summary_meta else ""
            
            content_container = article_soup.find('div', class_=['post-content', 'entry-content', 'article-content', 'content']) 
            if not content_container:
                content_container = article_soup.find('article') 
            
            if content_container:
                paragraphs = content_container.find_all('p')
                full_text = " ".join([p.get_text(strip=True) for p in paragraphs])
                if not full_text.strip():
                    full_text = "Content not found inside paragraphs."
            else:
                full_text = "Article container not found."
                
            tags_div = article_soup.find(class_=lambda x: x and 'tag' in x.lower())
            tags = [a.get_text(strip=True) for a in tags_div.find_all('a')] if tags_div else []
            
            extracted_articles.append({
                "id_interno": url,
                "fonte": "Pplware",
                "titulo": title,
                "resumo": summary,
                "autor": author,
                "url": url,
                "data_publicacao": pub_date,
                "data_extracao": datetime.now().isoformat(),
                "categoria": "Tecnologia",
                "tags": tags,
                "texto_completo": full_text
            })
            
        except Exception as e:
            logging.warning(f"Error extracting article {url}: {e}")
            continue

    return extracted_articles
