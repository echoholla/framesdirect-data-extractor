#     Framesdirect-data-extractor: Report

# overview

The goal of this project was to build a Python scraper using Selenium (for navigation and dynamic content loading) and BeautifulSoup (for parsing) to extract structured product data from FramesDirect’s eyeglasses catalog. Specifically, the capstone required extracting:

Brand Name

Product Name

Original Price (Former_Price)

Current Price (Current_Price)

Discount

The data was then stored in both CSV and JSON formats for further analysis.

#  Challenges & Decisions

- Dynamic Content Loading

The website loads product tiles dynamically using JavaScript. A standard requests approach only retrieved empty shells without product data.

Solution: Implemented Selenium WebDriver with explicit waits (WebDriverWait) to allow the product tiles (div.prod-holder) to fully load before parsing.

- Lazy Loading / Pagination

Products were revealed progressively as the user scrolls, and additional pages required navigation via a “Next” button.

Solution: Automated scrolling with driver.execute_script("window.scrollTo...") to trigger lazy loading, and added logic to detect and click “Next” until no more pages were found.

- Price Data Not Extracted (Null Values)

Although brand and product names were extracted correctly, many products returned null for Former_Price and Current_Price.

Cause: FramesDirect appears to encode or load price information asynchronously, sometimes only on the Product Detail Page (PDP) rather than the catalog. The HTML of the catalog tiles often lacked visible price nodes.

Solution (partial): Multiple CSS selectors were tested (span.price, .product-list-price, s, del), and regex was used to isolate numeric values. Discounts were sometimes captured (30% Off, 50% Off), but reliable price scraping may require navigating into PDP pages.

#  Why CSS Selectors Instead of Only Class Names (like catalog)

Initial attempts using By.CLASS_NAME on elements such as catalog-page did not work because:

Each product tile is in a div tags

class names sometimes appear on multiple unrelated elements.

Complex elements required chained selectors (e.g., .discount-badge span inside a product tile).

Solution: Used CSS selectors (div.prod-holder, span.price, .product-list-price) because they allow:

Precise targeting of nested elements.

Better flexibility when the site changes styles.

This made extraction more robust and adaptable compared to relying only on simple class name lookups.

#  Data Cleaning

Raw strings often contained underscores, extra spaces, or non-numeric symbols.

Solution: Applied regex ([\d,.]+) for numbers and used string replacements to normalize product names and discount values.

#  Outcomes

Successfully scraped brands, product names, and discounts for hundreds of eyeglass models.

Price fields remain incomplete due to asynchronous/encoded rendering in catalog view. Extracting prices reliably would require extending the scraper to enter individual Product Detail Pages (PDPs).

Delivered structured output in CSV and JSON formats.

#  Lessons Learned

Many modern e-commerce sites hide or encode sensitive data (like prices) in dynamic scripts, requiring advanced scraping strategies (e.g., PDP navigation, API inspection, or browser network monitoring).

Clean, modular code (separating setup, parsing, and saving) made debugging easier and allowed quick iteration on selectors.