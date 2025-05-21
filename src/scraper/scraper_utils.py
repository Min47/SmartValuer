# src/scraper/scraper_utils.py
from database import Properties
from datetime import datetime
from seleniumbase import SB
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import csv
import os
import random
import re
import time

class ScraperUtils:
    def __init__(self, session, mode, unit_type):
        self.session = session
        self.mode = mode
        self.unit_type = unit_type
        self.cur_page_listings = []
        self.all_properties = []

    def scrape_listings(self, desired_pages=None):
        cur_page = 1
        max_pages = 99  # Temporary default value for maximum pages

        # Filters
        lines = [
            f"= Scraping Mode: {self.mode}",
            f"= Unit Type: {'Room' if self.unit_type == -1 else 'Studio' if self.unit_type == 0 else f'{self.unit_type} Bedroom' if self.unit_type!= 5 else f'{self.unit_type} Bedroom+'}",
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
                        url = f"https://www.propertyguru.com.sg/property-for-rent/{cur_page}?listingType=rent&cur_page={cur_page}&isCommercial=false&sort=date&order=desc&bedrooms={self.unit_type}"
                    elif self.mode == "Buy":
                        url = f"https://www.propertyguru.com.sg/property-for-sale/{cur_page}?listingType=sale&cur_page={cur_page}&isCommercial=false&sort=date&order=desc&bedrooms={self.unit_type}"
                    # Print the URL for debugging
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
                    self.all_properties.extend(self.cur_page_listings)

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
                        break
                    # Check if reached the desired page limit
                    if desired_pages is not None and cur_page >= desired_pages:
                        print(f"> Reached Desired Page Limit: {desired_pages}")
                        break

                    # Increment the page number
                    cur_page += 1
                    time.sleep(random.uniform(2, 5))  # Sleep for a random time between 2 to 5 seconds
                    print("")
                except Exception as e:
                    print(f"❌ Error on Page {cur_page}: {e}")
                    break

    def scrape_details(self):
        # Info:
        # Description
        # Property Type
        # Property Type Text
        # Ownership Type
        # Ownership Type Text
        # Bedroom Count
        # Bathroom Count
        # Floor Size (sqft)
        # Land Size (sqft)
        # PSF Floor
        # PSF Land

        # Query the database for listings that need details
        listings = self.session.query(Properties).filter_by(details_fetched=False).all()

        # # After scraping details for a property
        # property.details_fetched = True
        # self.session.commit()
        pass

    # Use all properties to save to CSV
    def save_to_csv(self, filename="data/properties.csv"):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        if not self.all_properties:
            print("= No properties to save.")
            return
    
        # Dynamically detect fieldnames from the first property
        fieldnames = self.all_properties[0].keys()
        file_exists = os.path.isfile(filename)
        write_header = not file_exists or os.path.getsize(filename) == 0
    
        with open(filename, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerows(self.all_properties)
        # print(f"= Saved {len(self.all_properties)} Properties to {filename}")

    # Use current page listings to save to DB, since the listings will be saved per page
    def save_to_db_listings(self, session):
        # Save the listings to the database
        try:
            Properties.batch_upsert_listings(session, self.cur_page_listings)
        except Exception as e:
            print(f"❌ Error Saving to DB: {e}")

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
            ("property_type", "get_property_type"),
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
                    if field in ["property_type", "unit_type"]:
                        # For property_type and unit_type, use the class attributes
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
        except NoSuchElementException:
            outer_html = None
        finally:
            return outer_html
    
    def get_property_id(self, card):
        try:
            property_id_element = card.find_element(By.XPATH, './/div[@data-listing-id]')
            property_id = property_id_element.get_attribute('data-listing-id')
        except NoSuchElementException:
            property_id = None
        finally:
            return property_id
        
    def get_title(self, card):
        try:
            title = card.find_element(By.XPATH, './/h3[@class="listing-title"]').text
        except NoSuchElementException:
            title = None
        finally:
            return title
        
    def get_address(self, card):
        try:
            address = card.find_element(By.XPATH, './/div[@class="listing-address"]').text
        except NoSuchElementException:
            address = None
        finally:
            return address
        
    def get_property_url(self, card):
        try:
            property_url = card.find_element(By.XPATH, './/a[@class="listing-card-link"]').get_attribute('href')
        except NoSuchElementException:
            property_url = None
        finally:
            return property_url
        
    def get_availability(self, card):
        try:
            availability = card.find_element(By.XPATH, './/span[@da-id="lc-price-badge"]').text
        except NoSuchElementException:
            availability = None
        finally:
            return availability
        
    def get_project_year(self, card):
        try:
            year_text = card.find_element(By.XPATH, './/span[@da-id="lc-info-badge"]').text
            # Look for 'Built: xxxx' or 'New Project: xxxx'
            match = re.search(r'(Built:|New Project:)\s*(\d{4})', year_text)
            project_year = int(match.group(2).strip()) if match else None
        except NoSuchElementException:
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
        except NoSuchElementException:
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
        except NoSuchElementException:
            distance_to_closest_mrt = None  # Element not found
        finally:
            return distance_to_closest_mrt
        
    def get_is_verified_property(self, card):
        try:
            verified_element = card.find_element(By.XPATH, './/span[@da-id="verified-listing-badge-button"]')
            is_verified_property = True if verified_element else False
        except NoSuchElementException:
            is_verified_property = False
        finally:
            return is_verified_property
        
    def get_is_everyone_welcomed(self, card):
        try:
            everyone_welcomed_element = card.find_elements(By.XPATH, './/span[@da-id="lc-info-badge"]')
            # Convert text to lowercase and check if it contains 'everyone welcome'
            is_everyone_welcomed = any("everyone welcome" in element.text.lower() for element in everyone_welcomed_element)
        except NoSuchElementException:
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
                listed_date = datetime.strptime(date_str, "%B %d, %Y").date()  # Convert to YYYY-MM-DD format
            else:
                listed_date = None
        except NoSuchElementException:
            listed_date = None
        finally:
            return listed_date
        
    def get_agent_name(self, card):
        try:
            agent_name = card.find_element(By.XPATH, './/div[@class="agent-info-group"]//a[@da-id="lc-agent-name"]').text
        except NoSuchElementException:
            agent_name = None
        finally:
            return agent_name
        
    def get_agent_rating(self, card):
        try:
            agent_rating = card.find_element(By.XPATH, './/div[@class="agent-info-group"]//span[@class="rating-value"]').text
            # Convert rating to float
            agent_rating = float(agent_rating) if agent_rating else None
        except NoSuchElementException:
            agent_rating = None
        finally:
            return agent_rating
        
    def get_property_type(self):
        return self.mode  # Return the mode (Rent or Buy) as the property type
    
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
            selling_price = float(price_value) if price_value else None
        except NoSuchElementException:
            selling_price = None
        finally:
            return selling_price
        
    def get_selling_price_text(self, card):
        try:
            selling_price_text = card.find_element(By.XPATH, './/div[@class="listing-price"]').text
        except NoSuchElementException:
            selling_price_text = None
        finally:
            return selling_price_text