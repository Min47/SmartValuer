# src/scraper/incremental_scraper.py
from scraper.scraper_utils import ScraperUtils

class PropertyGuruIncrementalScraper:
    def main():
        # modes = ['buy', 'rent']
        modes = ['rent']  # For initial testing, only scrape rent mode
        for mode in modes:
            scraper = ScraperUtils(mode=mode)
            scraper.scrape(desired_pages=1)  # Remove desired_pages for full scrape
            scraper.save_to_csv(filename=f"data/listings_{mode}.csv")
            scraper.close()