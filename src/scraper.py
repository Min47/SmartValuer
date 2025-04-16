from database import Session, ListingsSample

# Create a session
session = Session()

# Fetch all listings
# ListingsSample.test_listing()
ListingsSample.fetch_all(session)
# Close the session
session.close()