# src/scraper/scraper_utils.py
from seleniumbase import SB
import csv
import os

class ScraperUtils:
    def __init__(self, base_url="https://www.propertyguru.com.sg", mode="rent", headless=True):
        self.base_url = base_url
        self.mode = mode
        self.headless = headless
        self.listings = []

    def scrape(self, max_pages=None):
        print(f"Starting scrape for mode: {self.mode}")
        page = 1
        with SB(headless=self.headless) as sb:  # Use SB() context manager
            while True:
                try:
                    if self.mode == "rent":
                        url = f"{self.base_url}/property-for-rent?listingType=rent&page={page}&isCommercial=false&sort=date&order=desc"
                    elif self.mode == "buy":
                        url = f"{self.base_url}/property-for-sale?listingType=sale&page={page}&isCommercial=false&sort=date&order=desc"
                    print(f"Scraping page {page}: {url}")
                    sb.open(url)

                    # Solve captcha if necessary
                    # self.solve_captcha(sb)
                    # time.sleep(2)

                    # Save the HTML content to a file for debugging (optional)
                    with open(f"page_{page}.html", "w", encoding="utf-8") as f:
                        f.write(sb.get_page_source())

                    cards = sb.find_elements('//*[@class="listing-card-banner-root"]')
                    if not cards or (max_pages and page > max_pages):
                        print("No more listings or page limit reached.")
                        break
                    else:
                        print(f"Found {len(cards)} listings on page {page}.")

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

                    page += 1
                except Exception as e:
                    print(f"❌ Error on page {page}: {e}")
                    break

    def save_to_csv(self, filename="data/listings.csv"):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["title", "price", "location"])
            writer.writeheader()
            writer.writerows(self.listings)
        print(f"✅ Saved {len(self.listings)} listings to {filename}")

    # def solve_captcha(self):
    #     try:
    #         send_url = "http://10.18.169.127:3000/cf-clearance-scraper"
    #         current_url = self.get_current_url()
    #         print(f"Solving captcha for URL: {current_url}")

    #         body = {"url": current_url, "mode": "waf-session"}
    #         response = requests.post(send_url, json=body)
    #         response_data = response.json()

    #         cfUA = response_data['headers']['user-agent']
    #         cookies = response_data['cookies']

    #         self.quit()
    #         self.start(headless=self.headless, user_agent=cfUA)
    #         self.open(current_url)
    #         time.sleep(2)
    #         for cookie in cookies:
    #             self.add_cookie({"name": cookie['name'], "value": cookie['value']})
    #         self.refresh()
    #         time.sleep(5)
    #     except Exception as e:
    #         print(f"❌ Error solving captcha: {e}")