import logging
import csv
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
    """Configures a fast, headless Selenium WebDriver instance."""
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

def detect_site_type(driver):
    """Detects if the site is static or dynamically loaded via JavaScript."""
    try:

        initial_source = driver.page_source
        
        time.sleep(3)
        
        final_source = driver.page_source
        
        if len(final_source) > len(initial_source):
            logging.info("Detected as a DYNAMIC site (Content loaded via JavaScript)")
            return "Dynamic"
        else:
            logging.info("Detected as a STATIC site (Content is fully available on initial load)")
            return "Static"
    except Exception as e:
        logging.warning(f"Site type detection failed: {e}")
        return "Unknown"

def fetch_page_content(url, driver):
    """Fetches page content, returns BeautifulSoup object + extracted price via JavaScript."""
    logging.info(f"Fetching page: {url}")
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except Exception:
        logging.warning(f"Page load timeout for {url}")
    site_type = detect_site_type(driver)
    try:
        price_js = driver.execute_script("""
            let price = document.querySelector('span.a-price-whole, span.a-offscreen, span.price, p.price, div.product-price');
            return price ? price.innerText : null;
        """)
        logging.info(f"Extracted Price (JS): {price_js}")
    except Exception as e:
        logging.error(f"JavaScript Extraction Failed: {e}")
        price_js = None

    soup = BeautifulSoup(driver.page_source, "html.parser")
    return soup, price_js, site_type

def extract_product_data(url, driver):
    """Extracts product name, price, and description from the given URL."""
    soup, price_js, site_type = fetch_page_content(url, driver)
    product_name = soup.select_one("span#productTitle, h1")
    product_name = product_name.get_text(strip=True) if product_name else "N/A"
    price = price_js if price_js else "N/A"
    if price == "N/A":
        for selector in [
            "span.a-price-whole", "span.a-offscreen", "span.price",
            "p.price", "div.product-price", "meta[itemprop='price']"
        ]:
            price_element = soup.select_one(selector)
            if price_element:
                price = price_element.get("content") if "meta" in selector else price_element.get_text(strip=True)
                break
    description = None
    for selector in ["div#feature-bullets ul", "div.product-description", "p.description", "meta[name='description']"]:
        desc_element = soup.select_one(selector)
        if desc_element:
            description = desc_element.get("content") if "meta" in selector else desc_element.get_text(strip=True)
            break
    description = description if description else "N/A"

    extracted_data = {
        "URL": url,
        "Product Name": product_name,
        "Price": price,
        "Description": description,
        "Site Type": site_type
    }
    logging.info(f"Extracted Data: {extracted_data}")
    return extracted_data

def save_data_to_csv(data, filename="extracted_data.csv"):
    """Appends extracted data to a CSV file without overwriting previous entries."""
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