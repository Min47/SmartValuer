# src/scraper/scraper_utils.py
from seleniumbase import SB
import csv
import os

class ScraperUtils:
    def __init__(self, mode="rent"):
        self.mode = mode
        self.listings = []

    def scrape(self, desired_pages=None):
        print(f"Starting scrape for mode: {self.mode}")
        cur_page = 1
        max_pages = 99  # Temporary default value for maximum pages

        with SB(uc=True, xvfb=True, locale="en", uc_cdp_events=True) as sb:  # Use SB() context manager
            while True:
                try:
                    # Check if the current page exceeds the desired pages
                    if desired_pages is not None and cur_page > desired_pages:
                        print(f"Reached desired page limit: {desired_pages}. Stopping scrape.")
                        break
                    if cur_page > max_pages:
                        print(f"Reached maximum page limit: {max_pages}. Stopping scrape.")
                        break
                    
                    # Construct the URL based on the mode
                    if self.mode == "rent":
                        url = f"https://www.propertyguru.com.sg/property-for-rent?listingType=rent&cur_page={cur_page}&isCommercial=false&sort=date&order=desc"
                    elif self.mode == "buy":
                        url = f"https://www.propertyguru.com.sg/property-for-sale?listingType=sale&cur_page={cur_page}&isCommercial=false&sort=date&order=desc"
                    print(f"Scraping cur_page {cur_page}: {url}")

                    # Solve captcha
                    sb.activate_cdp_mode(url)
                    sb.uc_gui_click_captcha()
                    sb.sleep(2)

                    # # Dynamically determine the maximum number of pages
                    # # Not yet verify the element
                    # if desired_pages is None:
                    #     try:
                    #         max_pages_element = sb.find_element('css selector', '.pagination-max')  # Adjust selector as needed
                    #         max_pages = int(max_pages_element.text.strip())
                    #         print(f"Determined max pages: {max_pages}")
                    #     except Exception as e:
                    #         print(f"❌ Failed to determine max pages, using default {max_pages}: {e}")

                    # Save the HTML content to a file for debugging (optional)
                    with open(f"page_{cur_page}.html", "w", encoding="utf-8") as f:
                        f.write(sb.get_page_source())
                    
                    # Find the listing cards on the page
                    cards = sb.find_elements('//*[@class="listing-card-banner-root"]')
                    if not cards:
                        print("No more listings.")
                        break
                    else:
                        print(f"Found {len(cards)} listings on cur_page {cur_page}.")

                    # Example of extracting data from cards
                    for card in cards:
                        try:
                            title = card.find_element("css selector", '.listing-title').text
                            price = card.find_element("css selector", '.price').text
                            location = card.find_element("css selector", '.listing-location').text
                            self.listings.append({
                                "title": title,
                                "price": price,
                                "location": location
                            })
                        except Exception as e:
                            print(f"❌ Failed to parse a card: {e}")

                    cur_page += 1
                except Exception as e:
                    print(f"❌ Error on cur_page {cur_page}: {e}")
                    break

    def save_to_csv(self, filename="data/listings.csv"):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["title", "price", "location"])
            writer.writeheader()
            writer.writerows(self.listings)
        print(f"✅ Saved {len(self.listings)} listings to {filename}")