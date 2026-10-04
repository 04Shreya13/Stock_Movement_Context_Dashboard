import pandas as pd

# Load original data
filings = pd.read_parquet("Data/filings.parquet")
news = pd.read_parquet("Data/news.parquet")
prices = pd.read_parquet("Data/prices.parquet")

# Create cleaned copies
filing_new = filings.copy()
news_new = news.copy()
price_new = prices.copy()

# Convert dates to datetime
filing_new["date"] = pd.to_datetime(filing_new["date"], errors="coerce")
news_new["date"] = pd.to_datetime(news_new["date"], errors="coerce")
price_new["date"] = pd.to_datetime(price_new["date"], errors="coerce")

# Verify date conversion
assert filing_new["date"].isna().sum() == 0
assert news_new["date"].isna().sum() == 0
assert price_new["date"].isna().sum() == 0

# Merge prices and news
price_news = price_new.merge(
    news_new,
    on=["symbol", "date"],
    how="left",
    validate="one_to_one",
    suffixes=("_price", "_news")
)

# Calculate daily range
price_new["daily_range"] = price_new["high"] - price_new["low"]

# Create 50-row cleaned sample
cleaned_sample = price_new.nlargest(50, "daily_range")
cleaned_sample.to_csv("cleaned_sample.csv", index=False)
print("Data cleaning completed successfully.")