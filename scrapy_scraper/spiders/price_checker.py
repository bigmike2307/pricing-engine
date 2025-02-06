# import scrapy
# import logging
# from scrapy.http import HtmlResponse
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager

# class PriceCheckerSpider(scrapy.Spider):
#     name = "price_checker"
#     custom_settings = {
#         "FEEDS": {
#             "output.csv": {
#                 "format": "csv",
#                 "fields": ["url", "product_name", "price"],
#             }
#         },
#         "LOG_LEVEL": "INFO",  # Reduce log level for cleaner output
#     }

#     def __init__(self, urls=None, *args, **kwargs):
#         super(PriceCheckerSpider, self).__init__(*args, **kwargs)
        
#         # Convert URL string to list
#         if urls:
#             self.start_urls = urls.split(",")
#         else:
#             self.start_urls = [
#                 "https://makarinigeria.com/products/naturalle-carotonic-extreme-gift-set",  # Example URL
#             ]
        
#         # Setup Selenium WebDriver
#         chrome_options = Options()
#         chrome_options.add_argument("--headless")
#         chrome_options.add_argument("--disable-blink-features=AutomationControlled")
#         chrome_options.add_argument("--no-sandbox")
#         chrome_options.add_argument("--disable-dev-shm-usage")

#         self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

#     def parse(self, response):
#         """Decide whether to use Scrapy or Selenium"""
#         self.logger.info(f"Processing URL: {response.url}")

#         # Use Selenium for JavaScript-heavy websites
#         if "makarinigeria.com" in response.url:
#             self.logger.info(f"Using Selenium for {response.url}")
#             self.driver.get(response.url)
            
#             # Wait for dynamic content to load
#             try:
#                 WebDriverWait(self.driver, 10).until(
#                     EC.presence_of_element_located((By.CSS_SELECTOR, "h1.product-title"))
#                 )
#             except Exception as e:
#                 self.logger.error(f"Error loading dynamic content: {e}")
#                 return
            
#             page_source = self.driver.page_source
#             response = HtmlResponse(url=response.url, body=page_source, encoding='utf-8')

#         # Extract data
#         yield self.extract_data(response)

#     def extract_data(self, response):
#         """Extract product name, price, and URL"""
#         try:
#             product_name = response.css("h1.product-title::text").get(default="N/A").strip()
#             price = response.css(".product-price::text").get(default="N/A").strip()
#         except Exception as e:
#             self.logger.error(f"Error extracting data: {e}")
#             product_name = "N/A"
#             price = "N/A"

#         return {
#             "url": response.url,
#             "product_name": product_name,
#             "price": price,
#         }

#     def closed(self, reason):
#         """Close Selenium WebDriver"""
#         self.driver.quit()


# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager

# # Setup Selenium WebDriver
# chrome_options = Options()
# chrome_options.add_argument("--headless")  # Run in headless mode
# chrome_options.add_argument("--disable-blink-features=AutomationControlled")
# chrome_options.add_argument("--no-sandbox")
# chrome_options.add_argument("--disable-dev-shm-usage")
# chrome_options.add_argument("--window-size=1920,1080")  # Set window size
# chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

# # Initialize WebDriver
# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# # Load the target URL
# url = "https://makarinigeria.com/products/naturalle-carotonic-extreme-gift-set"
# driver.get(url)

# # Wait for the page to load
# try:
#     WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
#     product_name = driver.find_element(By.TAG_NAME, "h1").text

#     # Use XPath instead of CSS Selector
#     try:
#         price = driver.find_element(By.XPATH, "//*[contains(text(), '₦')]").text  # Adjust if necessary
#     except:
#         price = "Price not found"

#     print(f"Product Name: {product_name}")
#     print(f"Price: {price}")

# except Exception as e:
#     print(f"Error: {e}")
# finally:
#     driver.quit()




import scrapy
import requests
import pandas as pd
import time
from scrapy.http import TextResponse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def is_dynamic_website(url):
    """
    Check if the website is dynamic by testing with Scrapy.
    If Scrapy returns empty content, we assume it's dynamic.
    """
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        scrapy_response = TextResponse(url, body=response.text, encoding="utf-8")
        page_content = scrapy_response.xpath("//body//text()").getall()
        return len(page_content) < 10 
    except Exception:
        return True 

def scrape_with_scrapy(url):
    """
    Scrape content from a static website using Scrapy.
    """
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    scrapy_response = TextResponse(url, body=response.text, encoding="utf-8")
    
    product_name = scrapy_response.css("h1::text").get(default="N/A").strip()
    price = scrapy_response.css(".product-price::text").get(default="N/A").strip()
    
    print(f"Scrapy - Product Name: {product_name}")
    print(f"Scrapy - Price: {price}")
    
    return {
        "URL": url,
        "Product Name": product_name,
        "Price": price,
    }

def scrape_with_selenium(url):
    """
    Scrape content from a dynamic website using Selenium.
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(5)
    try:
        product_name = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
    except:
        product_name = "N/A"

    try:
        price = driver.find_element(By.CSS_SELECTOR, ".product-price").text.strip()
    except:
        price = "N/A"

    print(f"Selenium - Product Name: {product_name}")
    print(f"Selenium - Price: {price}")

    driver.quit()
    
    return {
        "URL": url,
        "Product Name": product_name,
        "Price": price,
    }

def save_to_csv(data):
    """
    Save extracted data to a CSV file.
    """
    df = pd.DataFrame([data])
    df.to_csv("website_content.csv", index=False, encoding="utf-8")
    print("Content saved to 'website_content.csv'")

if __name__ == "__main__":
    url = input("Enter the website URL: ").strip()
    
    if is_dynamic_website(url):
        print(" Detected as a dynamic website. Using Selenium...")
        data = scrape_with_selenium(url)
    else:
        print(" Detected as a static website. Using Scrapy...")
        data = scrape_with_scrapy(url)

    save_to_csv(data)