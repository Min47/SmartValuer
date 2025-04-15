from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, Date, Enum, Float, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from dotenv import dotenv_values
import os

# Load properties from .env file
env = dotenv_values(".env")
DATABASE_USER = os.environ.get("DATABASE_USER", env.get("DATABASE_USER"))
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD", env.get("DATABASE_PASSWORD"))
DATABASE_HOST = os.environ.get("DATABASE_HOST", env.get("DATABASE_HOST"))
DATABASE_PORT = os.environ.get("DATABASE_PORT", env.get("DATABASE_PORT"))
DATABASE_NAME = os.environ.get("DATABASE_NAME", env.get("DATABASE_NAME"))

# Construct the DATABASE_URL
DATABASE_URL = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)

# Define the ListingsSample table
class ListingsSample(Base):
    __tablename__ = "listings_sample"

    id = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    availability = Column(Text, default=None)
    project_year = Column(Integer, default=None)
    distance_to_closest_MRT = Column(Integer, default=None)
    description = Column(Text, default=None)
    is_verified_listing = Column(Boolean, default=None)
    is_everyone_welcomed = Column(Boolean, default=None)
    listed_date = Column(Date, nullable=False)
    agent_name = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())  # Use func.now() for default timestamp
    property_type = Column(Enum("condo", "landed", "HDB", name="property_type_enum"), nullable=False)
    property_type_text = Column(String(255), default=None)
    ownership_type = Column(Enum("freehold", "leasehold", name="ownership_type_enum"), default=None)
    ownership_type_text = Column(String(255), default=None)
    listing_type = Column(Enum("buy", "rent", name="listing_type_enum"), nullable=False)
    selling_price = Column(Float, default=None)
    selling_price_text = Column(String(255), default=None)
    rent_per_month = Column(Float, default=None)
    rent_per_month_text = Column(String(255), default=None)
    unit_type = Column(Enum("room", "studio", "house", name="unit_type_enum"), nullable=False)
    bedroom_count = Column(Integer, default=None)
    bathroom_count = Column(Integer, default=None)
    floor_size_sqft = Column(Integer, default=None)
    land_size_sqft = Column(Integer, default=None)
    psf_floor = Column(Float, default=None)
    psf_land = Column(Float, default=None)

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @staticmethod
    def fetch_all(session):
        """Fetch all rows from the listings_sample table."""
        try:
            listings = session.query(ListingsSample).all()
            return listings
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []

    @staticmethod
    def fetch_by_id(session, listing_id):
        """Fetch a single row by ID."""
        try:
            listing = session.query(ListingsSample).filter_by(id=listing_id).first()
            return listing
        except Exception as e:
            print(f"Error fetching data by ID: {e}")
            return None

# Add more classes for other tables if needed
# Example:
# class AnotherTable(Base):
#     __tablename__ = "another_table"
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     ...

# Create the tables if they don't exist
Base.metadata.create_all(engine)