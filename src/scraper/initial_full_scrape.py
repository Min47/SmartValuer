# src/scraper/initial_full_scrape.py
from scraper.scraper_utils import ScraperUtils

class PropertyGuruInitialScraper:
    @staticmethod
    def run_scraper(session, mode, unit_type, desired_pages, filename):
        try:
            # Validate unit_type for "Buy" mode
            if mode == "Buy" and unit_type == -1:
                raise ValueError("Invalid unit_type '-1' for mode 'Buy'. Please select a valid unit_type.")

            scraper = ScraperUtils(session=session, mode=mode, unit_type=unit_type)
            scraper.scrape_listings(desired_pages=desired_pages)
            scraper.save_to_csv(filename=filename)
            print("")
        except Exception as e:
            print(f"❌ Error on run_scraper: {e}")