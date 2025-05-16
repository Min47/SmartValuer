from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, Date, Enum, Float, TIMESTAMP, text
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from datetime import date
from dotenv import dotenv_values
import os
import pymysql
import random

# Load properties from .env file
env = dotenv_values(".env")
DATABASE_USER = os.environ.get("DATABASE_USER", env.get("DATABASE_USER"))
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD", env.get("DATABASE_PASSWORD"))
DATABASE_HOST = os.environ.get("DATABASE_HOST", env.get("DATABASE_HOST"))
DATABASE_PORT = os.environ.get("DATABASE_PORT", env.get("DATABASE_PORT"))
DATABASE_NAME = os.environ.get("DATABASE_NAME", env.get("DATABASE_NAME"))

# --- RAW TABLE CREATION (MySQL) FROM SQL FILE ---
sql_file_path = os.path.join(os.path.dirname(__file__), "..", "sql", "create_table.sql")
sql_file_path = os.path.abspath(sql_file_path)
with open(sql_file_path, "r", encoding="utf-8") as f:
    create_table_sql = f.read()

connection = pymysql.connect(
    host=DATABASE_HOST,
    user=DATABASE_USER,
    password=DATABASE_PASSWORD,
    database=DATABASE_NAME,
    port=int(DATABASE_PORT)
)

# Create a cursor object
with connection.cursor() as cursor:
    cursor.execute(create_table_sql)

connection.commit()
connection.close()
# --- END RAW TABLE CREATION ---

# Construct the DATABASE_URL without specifying the database name
BASE_DATABASE_URL = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}"

# Create an engine to connect to the server
base_engine = create_engine(BASE_DATABASE_URL)

# Check if the database exists, and create it if it doesn't
with base_engine.connect() as connection:
    result = connection.execute(text(f"SHOW DATABASES LIKE '{DATABASE_NAME}';"))
    if not result.fetchone():
        connection.execute(text(f"CREATE DATABASE {DATABASE_NAME};"))
        print(f"Database '{DATABASE_NAME}' created.")

# Construct the full DATABASE_URL with the database name
DATABASE_URL = f"{BASE_DATABASE_URL}/{DATABASE_NAME}"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)

# Define the Listings table
class Listings(Base):
    __tablename__ = "listings"

    # Listings
    id = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(String(255), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    address = Column(String(255))
    listing_url = Column(Text, nullable=False)
    availability = Column(Text, default=None)
    project_year = Column(Integer, default=None)
    closest_mrt = Column(String(255), default=None)
    distance_to_closest_mrt = Column(Integer, default=None)
    is_verified_listing = Column(Boolean, default=None)
    is_everyone_welcomed = Column(Boolean, default=None)
    listed_date = Column(Date, default=None)
    agent_name = Column(String(255))
    agent_rating = Column(Float, default=None)
    listing_type = Column(Enum("Buy", "Rent", name="listing_type_enum"), nullable=False)
    unit_type = Column(Enum("Room", "Studio", "1 Bedroom", "2 Bedroom", "3 Bedroom", "4 Bedroom", "5+ Bedroom", name="unit_type_enum"), nullable=False)
    selling_price = Column(Float, default=None)
    selling_price_text = Column(String(255), default=None)

    # Property Details
    description = Column(Text, default=None)
    property_type = Column(Enum("condo", "landed", "HDB", name="property_type_enum"), default=None)
    property_type_text = Column(String(255), default=None)
    ownership_type = Column(Enum("freehold", "leasehold", name="ownership_type_enum"), default=None)
    ownership_type_text = Column(String(255), default=None)
    bedroom_count = Column(Integer, default=None)
    bathroom_count = Column(Integer, default=None)
    floor_size_sqft = Column(Integer, default=None)
    land_size_sqft = Column(Integer, default=None)
    psf_floor = Column(Float, default=None)
    psf_land = Column(Float, default=None)

    # Datetime
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())  # Use func.now() for default timestamp
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())  # Use func.now() for default timestamp

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        # # Run validation checks
        # self.validate()

    def __repr__(self):
        return f"<Listing(id={self.id}, title={self.title}, address={self.address}>"
    
    def validate(self):
        if not self.listing_id:
            raise ValueError("listing_id cannot be empty.")
        if not self.title:
            raise ValueError("title cannot be empty.")
        if not self.listing_url:
            raise ValueError("listing_url cannot be empty.")
        if not self.agent_name:
            raise ValueError("agent_name cannot be empty.")
        if not self.property_type:
            raise ValueError("property_type cannot be empty.")
        if not self.listing_type:
            raise ValueError("listing_type cannot be empty.")
        if not self.unit_type:
            raise ValueError("unit_type cannot be empty.")
        if self.agent_rating is not None and (self.agent_rating < 0 or self.agent_rating > 5):
            raise ValueError("agent_rating must be between 0 and 5.")
        if self.selling_price is not None and self.selling_price < 0:
            raise ValueError("selling_price cannot be negative.")
        if self.floor_size_sqft is not None and self.floor_size_sqft < 0:
            raise ValueError("floor_size_sqft cannot be negative.")
        if self.land_size_sqft is not None and self.land_size_sqft < 0:
            raise ValueError("land_size_sqft cannot be negative.")
        if self.bedroom_count is not None and self.bedroom_count < 0:
            raise ValueError("bedroom_count cannot be negative.")
        if self.bathroom_count is not None and self.bathroom_count < 0:
            raise ValueError("bathroom_count cannot be negative.")
        if self.psf_floor is not None and self.psf_floor < 0:
            raise ValueError("psf_floor cannot be negative.")
        if self.psf_land is not None and self.psf_land < 0:
            raise ValueError("psf_land cannot be negative.")
        if self.project_year is not None and self.project_year < 0:
            raise ValueError("project_year cannot be negative.")
        if self.distance_to_closest_mrt is not None and self.distance_to_closest_mrt < 0:
            raise ValueError("distance_to_closest_mrt cannot be negative.")
        if self.created_at is not None and not isinstance(self.created_at, date):
            raise ValueError("created_at must be a date object.")
        if self.availability is not None and not isinstance(self.availability, str):
            raise ValueError("availability must be a string.")
        if self.is_verified_listing is not None and not isinstance(self.is_verified_listing, bool):
            raise ValueError("is_verified_listing must be a boolean.")
        if self.is_everyone_welcomed is not None and not isinstance(self.is_everyone_welcomed, bool):
            raise ValueError("is_everyone_welcomed must be a boolean.")

    @staticmethod
    def fetch_all(session):
        print("= Fetching All Listings:")

        try:
            listings = session.query(Listings).all()
            for listing in listings:
                print(f"> Title: {listing.title}, Price: {listing.selling_price}, Listing_Type: {listing.listing_type}, Unit_Type: {listing.unit_type}, Distance_to_Closest_MRT: {listing.distance_to_closest_mrt}")
            print("")
            return listings
        except Exception as e:
            print(f"> Error: Fetching All Data: {e}\n")
            return []

    @staticmethod
    def fetch_by_id(session, listing_id):
        print(f"= Fetching Listing by ID: {listing_id}")

        try:
            listing = session.query(Listings).filter_by(id=listing_id).first()
            if listing:
                print(f"> Title: {listing.title}, Price: {listing.selling_price}, Listing_Type: {listing.listing_type}, Unit_Type: {listing.unit_type}")
            else:
                print(f"> No listing found with ID: {listing_id}")
            print("")
            return listing
        except Exception as e:
            print(f"> Error: Fetching Data by ID: {e}\n")
            return None

    @classmethod
    def upsert_listing(cls, session, **kwargs):
        # print(f"= Upsert New Listing: {kwargs.get('title', 'Unknown')}")
        try:
            # 1. Try to fetch the existing row by unique key
            existing = session.query(cls).filter_by(listing_id=kwargs.get("listing_id")).first()

            if existing:
                # 2. Compare each field (skip id, created_at, updated_at)
                changed = False
                for col in cls.__table__.columns.keys():
                    if col in ["id", "created_at", "updated_at"]:
                        continue
                    if col in kwargs and getattr(existing, col) != kwargs[col]:
                        changed = True
                        break

                if changed:
                    # 3. Only update if something changed
                    for col in cls.__table__.columns.keys():
                        if col in ["id", "created_at", "updated_at"]:
                            continue
                        if col in kwargs:
                            setattr(existing, col, kwargs[col])
                    existing.updated_at = func.now()
                    session.commit()
                    print(f"> Update | ID: {kwargs.get('listing_id', 'Unknown')}, Title: {kwargs.get('title', 'Unknown')}")
                    return "update"
                else:
                    print(f"> Ignore | ID: {kwargs.get('listing_id', 'Unknown')}, Title: {kwargs.get('title', 'Unknown')} ")
                    return "ignore"
            else:
                # Insert new row
                new_listing = cls(**kwargs)
                session.add(new_listing)
                session.commit()
                print(f"> Insert | ID: {kwargs.get('listing_id', 'Unknown')}, Title: {kwargs.get('title', 'Unknown')}")
                return "insert"
        except IntegrityError as e:
            session.rollback()
            print(f"> Error: Could Not Upsert Listing. Reason: {e.orig}\n")
        finally:
            session.close()

    @classmethod
    def batch_upsert_listings(cls, session, listings):
        print(f"= Batch Upsert Listings:")
        insert_count = 0
        update_count = 0
        ignore_count = 0
        total_insert = getattr(cls, "_total_insert", 0)
        total_update = getattr(cls, "_total_update", 0)
        total_ignore = getattr(cls, "_total_ignore", 0)

        try:
            # Capture the output of upsert_listing
            for listing in listings:
                result = cls.upsert_listing(session, **listing)
                if result == "insert":
                    insert_count += 1
                    total_insert += 1
                elif result == "update":
                    update_count += 1
                    total_update += 1
                elif result == "ignore":
                    ignore_count += 1
                    total_ignore += 1

            # Store cumulative totals as class attributes
            cls._total_insert = total_insert
            cls._total_update = total_update
            cls._total_ignore = total_ignore

            # Print cumulative counts
            print(f"= Counts | Insert: {insert_count} ({total_insert}) | Update: {update_count} ({total_update}) | Ignore: {ignore_count} ({total_ignore})")
        except Exception as e:
            session.rollback()
            print(f"> Error: Batch Upsert Failed. Reason: {e}\n")
        finally:
            session.close()

    @classmethod
    def delete_listing(cls, session, listing_id):
        print(f"= Deleting Listing with ID: {listing_id}")

        try:
            listing = session.query(cls).filter_by(listing_id=listing_id).first()
            if listing:
                session.delete(listing)
                session.commit()
                print(f"> Listing with listing_id {listing_id} deleted successfully!")
            else:
                print(f"> No listing found with listing_id {listing_id}.")
            print("")
        except Exception as e:
            session.rollback()
            print(f"> Error: Could Not Delete Listing. Reason: {e}\n")
        finally:
            session.close()

    @classmethod
    def test_listing(cls):
        # Create a session
        session = Session()

        try:
            # Generate a random 8-digit listing_id
            random_listing_id = f"{random.randint(10000000, 99999999)}"

            # Use the upsert_listing class method to add a new listing
            cls.upsert_listing(
                session,
                listing_id=random_listing_id,  # Random 8-digit identifier
                title="Luxury Condo",
                address="123 Main Street",
                listing_url="https://example.com/listing",
                listed_date=date.today(),
                agent_name="John Doe",
                property_type="condo",
                listing_type="Buy",
                unit_type="studio",
                selling_price=1200000.00,
                bedroom_count=2,
                bathroom_count=2,
                floor_size_sqft=1000
            )

            # Delete the test listing using the random listing_id
            cls.delete_listing(session, listing_id=random_listing_id)

        except Exception as e:
            session.rollback()
            print(f"Error during test_listing: {e}")
        finally:
            # Close the session
            session.close()