from playwright.sync_api import sync_playwright
from selectolax.parser import HTMLParser
import spacy
import re
import time

# Load NLP model
nlp = spacy.load("en_core_web_sm")

def extract_text_blocks(tree):
    blocks = tree.css('p, span, li, div, h1, h2')
    texts = [b.text(strip=True) for b in blocks if b.text(strip=True)]
    return ' '.join(texts[:500])  # Grab more context

def extract_entities(text):
    doc = nlp(text)
    price_regex = r"(?:₦|₹|\$|€|£)\s?\d[\d,]*(?:\.\d{2})?"
    prices = re.findall(price_regex, text)

    entities = {
        "product_name": None,
        "price": prices[0] if prices else None,
        "brands": [],
    }

    for ent in doc.ents:
        if ent.label_ == "ORG":
            entities["brands"].append(ent.text)
        if ent.label_ == "PRODUCT" and not entities["product_name"]:
            entities["product_name"] = ent.text

    return entities

def scrape_product(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112 Safari/537.36"
        )
        page = context.new_page()
        page.goto(url, wait_until='networkidle')
        time.sleep(2)  # give JS time to render

        html = page.content()
        browser.close()

    tree = HTMLParser(html)
    text = extract_text_blocks(tree)
    entities = extract_entities(text)

    return {
        "url": url,
        "product_name": entities["product_name"],
        "price": entities["price"],
        "brand": entities["brands"][0] if entities["brands"] else None,
        "raw_text_sample": text[:500]
    }

# 👇 Test
url = "https://www.jumia.com.ng/la-riviera-sparkling-rose-wine-75cl-278996082.html"
print(scrape_product(url))
