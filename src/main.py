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

        # Run the initial full scrape
        # Temporarily set to "Rent" mode and "Room" unit type for testing
        PropertyGuruInitialScraper.run_scraper(
            mode = "Rent", # ["Buy", "Rent"]
            unit_type = -1, # [-1 for 'Room', 0 for 'Studio', 1 for '1 Bedroom', 2 for '2 Bedroom', 3 for '3 Bedroom', 4 for '4 Bedroom', 5 for '5+ Bedroom']
            desired_pages = 2,
            session = session,
        )

    except Exception as e:
        print(f"❌ Error on Main: {e}")
    finally:
        # Close the database session if it was created
        if 'session' in locals():
            session.close()
        print("")