import pandas as pd
import re
import os

RAW_PATH = "ebay_tech_deals.csv"
CLEAN_PATH = "cleaned_ebay_deals.csv"

def clean_price(value):
    """Convert price strings like 'US $299.99' → float(299.99)."""
    if not isinstance(value, str):
        return None
    value = re.sub(r'[^\d.,]', '', value)  # keep digits and . or ,
    value = value.replace(',', '')  # remove thousands separator
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
    # extract first number (e.g. '$4.99')
    match = re.search(r'[\d,.]+', value)
    if match:
        try:
            return float(match.group().replace(',', ''))
        except:
            return None
    return None

def main():
    if not os.path.exists(RAW_PATH):
        print(f"[ERROR] File {RAW_PATH} not found.")
        return

    df = pd.read_csv(RAW_PATH)
    print(f"[INFO] Loaded {len(df)} rows from {RAW_PATH}")

    # --- Clean numeric fields ---
    df["price_clean"] = df["price"].apply(clean_price)
    df["original_price_clean"] = df["original_price"].apply(clean_price)
    df["shipping_cost"] = df["shipping"].apply(clean_shipping)

    # --- Calculate discount percentage ---
    def compute_discount(row):
        try:
            if pd.notnull(row["original_price_clean"]) and row["original_price_clean"] > 0 and pd.notnull(row["price_clean"]):
                return round(((row["original_price_clean"] - row["price_clean"]) / row["original_price_clean"]) * 100, 2)
        except:
            return None
        return None

    df["discount_percentage"] = df.apply(compute_discount, axis=1)

    # --- Drop duplicates and reorder columns ---
    df = df.drop_duplicates(subset=["item_url"])
    df = df[[
        "timestamp", "title", "price_clean", "original_price_clean",
        "discount_percentage", "shipping_cost", "item_url"
    ]]

    df.to_csv(CLEAN_PATH, index=False, encoding="utf-8")
    print(f"[SUCCESS] Cleaned data saved to {CLEAN_PATH}")
    print(df.head(5))

if __name__ == "__main__":
    main()