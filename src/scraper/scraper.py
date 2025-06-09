# src/scraper/scraper.py

class PropertyGuruScraper:
    @staticmethod
    def run_scraper_listings(scraper, desired_pages, listings_csv_path):
        try:
            scraper.scrape_listings(desired_pages=desired_pages)
            scraper.save_listings_to_csv(listings_csv_path)
            print("")
        except Exception as e:
            print(f"❌ Error on run_scraper_listings: {e}")

    @staticmethod
    def run_scraper_details(scraper, max_scrape, details_csv_path):
        try:
            scraper.scrape_details(max_scrape=max_scrape)
            scraper.save_details_to_csv(details_csv_path)
            print("")
        except Exception as e:
            print(f"❌ Error on run_scraper_details: {e}")