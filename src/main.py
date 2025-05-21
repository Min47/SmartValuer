# src/main.py
from dotenv import dotenv_values
from scraper.initial_full_scrape import PropertyGuruInitialScraper
from sqlalchemy import text
import database
import os
import time

# Allowed values
ALLOWED_MODES = {"Rent", "Buy"}
ALLOWED_UNIT_TYPES = {-1, 0, 1, 2, 3, 4, 5}

def validate_modes(modes):
    for mode in modes:
        if mode not in ALLOWED_MODES:
            raise ValueError(f"Invalid mode: {mode}. Allowed: {ALLOWED_MODES}")

def validate_unit_types(unit_types):
    for ut in unit_types:
        if ut not in ALLOWED_UNIT_TYPES:
            raise ValueError(f"Invalid unit_type: {ut}. Allowed: {ALLOWED_UNIT_TYPES}")

# Load environment variables
def get_env():
    return dotenv_values(".env")

def get_db_config(env):
    return {
        "user": os.environ.get("DATABASE_USER", env.get("DATABASE_USER")),
        "password": os.environ.get("DATABASE_PASSWORD", env.get("DATABASE_PASSWORD")),
        "host": os.environ.get("DATABASE_HOST", env.get("DATABASE_HOST")),
        "port": os.environ.get("DATABASE_PORT", env.get("DATABASE_PORT")),
        "name": os.environ.get("DATABASE_NAME", env.get("DATABASE_NAME")),
    }

def get_modes(env):
    modes = os.environ.get("MODES", env.get("MODES", ""))
    return [m.strip() for m in modes.split(",") if m.strip()]

def get_unit_types(env):
    unit_types = os.environ.get("UNIT_TYPES", env.get("UNIT_TYPES", ""))
    result = []
    for u in unit_types.split(","):
        u = u.strip()
        result.append(int(u))
    return result

# Main
if __name__ == '__main__':
    try:
        # Load environment variables
        env = get_env()
        modes = get_modes(env)
        unit_types = get_unit_types(env)
        db_config = get_db_config(env)

        # Validate user input
        validate_modes(modes)
        validate_unit_types(unit_types)

        # Clear CSV at the start of the run
        filename = os.environ.get("LISTINGS_CSV_PATH", env.get("LISTINGS_CSV_PATH", "data/listings.csv")) # Get CSV path from env or use default
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            pass  # This will clear the file

        # Initialize database with env/config and create session
        database.init_db(db_config)
        session = database.Session()
        session.execute(text("SELECT 1"))
        print("")
        print(f"> Host: {session.bind.url.host}")
        print(f"> Port: {session.bind.url.port}")
        print(f"> User: {session.bind.url.username}")
        print(f"> Database: {session.bind.url.database}")
        print("")

        # # Testing purpose
        modes = ["Rent", "Buy"]
        unit_types = [-1, 0, 5]
        for mode in modes:
            for unit_type in unit_types:
                if mode == "Buy" and unit_type == -1:
                    continue
                # Create a new session for each run
                session = database.Session()
                try:
                    PropertyGuruInitialScraper.run_scraper(
                        mode=mode,
                        unit_type=unit_type,
                        desired_pages=2,
                        session=session,
                        filename=filename
                    )
                finally:
                    session.close()
                # print("Sleeping for 30 seconds...")
                time.sleep(30)  # Sleep for 30 second between different modes and unit types

    except Exception as e:
        print(f"❌ Error on Main: {e}")
    finally:
        # Close the database session if it was created
        if 'session' in locals():
            session.close()
        print("")