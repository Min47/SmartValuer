# src/main.py
from database import Session, ListingsSample
from scraper.initial_full_scrape import PropertyGuruInitialScraper

if __name__ == '__main__':
    try:
        # Database connection
        print("-----------------------")
        print("| Database Connection |")
        print("-----------------------")

        # Create a database session and fetch all listings
        session = Session()
        ListingsSample.fetch_all(session)

        # Initial full scrape
        print("-----------------------")
        print("| Initial Full Scrape |")
        print("-----------------------")

        # Run the initial full scrape for "rent" mode
        PropertyGuruInitialScraper.run_scraper(
            mode = "rent",
            desired_pages = 2,
            session = session,
        )

        # # Run the initial full scrape for "buy" mode (optional)
        # PropertyGuruInitialScraper.run_scraper(
        #     mode="buy",
        #     desired_pages=1,
        #     output_file="data/listings_buy.csv"
        # )

    except Exception as e:
        print(f"❌ Error on Main: {e}")
    finally:
        # Close the database session if it was created
        if 'session' in locals():
            session.close()
        print("")