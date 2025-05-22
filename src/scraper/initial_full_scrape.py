# src/scraper/initial_full_scrape.py

class PropertyGuruInitialScraper:
    @staticmethod
    def run_scraper_listings(scraper, desired_pages, filename):
        try:
            scraper.scrape_listings(desired_pages=desired_pages)
            scraper.save_to_csv(filename=filename)
            print("")
        except Exception as e:
            print(f"❌ Error on run_scraper_listings: {e}")

    @staticmethod
    def run_scraper_details(scraper, filename):
        try:
            scraper.scrape_details(max_scrape=5)
            scraper.save_to_csv(filename=filename)
            print("")
        except Exception as e:
            print(f"❌ Error on run_scraper_details: {e}")