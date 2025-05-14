# src/main.py
from database import Session, ListingsSample
from scraper.initial_full_scrape import PropertyGuruInitialScraper

if __name__ == '__main__':
    # Create a database session
    session = Session()

    try:
        # Fetch all listings from the database
        print("= Fetching All Listings:")
        ListingsSample.fetch_all(session)

        # Run the initial full scrape for "rent" mode
        print("\n= Starting Initial Full Scrape:")
        PropertyGuruInitialScraper.run_scraper(
            mode="rent",
            max_pages=1,  # Adjust max_pages for production as needed
            output_file="data/listings_rent.csv"
        )

        # # Run the initial full scrape for "buy" mode (optional)
        # PropertyGuruInitialScraper.run_scraper(
        #     mode="buy",
        #     max_pages=1,
        #     output_file="data/listings_buy.csv"
        # )
    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        # Close the database session
        session.close()