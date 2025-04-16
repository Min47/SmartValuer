from database import Session, ListingsSample

# Create a session
session = Session()

# Fetch all listings
ListingsSample.test_listing()
listings = ListingsSample.fetch_all(session)
for listing in listings:
    print(f"Title: {listing.title}, Price: {listing.selling_price}, Type: {listing.property_type}")

# Close the session
session.close()