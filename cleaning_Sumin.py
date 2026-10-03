import pandas as pd

# Load original data
prices = pd.read_parquet("prices.parquet")
news = pd.read_parquet("news.parquet")
filings = pd.read_parquet("filings.parquet")

# Preserve original data and create cleaning copies
prices_clean = prices.copy()
news_clean = news.copy()
filings_clean = filings.copy()

# Convert date columns to datetime
prices_clean["date"] = pd.to_datetime(prices_clean["date"])
news_clean["date"] = pd.to_datetime(news_clean["date"])
filings_clean["date"] = pd.to_datetime(filings_clean["date"])

# Select five verification records
sample_indices = [0, 1, 100, 1000, 2655]

# Select 45 additional reproducible records
remaining_sample = prices_clean.drop(index=sample_indices).sample(
    n=45,
    random_state=42
)

# Create the 50-row cleaned sample
prices_sample = pd.concat([
    prices_clean.loc[sample_indices],
    remaining_sample
]).sort_index()

# Save cleaned sample
prices_sample.to_csv("prices_cleaned_sample.csv", index=False)

print("Cleaning complete.")
print("Sample size:", len(prices_sample)) 