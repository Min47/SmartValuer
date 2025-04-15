from database import Session, ListingsSample
from datetime import date as DATE
from sqlalchemy.exc import IntegrityError

# Create a session
session = Session()

# Add a new listing
new_listing = ListingsSample(
    listing_id="L12345",  # Unique identifier
    title="Luxury Condo",
    address="123 Main Street",
    url="https://example.com/listing",
    listed_date=DATE.today(),
    agent_name="John Doe",
    property_type="condo",
    listing_type="buy",
    unit_type="studio",
    selling_price=1200000.00,
    bedroom_count=2,
    bathroom_count=2,
    floor_size_sqft=1000
)

try:
    session.add(new_listing)
    session.commit()
    print("New listing added successfully!")
except IntegrityError as e:
    session.rollback()  # Rollback the transaction to avoid locking issues
    print(f"Error: Could not add listing. Reason: {e.orig}")
finally:
    # Close the session
    session.close()

# Create a session
session = Session()

# Fetch all listings
listings = ListingsSample.fetch_all(session)
for listing in listings:
    print(f"Title: {listing.title}, Price: {listing.selling_price}, Type: {listing.property_type}")

# Close the session
session.close()