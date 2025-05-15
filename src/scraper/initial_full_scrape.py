# src/scraper/initial_full_scrape.py
from scraper.scraper_utils import ScraperUtils

class PropertyGuruInitialScraper:
    @staticmethod
    def run_scraper(mode, desired_pages, session):
        try:
            scraper = ScraperUtils(mode=mode)
            scraper.scrape(desired_pages=desired_pages)
            scraper.save_to_csv()
            # scraper.save_to_db(session=session)
        except Exception as e:
            print(f"❌ Error on run_scraper: {e}")