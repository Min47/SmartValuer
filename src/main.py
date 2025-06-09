# src/main.py
from dotenv import dotenv_values
from scraper.scraper import PropertyGuruScraper
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
        self.run_listings = self.get_env_bool("RUN_LISTINGS", default="true")
        self.run_details = self.get_env_bool("RUN_DETAILS", default="true")
        self.listings_desired_pages = None if self.get_env_var("LISTINGS_DESIRED_PAGES", "2") is None else int(self.get_env_var("LISTINGS_DESIRED_PAGES", "2"))
        self.details_max_scrape = None if self.get_env_var("DETAILS_MAX_SCRAPE", "5") is None else int(self.get_env_var("DETAILS_MAX_SCRAPE", "5"))
        self.last_posted = int(self.get_env_var("LAST_POSTED", "2"))

        self.validate_input()
        self.setup_csvs()
        self.session = self.setup_database()

    def get_env_var(self, key, default=None):
        val = os.environ.get(key, self.env.get(key, default))
        if val is not None and str(val).lower() == "none":
            return None
        return val
    
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
        def create_and_cleanup_csv(env_key, default_path):
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            base_path = self.get_env_var(env_key, default_path)
            root, ext = os.path.splitext(base_path)
            path = f"{root}_{timestamp}{ext}"
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, 'w', encoding='utf-8').close()

            # Cleanup old CSVs for this base path
            files = [f for f in os.listdir(os.path.dirname(root))
                     if f.startswith(os.path.basename(root)) and f.endswith('.csv')]
            files.sort(reverse=True)
            for file in files[10:]:
                try:
                    os.remove(os.path.join(os.path.dirname(root), file))
                except Exception as e:
                    print(f"❌ Error Deleting old CSV file {file}: {e}")
            return path
    
        if self.run_listings:
            self.properties_csv_path = create_and_cleanup_csv("PROPERTIES_CSV_PATH", "properties.csv")
        if self.run_details:
            self.details_csv_path = create_and_cleanup_csv("DETAILS_CSV_PATH", "details.csv")

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

        # --- Scraper Phase --- #
        if prep.run_listings:
            for mode in prep.modes:
                for unit_type in prep.unit_types:
                    if mode == "Buy" and unit_type == -1:
                        continue
                    with database.Session() as sess:
                        scraper = ScraperUtils(session=sess, mode=mode, unit_type=unit_type, last_posted=prep.last_posted)
                        PropertyGuruScraper.run_scraper_listings(
                            scraper=scraper, 
                            desired_pages=prep.listings_desired_pages,
                            listings_csv_path=prep.properties_csv_path
                        )
                    time.sleep(30)

        if prep.run_details:
            with database.Session() as sess:
                scraper = ScraperUtils(session=sess, mode=None, unit_type=None, last_posted=None)
                PropertyGuruScraper.run_scraper_details(
                    scraper=scraper, 
                    max_scrape=prep.details_max_scrape,
                    details_csv_path=prep.details_csv_path
                )
    except Exception as e:
        print(f"❌ Error on Main: {e}")
    finally:
        if 'session' in locals():
            prep.session.close()