import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import logging

def scrape_pplware(existing_urls: set = None) -> list[dict]:
    if existing_urls is None:
        existing_urls = set()

    logging.info("Starting web scraping on Pplware...")
    print("Starting extraction on Pplware...")
    extracted_articles = []
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    # 1. THE BIG CHANGE: Scrape the homepage AND all specific tech categories
    target_urls = [
        "https://pplware.sapo.pt/",
        "https://pplware.sapo.pt/smartphones/",
        "https://pplware.sapo.pt/apple/",
        "https://pplware.sapo.pt/android/",
        "https://pplware.sapo.pt/hardware/",
        "https://pplware.sapo.pt/software/",
        "https://pplware.sapo.pt/inteligencia-artificial/",
        "https://pplware.sapo.pt/gadgets/",
        "https://pplware.sapo.pt/internet/",
        "https://pplware.sapo.pt/redes_sociais/"
    ]
    
    article_links = []
    
    # Keyword Blacklist
    forbidden_keywords = [
        'fisco', 'irs', 'imposto', 'multa', 'governo', 
        'financas', 'policia', 'politica', 'transito'
    ]
    
    # 2. Loop through every single category page
    for target in target_urls:
        try:
            response = requests.get(target, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            suspicious_elements = soup.find_all(['h2', 'h3', 'h4', 'h5', 'article'])
            
            for element in suspicious_elements:
                a_tag = element if element.name == 'a' else element.find('a')
                
                if a_tag and a_tag.has_attr('href'):
                    link = a_tag['href'].lower()
                    
                    # Ensure it's a valid article link
                    if ("pplware.sapo.pt" in link and 
                        link not in target_urls and 
                        "/tag/" not in link and 
                        "/author/" not in link):
                        
                        contains_bad_words = any(bad_word in link for bad_word in forbidden_keywords)
                        
                        # If it has no bad words and we haven't scraped it before
                        if not contains_bad_words:
                            if link not in article_links and link not in existing_urls:
                                article_links.append(link)
                                
        except requests.exceptions.RequestException as e:
            logging.error(f"Error accessing {target}: {e}")
            continue

    print(f"Found {len(article_links)} NEW tech-only links across all categories. Extracting data...")

    # 3. Extract EVERYTHING found (No slicing limit)
    for url in article_links:
        try:
            time.sleep(1) # Friendly pause to avoid overloading the server
            article_response = requests.get(url, headers=headers, timeout=10)
            article_response.raise_for_status()
            article_soup = BeautifulSoup(article_response.text, 'html.parser')
            
            title_tag = article_soup.find('h1')
            title = title_tag.get_text(strip=True) if title_tag else "Unknown"
            
            print(f"   -> Downloading: {title}")
            
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

            tags_elements = article_soup.select('a[rel="tag"]')
            tags = [tag.get_text(strip=True) for tag in tags_elements]
            
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
            print(f"   Error in link {url}: {e}")
            continue

    print("Pplware extraction completed!")
    return extracted_articles
