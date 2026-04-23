import json
import logging
import os
from pplware_scraper.py import scrape_pplware
from sapo_scraper.py import scrape_sapo_tek

# Configuration
JSON_FILE = "data/articles.json"
LOG_FILE  = "logs/extraction.log"

os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Output logs to console for real-time feedback (e.g., GitHub Actions)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(console)

# Scraper registry - add new sites here
SCRAPERS = {
    "PPLWARE":  scrape_pplware,
    "SAPO TEK": scrape_sapo_tek,
#   "Site 3":   scrape_site3,
}

def load_existing_data(json_file: str = JSON_FILE) -> list:
    """Loads the existing JSON file so we know what we already have."""
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            logging.warning("Invalid existing JSON file — starting from scratch.")
    return []

def save_data(existing_data: list, new_articles: list[dict], json_file: str = JSON_FILE) -> int:
    """Appends new articles to the existing data and saves the file."""
    if not new_articles:
        logging.info("No new articles to save.")
        return 0
        
    existing_data.extend(new_articles)
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)
    
    logging.info(f"Saved {len(new_articles)} new articles.")
    return len(new_articles)

def run_all():
    # 1. Load the database ONCE at the very beginning
    existing_data = load_existing_data()
    
    # Create a fast-lookup set of all URLs we already have
    existing_urls = {article['id_interno'] for article in existing_data if 'id_interno' in article}
    
    all_new_articles = []
    results = {}

    for name, scraper_fn in SCRAPERS.items():
        logging.info(f"[{name}] Starting extraction...")
        try:
            # 2. Pass the existing URLs to the scraper so it ignores old news
            articles = scraper_fn(existing_urls)
            all_new_articles.extend(articles)
            
            # 3. Add the newly found URLs to the set so the next scraper doesn't duplicate them
            for article in articles:
                existing_urls.add(article['id_interno'])
                
            results[name] = {"status": "OK", "count": len(articles)}
            logging.info(f"[{name}] {len(articles)} new articles extracted successfully.")
            
        except Exception as e:
            results[name] = {"status": "ERROR", "message": str(e)}
            logging.error(f"[{name}] Failed: {e}")

    # 4. Save everything to the JSON file
    total_saved = save_data(existing_data, all_new_articles)

    # Final execution summary
    logging.info("=" * 50)
    logging.info("EXECUTION SUMMARY")
    logging.info("=" * 50)
    for name, result in results.items():
        if result["status"] == "OK":
            logging.info(f" {name}: {result['count']} new articles extracted")
        else:
            logging.error(f" {name}: {result['message']}")
    logging.info(f"  → Total saved: {total_saved} new articles")
    logging.info("=" * 50)

    # Exit with error code if any scraper failed
    failed = [n for n, r in results.items() if r["status"] == "ERROR"]
    if failed:
        raise SystemExit(f"The following scrapers failed: {', '.join(failed)}")

if __name__ == "__main__":
    logging.info("--- JOB STARTED ---")
    run_all()
    logging.info("--- JOB FINISHED ---\n")
