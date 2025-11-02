# clean_data.py
# Incremental version: only cleans and appends new rows

import pandas as pd
import re
import os

RAW_PATH = "ebay_tech_deals.csv"
CLEAN_PATH = "cleaned_ebay_deals.csv"

def clean_price(value):
    """Convert price strings like 'US $299.99' → float(299.99)."""
    if not isinstance(value, str):
        return None
    value = re.sub(r'[^\d.,]', '', value).replace(',', '')
    try:
        return float(value)
    except ValueError:
        return None

def clean_shipping(value):
    """Standardize shipping cost."""
    if not isinstance(value, str) or value.strip() == "":
        return None
    if "Free" in value:
        return 0.0
    match = re.search(r'[\d,.]+', value)
    if match:
        try:
            return float(match.group().replace(',', ''))
        except:
            return None
    return None

def compute_discount(row):
    try:
        if pd.notnull(row["original_price_clean"]) and row["original_price_clean"] > 0 and pd.notnull(row["price_clean"]):
            return round(((row["original_price_clean"] - row["price_clean"]) / row["original_price_clean"]) * 100, 2)
    except:
        return None
    return None

def main():
    if not os.path.exists(RAW_PATH):
        print(f"[ERROR] File {RAW_PATH} not found.")
        return

    raw_df = pd.read_csv(RAW_PATH)
    print(f"[INFO] Loaded {len(raw_df)} raw rows.")

    if os.path.exists(CLEAN_PATH):
        cleaned_df = pd.read_csv(CLEAN_PATH)
        existing_urls = set(cleaned_df["item_url"])
        new_rows = raw_df[~raw_df["item_url"].isin(existing_urls)]
        print(f"[INFO] Found {len(new_rows)} new rows to clean.")
    else:
        cleaned_df = pd.DataFrame()
        new_rows = raw_df
        print(f"[INFO] No existing cleaned file found. Cleaning all rows.")

    if new_rows.empty:
        print("[INFO] No new data to clean. Exiting.")
        return

    # Clean new rows only
    new_rows["price_clean"] = new_rows["price"].apply(clean_price)
    new_rows["original_price_clean"] = new_rows["original_price"].apply(clean_price)
    new_rows["shipping_cost"] = new_rows["shipping"].apply(clean_shipping)
    new_rows["discount_percentage"] = new_rows.apply(compute_discount, axis=1)

    # Select relevant columns
    new_rows = new_rows[[
        "timestamp", "title", "price_clean", "original_price_clean",
        "discount_percentage", "shipping_cost", "item_url"
    ]]

    # Combine old + new
    if not cleaned_df.empty:
        final_df = pd.concat([cleaned_df, new_rows], ignore_index=True)
    else:
        final_df = new_rows

    final_df.drop_duplicates(subset=["item_url"], inplace=True)
    final_df.to_csv(CLEAN_PATH, index=False, encoding="utf-8")

    print(f"[SUCCESS] Cleaned file updated → {len(final_df)} total rows now.")

if __name__ == "__main__":
    main()
