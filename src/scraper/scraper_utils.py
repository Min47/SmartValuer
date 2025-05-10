# src/scraper/scraper_utils.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import requests
import time
import csv
import os

class ScraperUtils:
    def __init__(self, base_url="https://www.propertyguru.com.sg", mode="rent", headless=True):
        self.base_url = base_url
        self.mode = mode
        self.driver = self._init_driver(headless)
        self.listings = []

    def _init_driver(self, headless, UA=None):
        options = Options()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        if UA:
            options.add_argument(f'user-agent={UA}')

        driver = webdriver.Chrome(options=options)

        # Get the ChromeDriver version
        version = driver.capabilities['chrome']['chromedriverVersion'].split(' ')[0]
        print(f"ChromeDriver version: {version}")

        return driver

    def scrape(self, max_pages=None):
        print(f"Starting scrape for mode: {self.mode}")
        page = 1
        while True:
            if self.mode == "rent":
                url = f"{self.base_url}/property-for-rent?listingType=rent&page={page}&isCommercial=false&sort=date&order=desc"
            elif self.mode == "buy":
                url = f"{self.base_url}/property-for-sale?listingType=sale&page={page}&isCommercial=false&sort=date&order=desc"
            print(f"Scraping page {page}: {url}")
            self.driver.get(url)

            # Solve captcha
            self.solve_captcha()
            print("Captcha solved, continuing scrape...")
            time.sleep(2)

            # save the html content to a file for debugging
            with open(f"page_{page}.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)

            cards = self.driver.find_elements(By.XPATH, '//*[@class="listing-card-banner-root"]')
            if not cards or (max_pages and page > max_pages):
                print("No more listings or page limit reached.")
                break
            else:
                print(f"Found {len(cards)} listings on page {page}.")

            # for card in cards:
            #     try:
            #         title = card.find_element(By.CSS_SELECTOR, '.listing-title').text
            #         price = card.find_element(By.CSS_SELECTOR, '.price').text
            #         location = card.find_element(By.CSS_SELECTOR, '.listing-location').text
            #         self.listings.append({
            #             "title": title,
            #             "price": price,
            #             "location": location
            #         })
            #     except Exception as e:
            #         print("❌ Failed to parse a card:", e)

            page += 1

    def save_to_csv(self, filename="data/listings.csv"):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["title", "price", "location"])
            writer.writeheader()
            writer.writerows(self.listings)
        print(f"✅ Saved {len(self.listings)} listings to {filename}")

    def solve_captcha(self):
        send_url = "http://10.18.169.127:3000/cf-clearance-scraper"
        current_url = self.driver.current_url
        print(f"Solving captcha for URL: {current_url}")

        # Body for the POST request to send the URL to the captcha solver
        body: dict = {
            "url": current_url,
            "mode": "waf-session"
        }
        response: dict = requests.post(send_url, json=body)

        # Print response json
        print("Response JSON:", response.json())

        # Get UA
        cfUA = response.json()['headers']['user-agent']
        print("User-Agent:", cfUA)

        # Get cookies
        cookies: dict = response.json()['cookies']

        # Initialize an empty list to store all cookies
        cfCookie: list = []

        # Loop through the cookies list once
        for cookie in cookies:
            cfCookie.append({
                "name": cookie['name'],
                "value": cookie['value'],
                # Uncomment the following line if you need to specify the domain
                # "domain": cookie.get('domain', 'malaysia.indeed.com')
            })

        self.driver.quit()
        self.driver = self._init_driver(headless=True, UA=cfUA)
        self.driver.get(current_url)
        time.sleep(2)
        for cookie in cfCookie:
            self.driver.add_cookie(cookie)
        self.driver.refresh()
        time.sleep(5)

        # Capture html content after solving captcha
        print("Captcha solved, saving HTML content...")
        with open("captcha_solved.html", "w", encoding="utf-8") as f:
            f.write(self.driver.page_source)

    def close(self):
        self.driver.quit()
