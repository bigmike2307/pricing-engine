import logging
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def setup_driver():
    """Sets up a headless Chrome WebDriver for scraping."""
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
    """Cleans and formats extracted price strings."""
    if not price:
        return "N/A"
    
    price = price.strip().replace("\u20A6", "₦").replace("N", "₦").replace("₦₦", "₦")
    price = re.sub(r"\s+", "", price)  # Remove unnecessary spaces
    matches = re.findall(r'([₦$€£₹])?\s?([\d,.]+)', price)  # Capture currency + amount
    
    if matches:
        return f"{matches[0][0] or ''}{matches[0][1]}"
    return "N/A"

def fetch_amazon_page_content(url, driver):
    """Fetches Amazon product page content."""
    driver.get(url)
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except Exception as e:
        logging.warning(f"Page load timeout for Amazon {url}: {e}")

    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Extract product name
    product_name = soup.select_one("span#productTitle")
    product_name = product_name.get_text(strip=True) if product_name else "N/A"
    
    # Extract current price
    current_price = soup.select_one("span.a-price-whole, span.a-offscreen")
    current_price = clean_price(current_price.get_text(strip=True)) if current_price else "N/A"

    # Extract previous price (discounted price)
    previous_price = soup.select_one("span.a-text-strike")
    previous_price = clean_price(previous_price.get_text(strip=True)) if previous_price else "N/A"
    
    # Description section
    description = soup.select_one("div#productDescription")
    description = description.get_text(strip=True) if description else "N/A"
    
    return product_name, current_price, previous_price, description

def extract_product_data(url, driver):
    """Extracts product details including name, prices, and detailed description."""
    product_name, current_price, previous_price, description = fetch_amazon_page_content(url, driver)

    # Calculate discount
    discount = "0%"
    if previous_price != "N/A" and current_price != "N/A":
        try:
            prev_price_num = float(re.sub(r"[^\d.]", "", previous_price))
            price_num = float(re.sub(r"[^\d.]", "", current_price))
            discount = f"{round((prev_price_num - price_num) / prev_price_num * 100, 2)}%"
        except Exception:
            pass

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {"Timestamp": timestamp, "URL": url, "Product Name": product_name, "Current Price": current_price, "Previous Price": previous_price, "Discount": discount, "Description": description}

if __name__ == "__main__":
    url = input("Enter Amazon product page URL: ").strip()

    # Setup the web driver
    driver = setup_driver()

    try:
        data = extract_product_data(url, driver)
        print(data)  # Print the extracted data to verify it works
    except Exception as e:
        logging.error(f"Error extracting data for {url}: {e}")
    
    driver.quit()
