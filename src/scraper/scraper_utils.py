# src/scraper/scraper_utils.py
from database import Properties
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from seleniumbase import SB
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import csv
import os
import random
import re
import time

class ScraperUtils:
    def __init__(self, session, mode="Rent", unit_type=-1, last_posted=2):
        self.session = session
        self.mode = mode
        self.unit_type = unit_type
        self.last_posted = last_posted
        self.cur_page_listings = []
        self.csv_listings = []
        self.cur_details = {}
        self.csv_details = []

    def scrape_listings(self, desired_pages=2):
        cur_page = 1
        max_pages = 99  # Temporary default value for maximum pages

        # Filters
        lines = [
            f"= Scraping Mode: {self.mode}",
            f"= Unit Type: {'Room' if self.unit_type == -1 else 'Studio' if self.unit_type == 0 else f'{self.unit_type} Bedroom' if self.unit_type!= 5 else f'{self.unit_type} Bedroom+'}",
            f"= Last Posted: {self.last_posted} Days Ago" if self.last_posted is not None else "= Last Posted: None",
            f"= Desired Pages: {desired_pages if desired_pages is not None else 'All'}"
        ]
        max_len = max(len(line) for line in lines)
        header = "┌" + "─" * (max_len + 2) + "┐"
        footer = "└" + "─" * (max_len + 2) + "┘"
        print(header)
        for line in lines:
            print(f"| {line.ljust(max_len)} |")
        print(footer)
        print("")

        # Run the scraper with a context manager
        with SB(uc=True, xvfb=True, locale="en", uc_cdp_events=True) as sb:
            while True:
                try:
                    # Page
                    page_line = f"Page {cur_page}"
                    page_header = "┌" + "─" * (len(page_line) + 2) + "┐"
                    page_footer = "└" + "─" * (len(page_line) + 2) + "┘"
                    print(page_header)
                    print(f"| {page_line} |")
                    print(page_footer)
                    
                    # Construct the URL based on the filters
                    if self.mode == "Rent":
                        if self.last_posted is None:
                            url = f"https://www.propertyguru.com.sg/property-for-rent/{cur_page}?listingType=rent&cur_page={cur_page}&isCommercial=false&sort=date&order=desc&bedrooms={self.unit_type}"
                        else:
                            url = f"https://www.propertyguru.com.sg/property-for-rent/{cur_page}?listingType=rent&cur_page={cur_page}&isCommercial=false&sort=date&order=desc&bedrooms={self.unit_type}&lastPosted={self.last_posted}"
                    elif self.mode == "Buy":
                        if self.last_posted is None:
                            url = f"https://www.propertyguru.com.sg/property-for-sale/{cur_page}?listingType=sale&cur_page={cur_page}&isCommercial=false&sort=date&order=desc&bedrooms={self.unit_type}"
                        else:
                            url = f"https://www.propertyguru.com.sg/property-for-sale/{cur_page}?listingType=sale&cur_page={cur_page}&isCommercial=false&sort=date&order=desc&bedrooms={self.unit_type}&lastPosted={self.last_posted}"
                    print(f"> URL: {url}")
                    
                    # Solve captcha
                    sb.uc_open_with_reconnect(url, 4)
                    sb.uc_gui_click_captcha()
                    sb.sleep(2)

                    # # Save the HTML content to a file for debugging (optional)
                    # with open(f"data/Page_{cur_page}.html", "w", encoding="utf-8") as f:
                    #     f.write(sb.get_page_source())

                    # Total Properties #
                    # Show the total properties found
                    total_properties = sb.find_element(By.XPATH, './/h1[@class="page-title"]').text
                    # Extract the number at the start (with commas)
                    match = re.match(r"([\d,]+)", total_properties)
                    if match:
                        num_properties = int(match.group(1).replace(",", ""))
                        print(f"> Total Properties: {num_properties}")
                    else:
                        print(f"> Total Properties not Found in Text: '{total_properties}'")

                    # Total Listings For Current Page #
                    # Find the listing cards on the page
                    cards = sb.find_elements('//*[@class="listing-card-banner-root"]')
                    if not cards:
                        print(f"> Listings (Current Page): 0")
                        print("")
                        break
                    else:
                        print(f"> Listings (Current Page): {len(cards)}")
                        print("")

                    # Listings Info #
                    # Extract the listing information from the cards
                    listings_info = ListingsInfo(cards, self.mode, self.unit_type)
                    self.cur_page_listings = listings_info.cur_page_listings
                    self.csv_listings.append(self.cur_page_listings)

                    # Database #
                    # Save the listings to the database
                    self.save_to_db_listings(self.session)
                    print("")

                    # Pagination #
                    # Dynamically determine the maximum number of pages
                    page_items = sb.find_elements('//li[@class="page-item"]')
                    max_pages = cur_page  # Default fallback

                    # Try to find the last numeric page number (skip "Next", "»", etc.)
                    if page_items:
                        last_page_number = None
                        for item in reversed(page_items):
                            text = item.text.strip()
                            if text.isdigit():
                                last_page_number = text
                                break
                        if last_page_number is not None:
                            max_pages = int(last_page_number)
                            print(f"= Maximum Pages: {max_pages}")
                        else:
                            print("= Maximum Pages: Not Found (no numeric page item)")
                    else:
                        print("= Maximum Pages: Not Found (no page items)")
                    # Also print the desired pages if provided
                    if desired_pages is not None:
                        print(f"= Desired Pages: {desired_pages}")

                    # Check if reached the maximum page limit
                    if cur_page >= max_pages:
                        print(f"> Reached Maximum Page Limit: {max_pages}")
                        print("")
                        break
                    # Check if reached the desired page limit
                    if desired_pages is not None and cur_page >= desired_pages:
                        print(f"> Reached Desired Page Limit: {desired_pages}")
                        print("")
                        break

                    # Increment the page number
                    cur_page += 1
                    time.sleep(random.uniform(2, 5))
                    print("")
                except Exception as e:
                    print(f"❌ Error on Page {cur_page}: {e}")
                    # Take a screenshot for debugging
                    sb.save_screenshot(f"data/Listings_Error_Page_{cur_page}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                    # Save the page source for debugging
                    with open(f"data/Error_Page_{cur_page}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html", "w", encoding="utf-8") as f:
                        f.write(sb.get_page_source())
                    break

    def scrape_details(self, max_scrape=5):
        # Database Query #
        properties_pending = self.session.query(Properties).filter_by(details_fetched=False).all()
        if max_scrape is None:
            properties = properties_pending  # Scrape all
        else:
            properties = properties_pending[:max_scrape]  # Scrape up to max_scrape

        # Lines #
        lines = [
            "= Scraping Details",
            f"= Properties Pending: {len(properties_pending)}",
            f"= Properties to Scrape: {len(properties)}",
        ]
        max_len = max(len(line) for line in lines)
        header = "┌" + "─" * (max_len + 2) + "┐"
        footer = "└" + "─" * (max_len + 2) + "┘"
        print(header)
        for line in lines:
            print(f"| {line.ljust(max_len)} |")
        print(footer)
        print("")
        if not properties:
            return
        
        # Run the scraper with a context manager
        with SB(uc=True, xvfb=True, locale="en", uc_cdp_events=True) as sb:
            for idx, prop in enumerate(properties, 1):
                try:
                    print(f"= [{idx}/{len(properties)}] ID: {prop.property_id} | Title: {prop.title} | URL: {prop.property_url}")
                    sb.uc_open_with_reconnect(prop.property_url, 4)
                    sb.uc_gui_click_captcha()
                    sb.sleep(0.5)

                    # # Save the HTML content to a file for debugging (optional)
                    # with open(f"data/Details_{idx}.html", "w", encoding="utf-8") as f:
                    #     f.write(sb.get_page_source())

                    # Checking if we are in the details page instead of the listings page #
                    if not sb.find_elements('.//div[@class="property-snapshot-section"]'):
                        print("= Details Page Not Found")
                        Properties.update_field_value(
                            property_id=prop.property_id, 
                            field_name="details_fetched",
                            new_value=True
                        )
                        continue

                    # Details Info #
                    # Scrape the details from the page
                    details_info = DetailsInfo(sb)
                    DETAIL_COLUMNS = details_info.DETAIL_COLUMNS
                    
                    # 1. Initialize cur_details with all columns from prop
                    self.cur_details = {col: getattr(prop, col) for col in prop.__table__.columns.keys()}
                    self.csv_details.append(self.cur_details)
                    
                    # 2. Update only the detail columns with freshly scraped values
                    for col in DETAIL_COLUMNS:
                        if col in details_info.details:
                            self.cur_details[col] = details_info.details[col]

                    # Database #
                    self.save_to_db_details(DETAIL_COLUMNS)
                    print("")

                except Exception as e:
                    print(f"❌ Error Scraping Details: {e}")
                    print("")
                    continue

    def save_to_db_listings(self, session):
        try:
            Properties.batch_upsert_listings(session, self.cur_page_listings)
        except Exception as e:
            print(f"❌ Error Saving to DB: {e}")

    def save_listings_to_csv(self, path):
        # Flatten the list of lists into a single list of dicts
        all_rows = [item for sublist in self.csv_listings for item in sublist]
        if not all_rows:
            return
        fieldnames = list(all_rows[0].keys())
        file_exists = os.path.isfile(path)
        with open(path, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists or os.stat(path).st_size == 0:
                writer.writeheader()
            for row in all_rows:
                writer.writerow(row)

    def save_to_db_details(self, DETAIL_COLUMNS):
        try:
            Properties.update_details(self.cur_details, DETAIL_COLUMNS)
        except Exception as e:
            print(f"❌ Error Saving to DB: {e}")

    def save_details_to_csv(self, path):
        if not self.csv_details:
            return
        else:
            fieldnames = list(self.csv_details[0].keys())
            file_exists = os.path.isfile(path)
        with open(path, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists or os.stat(path).st_size == 0:
                writer.writeheader()
            for row in self.csv_details:
                writer.writerow(row)

class ListingsInfo:
    def __init__(self, cards, mode, unit_type):
        self.mode = mode
        self.unit_type = unit_type
        self.cur_page_listings = []
        self.print_output = True
        self.extract_listings(cards)

    def extract_listings(self, cards):
        # List of (field_name, method_name) pairs
        fields = [
            # ("outer_html", "get_outer_html"),
            ("property_id", "get_property_id"),
            ("title", "get_title"),
            ("address", "get_address"),
            ("property_url", "get_property_url"),
            ("availability", "get_availability"),
            ("project_year", "get_project_year"),
            ("closest_mrt", "get_closest_mrt"),
            ("distance_to_closest_mrt", "get_distance_to_closest_mrt"),
            ("is_verified_property", "get_is_verified_property"),
            ("is_everyone_welcomed", "get_is_everyone_welcomed"),
            ("listed_date", "get_listed_date"),
            ("agent_name", "get_agent_name"),
            ("agent_rating", "get_agent_rating"),
            ("property_selling_type", "get_property_selling_type"),
            ("unit_type", "get_unit_type"),
            ("selling_price", "get_selling_price"),
            ("selling_price_text", "get_selling_price_text"),
        ]

        # Iterate through each card and extract the required information
        for card in cards:
            try:
                # Listing dictionary to store the extracted information
                listing = {}

                # # Call the method dynamically
                for field, method in fields:
                    if field in ["property_selling_type", "unit_type"]:
                        # For property_selling_type and unit_type, use the class attributes
                        listing[field] = getattr(self, method)()
                    else:
                        # For other fields, call the respective method
                        listing[field] = getattr(self, method)(card)

                # Print the extracted information for debugging
                if self.print_output:
                    print("= Card Info:")
                    printed = set()
                    for field, method in fields:
                        if field in ["property_id", "property_url"] and "property_id_url" not in printed:
                            print(f"> Property ID: {listing['property_id']} | URL: {listing['property_url']}")
                            printed.add("property_id_url")
                        elif field in ["closest_mrt", "distance_to_closest_mrt"] and "closest_mrt" not in printed:
                            print(f"> Closest MRT: {listing['closest_mrt']} ({listing['distance_to_closest_mrt']} m)")
                            printed.add("closest_mrt")
                        elif field in ["agent_name", "agent_rating"] and "agent" not in printed:
                            print(f"> Agent: {listing['agent_name']} | Rating: {listing['agent_rating']}")
                            printed.add("agent")
                        elif field in ["selling_price", "selling_price_text"] and "selling_price" not in printed:
                            if listing['selling_price'] is not None:
                                print(f"> Selling Price: {listing['selling_price']:.2f} ({listing['selling_price_text']})")
                            else:
                                print(f"> Selling Price: {listing['selling_price']} ({listing['selling_price_text']})")
                            printed.add("selling_price")
                        elif field not in [
                            "property_id", "property_url",
                            "closest_mrt", "distance_to_closest_mrt",
                            "agent_name", "agent_rating",
                            "selling_price", "selling_price_text"
                        ]:
                            display_name = field.replace("_", " ").title()
                            print(f"> {display_name}: {listing[field]}")
                    print("")

                # Add the extracted listing information to the list
                self.cur_page_listings.append(listing)
            except Exception as e:
                print(f"❌ Error on Listings Cards Info Extraction: {e}")
                print("")

    def get_outer_html(self, card):
        try:
            outer_html = card.get_attribute('outerHTML')
        except Exception:
            outer_html = None
        finally:
            return outer_html
    
    def get_property_id(self, card):
        try:
            property_id_element = card.find_element(By.XPATH, './/div[@data-listing-id]')
            property_id = property_id_element.get_attribute('data-listing-id')
        except Exception:
            property_id = None
        finally:
            return property_id
        
    def get_title(self, card):
        try:
            title = card.find_element(By.XPATH, './/h3[@class="listing-title"]').text
        except Exception:
            title = None
        finally:
            return title
        
    def get_address(self, card):
        try:
            address = card.find_element(By.XPATH, './/div[@class="listing-address"]').text
        except Exception:
            address = None
        finally:
            return address
        
    def get_property_url(self, card):
        try:
            property_url = card.find_element(By.XPATH, './/a[@class="listing-card-link"]').get_attribute('href')
        except Exception:
            property_url = None
        finally:
            return property_url
        
    def get_availability(self, card):
        try:
            availability = card.find_element(By.XPATH, './/span[@da-id="lc-price-badge"]').text
        except Exception:
            availability = None
        finally:
            return availability
        
    def get_project_year(self, card):
        try:
            year_text = card.find_element(By.XPATH, './/span[@da-id="lc-info-badge"]').text
            # Look for 'Built: xxxx' or 'New Project: xxxx'
            match = re.search(r'(Built:|New Project:)\s*(\d{4})', year_text)
            project_year = int(match.group(2).strip()) if match else None
        except Exception:
            project_year = None
        finally:
            return project_year
        
    def get_closest_mrt(self, card):
        try:
            closest_mrt_text = card.find_element(By.XPATH, './/span[@class="listing-location-value"]').text
            # Check if the text contains 'from'
            if 'from' in closest_mrt_text:
                # Extract the MRT station name after 'from'
                match = re.search(r'from\s+(.+)', closest_mrt_text)
                closest_mrt = match.group(1).strip() if match else None
            else:
                # Take the whole string if 'from' is not present
                closest_mrt = closest_mrt_text.strip() if closest_mrt_text else None
        except Exception:
            closest_mrt = None  # Element not found
        finally:
            return closest_mrt
        
    def get_distance_to_closest_mrt(self, card):
        try:
            distance_text = card.find_element(By.XPATH, './/span[@class="listing-location-value"]').text
            # Look for patterns like '(460 m)', '(1.04 km)', or similar, ensuring it's inside brackets
            match = re.search(r'\(([\d.]+)\s*(km|m)\)', distance_text)
            if match:
                distance_value = float(match.group(1).strip())
                distance_unit = match.group(2).strip()
                if distance_unit == 'km':
                    distance_to_closest_mrt = int(distance_value * 1000)  # Convert km to m and cast to int
                else:
                    distance_to_closest_mrt = int(distance_value)  # Cast to int
            else:
                distance_to_closest_mrt = None  # No valid distance found
        except Exception:
            distance_to_closest_mrt = None  # Element not found
        finally:
            return distance_to_closest_mrt
        
    def get_is_verified_property(self, card):
        try:
            verified_element = card.find_element(By.XPATH, './/span[@da-id="verified-listing-badge-button"]')
            is_verified_property = True if verified_element else False
        except Exception:
            is_verified_property = False
        finally:
            return is_verified_property
        
    def get_is_everyone_welcomed(self, card):
        try:
            everyone_welcomed_element = card.find_elements(By.XPATH, './/span[@da-id="lc-info-badge"]')
            # Convert text to lowercase and check if it contains 'everyone welcome'
            is_everyone_welcomed = any("everyone welcome" in element.text.lower() for element in everyone_welcomed_element)
        except (NoSuchElementException, TimeoutException):
            is_everyone_welcomed = False
        finally:
            return is_everyone_welcomed
    
    def get_listed_date(self, card):
        try:
            listed_date_text = card.find_element(By.XPATH, './/ul[@class="listing-recency"]//span[@class="info-value"]').text
            # Extract the date part after "Listed on"
            match = re.search(r'Listed on\s+(\w+\s\d{1,2},\s\d{4})', listed_date_text)
            if match:
                # Parse the extracted date string into a datetime object
                date_str = match.group(1).strip()
                listed_date = datetime.strptime(date_str, "%b %d, %Y").date()  # Convert to YYYY-MM-DD format
            else:
                listed_date = None
        except Exception:
            listed_date = None
        finally:
            return listed_date
        
    def get_agent_name(self, card):
        try:
            agent_name = card.find_element(By.XPATH, './/div[@class="agent-info-group"]//a[@da-id="lc-agent-name"]').text
        except Exception:
            agent_name = None
        finally:
            return agent_name
        
    def get_agent_rating(self, card):
        try:
            agent_rating = card.find_element(By.XPATH, './/div[@class="agent-info-group"]//span[@class="rating-value"]').text
            # Convert rating to float
            agent_rating = float(agent_rating) if agent_rating else None
        except Exception:
            agent_rating = None
        finally:
            return agent_rating
        
    def get_property_selling_type(self):
        return self.mode  # Return the mode (Rent or Buy) as the property selling type
    
    def get_unit_type(self):
        if self.unit_type == -1:
            return "Room"
        elif self.unit_type == 0:
            return "Studio"
        elif self.unit_type == 1:
            return "1 Bedroom"
        elif self.unit_type == 2:
            return "2 Bedroom"
        elif self.unit_type == 3:
            return "3 Bedroom"
        elif self.unit_type == 4:
            return "4 Bedroom"
        elif self.unit_type == 5:
            return "5+ Bedroom"
        
    def get_selling_price(self, card):
        try:
            price = card.find_element(By.XPATH, './/div[@class="listing-price"]').text
            # Extract the numeric part of the price
            price_value = re.sub(r"[^\d.]", "", price)
            selling_price = Decimal(price_value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if price_value else None
        except Exception:
            selling_price = None
        finally:
            return selling_price
        
    def get_selling_price_text(self, card):
        try:
            selling_price_text = card.find_element(By.XPATH, './/div[@class="listing-price"]').text
        except Exception:
            selling_price_text = None
        finally:
            return selling_price_text
        
class DetailsInfo:
    DETAIL_COLUMNS = [
        "description", 
        "property_type", "property_type_text", 
        "lease_term", "lease_term_text",
        "bedroom_count", "bathroom_count", 
        "furnishing",
        "floor_size_sqft", "land_size_sqft", 
        "psf_floor", "psf_land",
        "raw_details_text", "raw_amenities_text", "raw_facilities_text"
    ]

    def __init__(self, sb):
        self.sb = sb
        self.print_output = True
        self.details = {}
        self.extract_details()

    def extract_details(self):
        # Extract the details from URL
        try:
            # Listing dictionary to store the extracted information
            details = {}

            details['description'] = self.get_description()
            details['bedroom_count'] = self.get_bedroom_count()
            details['bathroom_count'] = self.get_bathroom_count()

            # Click 'See All Details' button (might not be present)
            try:
                details_section = self.sb.find_element(By.XPATH, './/section[@class="details-section"]', timeout=2)
                self.sb.execute_script("arguments[0].scrollIntoView();", details_section)
                self.sb.wait_for_element_visible(By.XPATH, './/section[@class="details-section"]', timeout=5)
                # Try to find the 'See All Details' button
                buttons = details_section.find_elements(By.XPATH, './/button[@da-id="meta-table-see-more-btn"]')
                is_button_present = bool(buttons)
                if is_button_present:
                    see_all_details_button = buttons[0]
                    self.sb.execute_script("arguments[0].scrollIntoView();", see_all_details_button)
                    self.sb.execute_script("arguments[0].click();", see_all_details_button)
                    self.sb.sleep(1)
                # Extract the details (from modal if button, else from section)
                details['property_type'], details['property_type_text'] = self.get_property_type(is_button_present)
                details['lease_term'], details['lease_term_text'] = self.get_lease_term(is_button_present)
                details['furnishing'] = self.get_furnishing(is_button_present)
                details['floor_size_sqft'] = self.get_floor_size_sqft(is_button_present)
                details['land_size_sqft'] = self.get_land_size_sqft(is_button_present)
                details['psf_floor'] = self.get_psf_floor(is_button_present)
                details['psf_land'] = self.get_psf_land(is_button_present)
                details['raw_details_text'] = self.get_raw_details_text(is_button_present)
                # Try to close the modal if it was opened
                if is_button_present:
                    try:
                        close_button = self.sb.find_element(By.XPATH, './/div[@da-id="property-details-modal-header"]//button[@da-id="modal-close-button"]', timeout=1)
                        self.sb.execute_script("arguments[0].scrollIntoView();", close_button)
                        self.sb.wait_for_element_visible(By.XPATH, './/div[@da-id="property-details-modal-header"]//button[@da-id="modal-close-button"]', timeout=5)
                        self.sb.execute_script("arguments[0].click();", close_button)
                    except Exception:
                        pass
            except Exception:
                print("> 'See All Details' Section Not Found")
                details['property_type'] = None
                details['property_type_text'] = None
                details['lease_term'] = None
                details['lease_term_text'] = None
                details['furnishing'] = None
                details['floor_size_sqft'] = None
                details['land_size_sqft'] = None
                details['psf_floor'] = None
                details['psf_land'] = None
                details['raw_details_text'] = None

            # Click 'See All x Amenities' button (might not be present)
            try:
                amenities_section = self.sb.find_element(By.XPATH, './/section[@class="property-amenities-section"]', timeout=1)
                self.sb.execute_script("arguments[0].scrollIntoView();", amenities_section)
                self.sb.wait_for_element_visible(By.XPATH, './/section[@class="property-amenities-section"]', timeout=5)
                # Try to find the 'See All Amenities' button
                buttons = amenities_section.find_elements(By.XPATH, './/button[@da-id="amenities-see-all-btn"]')
                if buttons:
                    see_all_amenities_button = buttons[0]
                    self.sb.execute_script("arguments[0].scrollIntoView();", see_all_amenities_button)
                    self.sb.execute_script("arguments[0].click();", see_all_amenities_button)
                    self.sb.sleep(0.1)
                    details['raw_amenities_text'] = self.get_raw_amenities_text(is_button_present=True)
                    # Try to close the modal
                    try:
                        close_button = self.sb.find_element(By.XPATH, './/div[@da-id="facilities-amenities-modal-header"]//button[@da-id="modal-close-button"]', timeout=1)
                        self.sb.execute_script("arguments[0].scrollIntoView();", close_button)
                        self.sb.execute_script("arguments[0].click();", close_button)
                    except Exception:
                        pass
                else:
                    details['raw_amenities_text'] = self.get_raw_amenities_text(is_button_present=False)
            except Exception:
                details['raw_amenities_text'] = None

            # Click 'See All x Facilities' button (might not be present)
            try:
                facilities_section = self.sb.find_element(By.XPATH, './/section[@class="property-facilities-section"]', timeout=1)
                self.sb.execute_script("arguments[0].scrollIntoView();", facilities_section)
                self.sb.wait_for_element_visible(By.XPATH, './/section[@class="property-facilities-section"]', timeout=5)
                # Try to find the 'See All Facilities' button
                buttons = facilities_section.find_elements(By.XPATH, './/button[@da-id="facilities-see-all-btn"]')
                if buttons:
                    see_all_facilities_button = buttons[0]
                    self.sb.execute_script("arguments[0].scrollIntoView();", see_all_facilities_button)
                    self.sb.execute_script("arguments[0].click();", see_all_facilities_button)
                    self.sb.sleep(0.1)
                    details['raw_facilities_text'] = self.get_raw_facilities_text(is_button_present=True)
                    # Try to close the modal
                    try:
                        close_button = self.sb.find_element(By.XPATH, './/div[@da-id="facilities-amenities-modal-header"]//button[@da-id="modal-close-button"]', timeout=1)
                        self.sb.execute_script("arguments[0].scrollIntoView();", close_button)
                        self.sb.execute_script("arguments[0].click();", close_button)
                    except Exception:
                        pass
                else:
                    details['raw_facilities_text'] = self.get_raw_facilities_text(is_button_present=False)
            except Exception:
                details['raw_facilities_text'] = None

            # Print the extracted information for debugging
            if self.print_output:
                printed = set()
                for field in self.DETAIL_COLUMNS:
                    # Description
                    if field == "description" and "description" not in printed:
                        desc_val = details['description']
                        if desc_val:
                            desc_val = desc_val.replace('\n', ' ')
                            if len(desc_val) > 100:
                                shortened_desc = f"{desc_val[:50]}...{desc_val[-50:]}"
                                print(f"> Description: {shortened_desc}")
                            else:
                                print(f"> Description: {desc_val}")
                        else:
                            print("> Description: None")
                        printed.add("description")
                    # Property Type, Property Type Text
                    elif field in ["property_type", "property_type_text"] and "property_type" not in printed:
                        print(f"> Property Type: {details['property_type']} ({details['property_type_text']})")
                        printed.add("property_type")
                    # Lease Term, Lease Term Text
                    elif field in ["lease_term", "lease_term_text"] and "lease_term" not in printed:
                        print(f"> Lease Term: {details['lease_term']} ({details['lease_term_text']})")
                        printed.add("lease_term")
                    # Elsewhere
                    elif field not in [
                        "description",
                        "property_type", "property_type_text",
                        "lease_term", "lease_term_text",
                        # "raw_details_text", "raw_amenities_text", "raw_facilities_text"
                    ]:
                        display_name = field.replace("_", " ").title()
                        print(f"> {display_name}: {details[field]}")

            # Assign the extracted details to the instance variable
            self.details = details

        except Exception as e:
            print(f"❌ Error on Details Info Extraction: {e}")
            print("")

    def get_description(self):
        try:
            # Try to get subtitle
            try:
                subtitle = self.sb.find_element(By.XPATH, './/h3[@class="subtitle"]', timeout=1).text
            except Exception:
                subtitle = None

            # Try to get main description
            try:
                description = self.sb.find_element(By.XPATH, './/div[@class="description trimmed"]', timeout=1).text
            except Exception:
                description = None

            # Combine subtitle and description if present
            if subtitle and description:
                full_desc = f"{subtitle}\n{description}"
            elif subtitle:
                full_desc = subtitle
            elif description:
                full_desc = description
            else:
                full_desc = None

        except Exception as e:
            print(f"❌ Error extracting description: {e}")
            full_desc = None
        finally:
            return full_desc
        
    def get_property_type(self, is_button_present=True):
        property_type = None
        property_type_text = None
        try:
            if is_button_present:
                property_type_text = self.sb.find_element(By.XPATH, './/div[@class="property-modal-body-wrapper"]//img[@alt="home-open-o"]/../*[2]', timeout=1).text
            else:
                property_type_text = self.sb.find_element(By.XPATH, './/div[@da-id="property-details"]//img[@alt="home-open-o"]/../*[2]', timeout=1).text
            
            # Extract the part before " for "
            match = re.match(r"(.+?)\s+for\s+", property_type_text, re.IGNORECASE)
            property_type_raw = match.group(1).strip() if match else property_type_text
    
            # Map to enum: Condo, Landed, HDB
            lower = property_type_raw.lower()
            hdb_keywords = ['HDB']
            condo_keywords = ['Condominium', 'Apartment', 'Walk-up', 'Cluster House', 'Executive Condominium']
            landed_keywords = ['Terraced House', 'Detached House', 'Semi-Detached House', 'Corner Terrace', 'Bungalow House', 'Good Class Bungalow', 'Shophouse', 'Land Only', 'Town House', 'Conservation House', 'Cluster House']
    
            if any(word.lower() in lower for word in hdb_keywords):
                property_type = 'HDB'
            elif any(word.lower() in lower for word in condo_keywords):
                property_type = 'Condo'
            elif any(word.lower() in lower for word in landed_keywords):
                property_type = 'Landed'
            else:
                property_type = None
        except Exception:
            pass
        finally:
            return property_type, property_type_text
        
    def get_lease_term(self, is_button_present=True):
        lease_term = None
        lease_term_text = None
        try:
            if is_button_present:
                lease_term_text = self.sb.find_element(By.XPATH, './/div[@class="property-modal-body-wrapper"]//img[@alt="calendar-days-o"]/../*[2]', timeout=1).text
            else:
                lease_term_text = self.sb.find_element(By.XPATH, './/div[@da-id="property-details"]//img[@alt="calendar-days-o"]/../*[2]', timeout=1).text
            
            lower = lease_term_text.lower()
            if 'lease' in lower:
                lease_term = 'Leasehold'
            elif 'freehold' in lower:
                lease_term = 'Freehold'
            else:
                lease_term = None
        except Exception:
            pass
        finally:
            return lease_term, lease_term_text
        
    def get_bedroom_count(self):
        bedroom_count = None
        try:
            bed_number_element = self.sb.find_element(By.XPATH, './/div[@class="amenity"]//span//img[contains(@alt, "Bed")]//..//..//div//p', timeout=1)
            text = bed_number_element.text.strip()
            if text.isdigit():
                bedroom_count = int(text)
            else:
                # fallback to regex in case there is extra text
                match = re.search(r'(\d+)', text)
                if match:
                    bedroom_count = int(match.group(1))
        except Exception:
            pass
        finally:
            return bedroom_count

    def get_bathroom_count(self):
        bathroom_count = None
        try:
            bath_number_element = self.sb.find_element(By.XPATH, './/div[@class="amenity"]//span//img[contains(@alt, "Bath")]//..//..//div//p', timeout=1)
            text = bath_number_element.text.strip()
            if text.isdigit():
                bathroom_count = int(text)
            else:
                # fallback to regex in case there is extra text
                match = re.search(r'(\d+)', text)
                if match:
                    bathroom_count = int(match.group(1))
        except Exception:
            pass
        finally:
            return bathroom_count
        
    def get_furnishing(self, is_button_present=True):
        furnishing = None
        if is_button_present:
            elements = self.sb.find_elements(By.XPATH, './/div[@class="property-modal-body-wrapper"]//p')
        else:
            elements = self.sb.find_elements(By.XPATH, './/div[@da-id="property-details"]//td//img//..//div')
        for el in elements:
            text = el.text.strip().lower()
            if 'unfurnished' in text:
                furnishing = 'Unfurnished'
                break
            elif 'partially furnished' in text:
                furnishing = 'Partially Furnished'
                break
            elif 'fully furnished' in text or 'furnished' in text:
                furnishing = 'Fully Furnished'
                break
        return furnishing

    def get_floor_size_sqft(self, is_button_present=True):
        floor_size_sqft = None
        if is_button_present:
            elements = self.sb.find_elements(By.XPATH, './/div[@class="property-modal-body-wrapper"]//p')
        else:
            elements = self.sb.find_elements(By.XPATH, './/div[@da-id="property-details"]//td//img//..//div')
        for el in elements:
            text = el.text.lower()
            match = re.search(r'(\d+(?:\.\d+)?)\s*sqft\s*floor area', text)
            if match:
                floor_size_sqft = int(round(float(match.group(1))))
                break
        return floor_size_sqft
    
    def get_land_size_sqft(self, is_button_present=True):
        land_size_sqft = None
        if is_button_present:
            elements = self.sb.find_elements(By.XPATH, './/div[@class="property-modal-body-wrapper"]//p')
        else:
            elements = self.sb.find_elements(By.XPATH, './/div[@da-id="property-details"]//td//img//..//div')
        for el in elements:
            text = el.text.lower()
            match = re.search(r'(\d+(?:\.\d+)?)\s*sqft\s*land area', text)
            if match:
                land_size_sqft = int(round(float(match.group(1))))
                break
        return land_size_sqft
    
    def get_psf_floor(self, is_button_present=True):
        psf_floor = None
        if is_button_present:
            elements = self.sb.find_elements(By.XPATH, './/div[@class="property-modal-body-wrapper"]//p')
        else:
            elements = self.sb.find_elements(By.XPATH, './/div[@da-id="property-details"]//td//img//..//div')
        for el in elements:
            text = el.text.lower()
            # Match "S$ 10.89 psf" but not if "(land)" is present
            if "psf" in text and "(land)" not in text:
                match = re.search(r's\$[\s]*([\d,]+(?:\.\d+)?)\s*psf', text)
                if match:
                    psf_floor = Decimal(match.group(1).replace(',', '')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    break
        return psf_floor
    
    def get_psf_land(self, is_button_present=True):
        psf_land = None
        if is_button_present:
            elements = self.sb.find_elements(By.XPATH, './/div[@class="property-modal-body-wrapper"]//p')
        else:
            elements = self.sb.find_elements(By.XPATH, './/div[@da-id="property-details"]//td//img//..//div')
        for el in elements:
            text = el.text.lower()
            # Match "S$ 2,479.50 psf (land)"
            if "psf" in text and "(land)" in text:
                match = re.search(r's\$[\s]*([\d,]+(?:\.\d+)?)\s*psf', text)
                if match:
                    psf_land = Decimal(match.group(1).replace(',', '')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    break
        return psf_land
    
    def get_raw_details_text(self, is_button_present=True):
        if is_button_present:
            try:
                elements = self.sb.find_elements(By.XPATH, './/div[@class="property-modal-body-wrapper"]//p')
                all_texts = [el.text.strip() for el in elements if el.text.strip()]
                return ' || '.join(all_texts)
            except Exception:
                return None
        else:
            try:
                elements = self.sb.find_elements(By.XPATH, './/section[@class="details-section"]//td//img//..//div')
                all_texts = [el.text.strip() for el in elements if el.text.strip()]
                return ' || '.join(all_texts)
            except Exception:
                return None
        
    def get_raw_amenities_text(self, is_button_present=True):
        if is_button_present:
            try:
                elements = self.sb.find_elements(By.XPATH, './/div[@class="amenities-facilties-modal-body-wrapper"]//p')
                all_texts = [el.text.strip() for el in elements if el.text.strip()]
                return ' || '.join(all_texts)
            except Exception:
                return None
        else:
            try:
                elements = self.sb.find_elements(By.XPATH, './/section[@class="property-amenities-section"]//p')
                all_texts = [el.text.strip() for el in elements if el.text.strip()]
                return ' || '.join(all_texts)
            except Exception:
                return None
        
    def get_raw_facilities_text(self, is_button_present=True):
        if is_button_present:
            try:
                elements = self.sb.find_elements(By.XPATH, './/div[@class="amenities-facilties-modal-body-wrapper"]//p')
                all_texts = [el.text.strip() for el in elements if el.text.strip()]
                return ' || '.join(all_texts)
            except Exception:
                return None
        else:
            try:
                elements = self.sb.find_elements(By.XPATH, './/section[@class="property-facilities-section"]//p')
                all_texts = [el.text.strip() for el in elements if el.text.strip()]
                return ' || '.join(all_texts)
            except Exception:
                return None