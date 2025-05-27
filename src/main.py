# src/main.py
from dotenv import dotenv_values
from scraper.initial_full_scrape import PropertyGuruInitialScraper
from scraper.scraper_utils import ScraperUtils
from sqlalchemy import text
import database
import datetime
import os
import time

class Prep:
    # Allowed values
    ALLOWED_MODES = {"Rent", "Buy"}
    ALLOWED_UNIT_TYPES = {-1, 0, 1, 2, 3, 4, 5}

    def __init__(self):
        self.env = dotenv_values(".env")
        self.db_config = self.get_db_config()
        self.modes = self.parse_modes()
        self.unit_types = self.parse_unit_types()
        self.run_initial_listings = self.get_env_bool("RUN_INITIAL_LISTINGS", default="true")
        self.run_initial_details = self.get_env_bool("RUN_INITIAL_DETAILS", default="true")

        self.validate_input()
        self.setup_csvs()
        self.session = self.setup_database()

    def get_env_var(self, key, default=None):
        return os.environ.get(key, self.env.get(key, default))
    
    def get_env_bool(self, key, default="false"):
        return self.get_env_var(key, default).lower() == "true"
    
    def get_db_config(self):
        return {
            "user": self.get_env_var("DATABASE_USER"),
            "password": self.get_env_var("DATABASE_PASSWORD"),
            "host": self.get_env_var("DATABASE_HOST"),
            "port": self.get_env_var("DATABASE_PORT"),
            "name": self.get_env_var("DATABASE_NAME"),
        }
    
    def parse_modes(self):
        return [m.strip() for m in self.get_env_var("MODES", "").split(",") if m.strip()]
    
    def parse_unit_types(self):
        return [int(u.strip()) for u in self.get_env_var("UNIT_TYPES", "").split(",") if u.strip()]

    def validate_input(self):
        for mode in self.modes:
            if mode not in self.ALLOWED_MODES:
                raise ValueError(f"Invalid mode: {mode}. Allowed: {self.ALLOWED_MODES}")
        for unit_type in self.unit_types:
            if unit_type not in self.ALLOWED_UNIT_TYPES:
                raise ValueError(f"Invalid unit_type: {unit_type}. Allowed: {self.ALLOWED_UNIT_TYPES}")
            
    def setup_csvs(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.run_initial_listings:
            base_path = self.get_env_var("PROPERTIES_CSV_PATH", "data/properties_csv.csv")
            root, ext = os.path.splitext(base_path)
            path = f"{root}_{timestamp}{ext}"
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, 'w', encoding='utf-8').close()
            self.properties_csv_path = path
        if self.run_initial_details:
            base_path = self.get_env_var("DETAILS_CSV_PATH", "data/details_csv.csv")
            root, ext = os.path.splitext(base_path)
            path = f"{root}_{timestamp}{ext}"
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, 'w', encoding='utf-8').close()
            self.details_csv_path = path
    
    def setup_database(self):
        database.init_db(self.db_config)
        session = database.Session()
        session.execute(text("SELECT 1"))

        current_id = session.execute(text("SELECT CONNECTION_ID()")).scalar()
        for pid, user in session.execute(text("SELECT ID, USER FROM performance_schema.processlist")):
            if pid != current_id and user == session.bind.url.username:
                try:
                    session.execute(text(f"KILL {pid}"))
                except Exception:
                    pass
        session.commit()

        print(f"\n> Host: {session.bind.url.host}")
        print(f"> Port: {session.bind.url.port}")
        print(f"> User: {session.bind.url.username}")
        print(f"> Database: {session.bind.url.database}\n")
        return session

# Main
if __name__ == '__main__':
    try:
        # --- Preparation Phase --- #
        prep = Prep()

        # --- Initial Scraper Phase --- #
        if prep.run_initial_listings:
            for mode in prep.modes:
                for unit_type in prep.unit_types:
                    if mode == "Buy" and unit_type == -1:
                        continue
                    with database.Session() as sess:
                        scraper = ScraperUtils(session=sess, mode=mode, unit_type=unit_type)
                        PropertyGuruInitialScraper.run_scraper_listings(
                            scraper=scraper, 
                            desired_pages=2,
                            listings_csv_path=prep.properties_csv_path
                        )
                    time.sleep(30)

        if prep.run_initial_details:
            with database.Session() as sess:
                scraper = ScraperUtils(session=sess, mode=None, unit_type=None)
                PropertyGuruInitialScraper.run_scraper_details(
                    scraper=scraper, 
                    max_scrape=5,
                    details_csv_path=prep.details_csv_path
                )
    except Exception as e:
        print(f"❌ Error on Main: {e}")
    finally:
        if 'session' in locals():
            prep.session.close()