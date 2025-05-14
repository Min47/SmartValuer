# src/scraper/initial_full_scrape.py
from scraper.scraper_utils import ScraperUtils

class PropertyGuruInitialScraper:
    @staticmethod
    def run_scraper(mode="rent", desired_pages=None, output_file="data/listings.csv"):
        """
        Run the scraper for the specified mode and save the results to a CSV file.

        :param mode: The mode to scrape ("rent" or "buy").
        :param desired_pages: The maximum number of pages to scrape (None for all pages).
        :param output_file: The file path to save the scraped data.
        """
        try:
            scraper = ScraperUtils(mode=mode)
            scraper.scrape(desired_pages=desired_pages)
            scraper.save_to_csv(filename=output_file)
        except Exception as e:
            print(f"❌ Error during scraping: {e}")