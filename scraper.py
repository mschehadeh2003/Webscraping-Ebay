# scraper.py
# COSC 482 – Assignment 5
# Web Scraping with Selenium (eBay Global Tech Deals)
# Extracts: timestamp, title, price, original_price, shipping, item_url
# Multithreaded and GitHub Actions–friendly

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
from datetime import datetime
import os
from concurrent.futures import ThreadPoolExecutor, as_completed


TECH_DEALS_URL = "https://www.ebay.com/globaldeals/tech"
CSV_PATH = "ebay_tech_deals.csv"
MAX_WORKERS = 4


# ---------------- DRIVER INITIALIZATION ----------------

def initialize_driver():
    """Set up Chrome WebDriver in headless mode for GitHub Actions compatibility."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    return webdriver.Chrome(options=options)


# ---------------- SCROLL FUNCTION ----------------

def scroll_to_bottom(driver, pause_time=2):
    """Scrolls down until all products are loaded."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


# ---------------- PRODUCT LINK COLLECTION ----------------

def collect_product_links():
    """Open the Tech Deals page and collect all product URLs."""
    driver = initialize_driver()
    driver.get(TECH_DEALS_URL)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.dne-itemtile-detail"))
    )
    scroll_to_bottom(driver)

    items = driver.find_elements(By.CSS_SELECTOR, "div.dne-itemtile-detail a[href*='/itm/']")
    links = []
    for i in items:
        href = i.get_attribute("href")
        if href and "ebay.com/itm" in href:
            href = href.split("?")[0]
            if href not in links:
                links.append(href)

    driver.quit()
    print(f"[INFO] Collected {len(links)} product URLs.")
    return links


# ---------------- PRODUCT PAGE SCRAPER ----------------

def scrape_product_page(url):
    """Open a product page and extract required details."""
    driver = initialize_driver()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Default dict to prevent UnboundLocalError
    dict_item = {
        "timestamp": ts,
        "title": "N/A",
        "price": "N/A",
        "original_price": "N/A",
        "shipping": "N/A",
        "item_url": url
    }

    try:
        driver.get(url)

        # Wait for title layout (new or old)
        try:
            WebDriverWait(driver, 20).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1.x-item-title__mainTitle")),
                    EC.presence_of_element_located((By.ID, "itemTitle"))
                )
            )
        except:
            print(f"[WARN] Timeout waiting for title on {url}")
            return dict_item

        # --- Title ---
        try:
            title = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "h1.x-item-title__mainTitle span.ux-textspans.ux-textspans--BOLD")
                )
            ).text.strip()
        except:
            try:
                title = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "itemTitle"))
                ).text.replace("Details about", "").strip()
            except:
                title = "N/A"

        # --- Price ---
        try:
            price = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".x-price-primary .ux-textspans"))
            ).text.strip()
        except:
            try:
                price = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span#prcIsum"))
                ).text.strip()
            except:
                price = "N/A"

        # --- Original Price ---
        try:
            original_price = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//span[contains(@class, 'ux-textspans--SECONDARY') and contains(@class, 'ux-textspans--STRIKETHROUGH')]")
                )
            ).text.strip()
        except:
            try:
                original_price = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span#orgPrc"))
                ).text.strip()
            except:
                original_price = "N/A"

        # Pause slightly to let shipping render
        time.sleep(1.5)

        # --- Shipping ---
        try:
            shipping = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".ux-labels-values__values-content div"))
            ).text.strip()
        except:
            try:
                shipping = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#shSummary"))
                ).text.strip()
            except:
                shipping = "N/A"

        # Update dict
        dict_item = {
            "timestamp": ts,
            "title": title,
            "price": price,
            "original_price": original_price,
            "shipping": shipping,
            "item_url": url
        }

        print(f"[OK] Scraped: {title[:60]}...")
        return dict_item

    except Exception as e:
        print(f"[ERROR] {url[:80]} -> {type(e).__name__}: {e}")
        return dict_item

    finally:
        time.sleep(2)
        driver.quit()


# ---------------- MAIN CONTROLLER ----------------

def scrape_ebay_deals():
    """Main scraper controller using multithreading."""
    links = collect_product_links()
    if not links:
        print("[WARN] No product links found.")
        return

    print(f"[INFO] Starting product scraping using {MAX_WORKERS} threads...")
    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(scrape_product_page, url) for url in links]
        for fut in as_completed(futures):
            results.append(fut.result())

    df = pd.DataFrame(results)
    write_headers = not os.path.exists(CSV_PATH)
    df.to_csv(
        CSV_PATH,
        mode="a" if not write_headers else "w",
        index=False,
        header=write_headers,
        encoding="utf-8"
    )

    print(f"[SUCCESS] Scraped {len(df)} products at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[SAVED] Data saved to {CSV_PATH}")


if __name__ == "__main__":
    scrape_ebay_deals()
