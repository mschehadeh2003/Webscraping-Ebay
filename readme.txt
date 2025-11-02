


 Overview

This project automates the collection, cleaning, and analysis of eBay Global Tech Deals.
It consists of four main tasks:

Task 1: scraper.py
    Scrapes live product data (title, price, original price, shipping, URL) using Selenium and multithreading.

Task 2: .github/workflows/scraper.yml
    Runs the scraper automatically every 3 hours via GitHub Actions.

Task 3: clean_data.py
    Cleans and normalizes prices, computes discount percentages, and produces cleaned_ebay_deals.csv.

Task 4: EDA.ipynb
    Exploratory Data Analysis notebook with descriptive statistics and visualizations.


Methodology
1. Data Collection:
   Selenium in headless Chrome scrolls through the eBay Tech Deals page, visits each product, and extracts structured data.

2. Automation:
   A GitHub Actions workflow executes the scraper every 3 hours, commits updates, and pushes new data.

3. Cleaning & Processing:
   Regex-based parsing converts "US $299.99" → 299.99 (float) and standardizes shipping values.
   A new feature discount_percentage = ((original_price − price) / original_price) × 100 is computed.

4. EDA:
   The cleaned dataset is explored using pandas, matplotlib, and seaborn to visualize pricing trends, discount distributions, and relationships.


Key Findings
1. Price Distribution: Most products cluster under $300, with a few premium items above $1000.
2. Discount Range: Typical discounts fall between 10 – 25 %, with occasional deep cuts beyond 70 %.
3. Correlations: Original and discounted prices are strongly correlated (≈ 0.78). Discount % has a mild negative correlation with price (≈ −0.42).
4. Shipping Effect: Deals with paid shipping averaged higher discounts (~43 %) than free-shipping offers.


Challenges Faced
- Dynamic HTML: eBay renders prices and shipping asynchronously; explicit WebDriverWait calls were required.
- Anti-bot protection: Occasional headless-browser detection; solved by adding custom user-agent and delays.
- ChromeDriver timeouts: Mitigated by limiting thread count (4) and caching chromedriver locally.


Potential Improvements

- Add sentiment analysis on item titles (e.g., “refurbished”, “new”) to classify deal quality.
- Integrate a database (SQLite / PostgreSQL) for continuous historical tracking.
- Build an interactive Streamlit dashboard showing price and discount trends over time.



