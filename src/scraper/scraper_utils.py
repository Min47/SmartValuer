# src/scraper/scraper_utils.py
from seleniumbase import SB
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import csv
import os

class ScraperUtils:
    def __init__(self, mode="rent"):
        self.mode = mode
        self.listings = []

    def scrape(self, desired_pages=None):
        cur_page = 1
        max_pages = 99  # Temporary default value for maximum pages

        # Filters
        print(f"= Scraping Mode: {self.mode}")
        print("")

        # Run the scraper with a context manager
        with SB(uc=True, xvfb=True, locale="en", uc_cdp_events=True) as sb:
            while True:
                try:
                    # Page
                    print(f"= Page {cur_page}")
                    
                    # Construct the URL based on the filters
                    if self.mode == "rent":
                        url = f"https://www.propertyguru.com.sg/property-for-rent/{cur_page}?listingType=rent&cur_page={cur_page}&isCommercial=false&sort=date&order=desc"
                    elif self.mode == "buy":
                        url = f"https://www.propertyguru.com.sg/property-for-sale/{cur_page}?listingType=sale&cur_page={cur_page}&isCommercial=false&sort=date&order=desc"
                    # Print the URL for debugging
                    print(f"> URL: {url}")
                    
                    # Solve captcha
                    sb.uc_open_with_reconnect(url, 4)
                    sb.uc_gui_click_captcha()
                    sb.sleep(2)

                    # Save the HTML content to a file for debugging (optional)
                    with open(f"data/Page_{cur_page}.html", "w", encoding="utf-8") as f:
                        f.write(sb.get_page_source())

                    # # Dynamically determine the maximum number of pages
                    # # Not yet verify the element
                    # if desired_pages is None:
                    #     try:
                    #         max_pages_element = sb.find_element('css selector', '.pagination-max')  # Adjust selector as needed
                    #         max_pages = int(max_pages_element.text.strip())
                    #         print(f"Determined Max Pages: {max_pages}")
                    #     except Exception as e:
                    #         print(f"❌ Error Determining Max Pages: {e}")

                    # Find the listing cards on the page
                    cards = sb.find_elements('//*[@class="listing-card-banner-root"]')
                    if not cards:
                        print(f"> Listings Found: 0")
                        break
                    else:
                        print(f"> Listings Found: {len(cards)}")

                    # Extract information from each card
                    for card in cards:
                        try:
                            # # Print the card HTML for debugging
                            # print(card.get_attribute('outerHTML'))

                            # Extract the card id
                            try:
                                card_id_element = card.find_element(By.XPATH, './/div[@data-listing-id]')
                                card_id = card_id_element.get_attribute('data-listing-id')
                            except NoSuchElementException:
                                card_id = None

                            # Extract the title
                            try:
                                title = card.find_element(By.XPATH, './/h3[@class="listing-title"]').text
                            except NoSuchElementException:
                                title = None

                            # Extract the price
                            try:
                                price = card.find_element(By.XPATH, './/div[@class="listing-price"]').text
                            except NoSuchElementException:
                                price = None

                            # Extract the address
                            try:
                                address = card.find_element(By.XPATH, './/div[@class="listing-address"]').text
                            except NoSuchElementException:
                                address = None

                            # Add the extracted listing information to the list
                            self.listings.append({
                                "card_id": card_id,
                                "title": title,
                                "price": price,
                                "location": address
                            })

                            # Debugging output
                            print(f"Card: {card_id} | Title: {title} | Price: {price} | Location: {address}")
                        except Exception as e:
                            print(f"❌ Error on Card Extraction: {e}")

                    # Check if reached the desired page limit
                    if desired_pages is not None and cur_page >= desired_pages:
                        print("")
                        print(f"= Reached Desired Page Limit: {desired_pages}.")
                        break
                    # Check if reached the maximum page limit
                    if cur_page >= max_pages:
                        print("")
                        print(f"= Reached Maximum Page Limit: {max_pages}.")
                        break

                    # Increment the page number
                    cur_page += 1
                    print("")
                except Exception as e:
                    print(f"❌ Error on Page {cur_page}: {e}")
                    break

    def save_to_csv(self, filename="data/listings.csv"):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["card_id", "title", "price", "location"])
            writer.writeheader()
            writer.writerows(self.listings)
        print(f"= Saved {len(self.listings)} Listings to {filename}")