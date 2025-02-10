import logging
import csv
import re
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def setup_driver():

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def clean_price(price):
    if not price:
        return "N/A"
    
    price = price.strip()

    price = price.replace("\u20A6", "₦").replace("N", "₦").replace("₦₦", "₦")

    matches = re.findall(r'₦?\s?[\d,.]+', price)

    if matches:
        cleaned_price = min(matches, key=lambda p: len(p))
        return cleaned_price.strip()
    
    return "N/A"

def fetch_page_content(url, driver):

    logging.info(f"Fetching page: {url}")
    driver.get(url)

    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except Exception:
        logging.warning(f"Page load timeout for {url}")

    # JavaScript Extraction for Price
    try:
        price_js = driver.execute_script("""
            let priceElements = document.querySelectorAll('span.a-price-whole, span.a-offscreen, span.price, p.price, div.product-price, div.prc, div[class*="price"], [itemprop="price"], .-b -ltr -tal, .price-box, span#prcIsum, .item-price, .display-price');
            let priceList = Array.from(priceElements).map(el => el.innerText.trim());
            return priceList.length > 0 ? priceList[0] : null;
        """)
        logging.info(f"Extracted Price (JS): {price_js}")
    except Exception as e:
        logging.error(f"JavaScript Extraction Failed: {e}")
        price_js = None

    # XPath Extraction for Price
    try:
        price_xpath = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'₦') or contains(@class, 'price') or contains(@id, 'prcIsum')]"))
        ).text
        logging.info(f"Extracted Price (XPath): {price_xpath}")
    except Exception:
        price_xpath = None

    soup = BeautifulSoup(driver.page_source, "html.parser")
    return soup, clean_price(price_js or price_xpath)

def extract_product_data(url, driver):
    soup, price_js = fetch_page_content(url, driver)

    # Extract product name
    product_name = None
    for selector in ["span#productTitle", "h1", "h2.product-title", "h1.product_name", ".product-name", ".-fs20 -pts -pbxs", ".product-title", ".prod-title"]:
        product_element = soup.select_one(selector)
        if product_element:
            product_name = product_element.get_text(strip=True)
            break
    product_name = product_name if product_name else "N/A"

    # Use extracted price, fallback to HTML if necessary
    price = price_js if price_js else "N/A"
    if price == "N/A":
        for selector in ["span.a-price-whole", "span.a-offscreen", "span.price", "p.price", "div.product-price", ".-b -ltr -tal -fs24", "span#prcIsum", ".price", ".prc"]:
            price_element = soup.select_one(selector)
            if price_element:
                raw_price = price_element.get_text(strip=True)
                price = clean_price(raw_price)
                break

    # Extract description
    description = None
    for selector in ["div#feature-bullets ul", "div.product-description", "p.description", "meta[name='description']", ".product-desc", ".prod-desc"]:
        desc_element = soup.select_one(selector)
        if desc_element:
            description = desc_element.get("content") if "meta" in selector else desc_element.get_text(strip=True)
            break
    description = description if description else "N/A"

    extracted_data = {
        "URL": url,
        "Product Name": product_name,
        "Price": price,
        "Description": description
    }
    logging.info(f"Extracted Data: {extracted_data}")
    return extracted_data

def save_data_to_csv(data, filename="extracted_data.csv"):
    file_exists = False
    try:
        with open(filename, "r", newline="", encoding="utf-8") as f:
            file_exists = bool(f.readline())
    except FileNotFoundError:
        pass

    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

    logging.info(f"Data appended to {filename}")

if __name__ == "__main__":
    url = input("Enter product page URL: ").strip()
    driver = setup_driver()
    
    try:
        data = extract_product_data(url, driver)
        save_data_to_csv(data)
    finally:
        driver.quit()

