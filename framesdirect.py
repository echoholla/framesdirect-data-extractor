# FramesDirect Scraper — Capstone Requirement Version
# ============================================================
# Extract exactly: Brand, Product_Name, Former_Price, Current_Price (numbers only), Discount
# Stack: Selenium (navigation) + BeautifulSoup (parsing)
# Flow: Setup → Visit → Wait (inline) → Parse → Save → Quit
# Output: CSV + JSON (only required fields)
# ------------------------------------------------------------

# Libraries Used
import csv
import json
import re
import time

# Selenium imports to drive Chrome
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Step 1 - Configuration and WebDriver Setup
print("Setting up webdriver...")
chrome_option = Options()
chrome_option.add_argument("--headless")        # run browser in headless mode (no UI)
chrome_option.add_argument("--disable-gpu")     # stability
chrome_option.add_argument("--no-sandbox")      # needed on some OS setups
chrome_option.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.265 Safari/537.36"
)
print("done setting up..")

print("Installing Chrome WD")
service = Service(ChromeDriverManager().install())  # download driver matching your Chrome
print("Final Setup")
driver = webdriver.Chrome(service=service, options=chrome_option)
wait = WebDriverWait(driver, 20)
print("Done")

# Step 1.5 - Navigate to the catalog page
START_URL = "https://www.framesdirect.com/eyeglasses/"
print(f"Visiting {START_URL}")
driver.get(START_URL)

# Wait for product tiles to load
try:
    print("Waiting for product tiles to load")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.prod-holder")))
    print("Done...Proceed to parse the data")
except (TimeoutError, Exception) as e:
    print(f"Error waiting for {START_URL}: {e}")
    driver.quit()
    print("Closed")
    raise SystemExit(1)

# Step 2 - Data Parsing and Extraction
all_products = []   # master list across all pages
page_num = 1        # track current page number
NUM = re.compile(r"[\d,.]+")  # numbers-only helper (e.g., 1,234.56)

while True:
    # Nudge lazy-load: scroll down a bit
    for _ in range(2):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.0)

    # Parse current DOM with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Collect product tiles
    product_tiles = soup.select("div.prod-holder")
    print(f"[Page {page_num}] Raw tiles found: {len(product_tiles)}")

    # Extract data from each tile
    data_batch = []
    for tile in product_tiles:
        # --- Brand & Product Name (prefer data-description) ---
        brand, name = None, None
        desc = tile.get("data-description") or ""
        if desc:
            parts = desc.split("_")
            if len(parts) >= 2:
                brand = parts[0].strip()
                name = parts[1].replace(".", " ").replace("_", " ").strip()

        # Fallbacks (visible text)
        if not name:
            nm = tile.select_one(".prod-title.prod-name, [class*='name'], [class*='title']")
            if nm:
                name = re.sub(r"\s+", " ", nm.get_text(strip=True))
        if not brand:
            bn = tile.select_one(".catalog-name, .brand, .product-brand, [class*='brand']")
            if bn:
                brand = re.sub(r"\s+", " ", bn.get_text(strip=True))

        # --- Prices (numbers only) ---
        current_price = None
        former_price = None

        # Current / offer price
        for node in tile.select("span.price, [data-testid*='current'], [class*='offer']"):
            m = NUM.search(node.get_text(" ", strip=True))
            if m:
                current_price = float(m.group(0).replace(",", ""))
                break

        # Former / list / original price
        for node in tile.select(".product-list-price, [class*='original'], [class*='list'], s, del, [data-testid*='original']"):
            m = NUM.search(node.get_text(" ", strip=True))
            if m:
                former_price = float(m.group(0).replace(",", ""))
                break

        # --- Discount ---
        discount = None
        disc_node = tile.select_one(".discount-badge, [class*='badge'][class*='discount'], [class*='off']")
        if disc_node:
            discount = re.sub(r"\s+", " ", disc_node.get_text(strip=True))
        else:
            blob = tile.get_text(" ", strip=True)
            m = re.search(r"\b\d{1,2}%\s*off\b", blob, flags=re.I)
            if m:
                discount = m.group(0)

        # Only add meaningful rows
        if brand or name:
            data_batch.append({
                "Brand": brand,
                "Product_Name": name,
                "Former_Price": former_price,
                "Current_Price": current_price,
                "Discount": discount
            })

    # After finishing this page's tiles
    print(f"[Page {page_num}] New products parsed: {len(data_batch)}")
    all_products.extend(data_batch)

    # Pagination: try to click "Next"
    progressed = False
    try:
        next_el = driver.find_element(By.LINK_TEXT, "Next")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", next_el)
        time.sleep(0.3)
        next_el.click()
        progressed = True
    except Exception:
        try:
            next_el = driver.find_element(
                By.CSS_SELECTOR,
                "a[aria-label='Next'], button[aria-label='Next'], "
                ".pagination .next a, .pagination-next a, li.next a, [rel='next']"
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", next_el)
            time.sleep(0.3)
            next_el.click()
            progressed = True
        except Exception:
            progressed = False

    if progressed:
        page_num += 1
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.prod-holder")))
        except (TimeoutError, Exception) as e:
            print(f"Pagination wait failed: {e}")
            break
    else:
        print("No more pages detected.")
        break

# Step 3 - Save outputs
if all_products:
    columns = list(all_products[0].keys())
    with open('framesdirect_data.csv', mode='w', newline='', encoding='utf-8') as csv_file:
        dict_writer = csv.DictWriter(csv_file, fieldnames=columns)
        dict_writer.writeheader()
        dict_writer.writerows(all_products)
    print(f"Saved {len(all_products)} records to CSV")

    with open('framesdirect_data.json', mode='w', encoding='utf-8') as json_file:
        json.dump(all_products, json_file, indent=2, ensure_ascii=False)
    print(f"Saved {len(all_products)} records to JSON")
else:
    print("No products extracted. Nothing to save.")

# Close the browser
driver.quit()
print("End of Web Extraction")
