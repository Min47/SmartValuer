from database import Session, ListingsSample
from scraper.initial_full_scrape import PropertyGuruInitialScraper
from scraper.incremental_scraper import PropertyGuruIncrementalScraper

if __name__ == '__main__':
    # Create a session
    session = Session()

    # Fetch all listings
    # ListingsSample.test_listing()
    ListingsSample.fetch_all(session)
    # Close the session
    session.close()

    # Run the initial full scrape
    scraper = PropertyGuruInitialScraper.main()