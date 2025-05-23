# src/main.py
from dotenv import dotenv_values
from scraper.initial_full_scrape import PropertyGuruInitialScraper
from scraper.scraper_utils import ScraperUtils
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
        filename = os.environ.get("PROPERTIES_CSV_PATH", env.get("PROPERTIES_CSV_PATH", "data/properties.csv")) # Get CSV path from env or use default
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            pass  # This will clear the file

        # --- Initialize database with env/config and create session --- #
        database.init_db(db_config)
        session = database.Session()
        session.execute(text("SELECT 1"))

        # --- Kill other MySQL sessions --- #
        current_id = session.execute(text("SELECT CONNECTION_ID()")).scalar()
        processes = session.execute(text("SELECT ID, USER FROM performance_schema.processlist")).fetchall()
        for proc in processes:
            pid = proc[0]
            user = proc[1]
            if pid != current_id and user == session.bind.url.username:
                try:
                    session.execute(text(f"KILL {pid}"))
                    # print(f"Killed Session: {pid} (User: {user})")
                except Exception as e:
                    # print(f"Could Not Kill Session: {pid} (User: {user}) - {e}")
                    pass
        session.commit()

        # --- Print database connection details --- #
        print("")
        print(f"> Host: {session.bind.url.host}")
        print(f"> Port: {session.bind.url.port}")
        print(f"> User: {session.bind.url.username}")
        print(f"> Database: {session.bind.url.database}")
        print("")

        # [Initial] Scraper Listings #
        modes = ["Rent", "Buy"]
        unit_types = [-1, 0, 5]
        for mode in modes:
            for unit_type in unit_types:
                if mode == "Buy" and unit_type == -1:
                    continue
                # Create a new session for each run
                session = database.Session()
                try:
                    scraper = ScraperUtils(session=session, mode=mode, unit_type=unit_type)
                    PropertyGuruInitialScraper.run_scraper_listings(
                        scraper=scraper,
                        desired_pages=2,
                        filename=filename
                    )
                finally:
                    session.close()
                # print("Sleeping for 30 seconds...")
                time.sleep(30)  # Sleep for 30 second between different modes and unit types

        # [Initial] Scraper Details #
        session = database.Session()
        try:
            scraper = ScraperUtils(session=session, mode=None, unit_type=None)
            PropertyGuruInitialScraper.run_scraper_details(
                scraper=scraper,
                filename=filename
            )
        finally:
            session.close()

    except Exception as e:
        print(f"❌ Error on Main: {e}")
    finally:
        # Close the database session if it was created
        if 'session' in locals():
            session.close()
        print("")