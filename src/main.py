import json
import logging
import os
from sapo_scraper import scrape_sapo_tek
#from site2_scraper import scrape_site2
#from site3_scraper import scrape_site3

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
    "SAPO TEK":  scrape_sapo_tek,
#    "Site 2":    scrape_site2,
#    "Site 3":    scrape_site3,
}

def save_data(new_articles: list[dict], json_file: str = JSON_FILE) -> int:
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            logging.warning("Invalid existing JSON file — starting from scratch.")
            existing_data = []
    else:
        existing_data = []

    existing_ids = {article['id_interno'] for article in existing_data}
    articles_to_add = []
    seen_in_batch = set()

    for article in new_articles:
        url = article['id_interno']
        if url not in existing_ids and url not in seen_in_batch:
            articles_to_add.append(article)
            seen_in_batch.add(url)

    if articles_to_add:
        existing_data.extend(articles_to_add)
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
        logging.info(f"Saved {len(articles_to_add)} new articles.")
    else:
        logging.info("No new articles to save.")

    return len(articles_to_add)

def run_all():
    all_articles = []
    results = {}

    for name, scraper_fn in SCRAPERS.items():
        logging.info(f"[{name}] Starting extraction...")
        try:
            articles = scraper_fn()
            all_articles.extend(articles)
            results[name] = {"status": "OK", "count": len(articles)}
            logging.info(f"[{name}] {len(articles)} articles extracted successfully.")
        except Exception as e:
            results[name] = {"status": "ERROR", "message": str(e)}
            logging.error(f"[{name}] Failed: {e}")

    # Global deduplication before saving
    total_saved = save_data(all_articles)

    # Final execution summary
    logging.info("=" * 50)
    logging.info("EXECUTION SUMMARY")
    logging.info("=" * 50)
    for name, result in results.items():
        if result["status"] == "OK":
            logging.info(f" {name}: {result['count']} articles extracted")
        else:
            logging.error(f"{name}: {result['message']}")
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