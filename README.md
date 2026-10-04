# Stock Movement Context Dashboard

## Module 6: Data Cleaning

**Project goal:** Help an investor-relations analyst identify unusually wide daily price movements across eight large-cap companies and review relevant news and filing information around those movements for human follow-up.

**Business question:** Which companies and dates have unusually wide daily price ranges, and what news highlights and recent 10-K or 10-Q filing information are available around those movements?

**Main metric:** Daily price range = high price − low price, measured in U.S. dollars per share.

## Data and Cleaning

**Data source:** HERCULEAN dataset from TheFinAI on Hugging Face  

**Dataset version:** No version specified  

**Download date:** [October 2, 2026]

The raw files are `prices.parquet`, `news.parquet`, and `filings.parquet`, stored in `Data/`. These raw files remain unchanged; the script works with copies in memory.

`data_cleaning.py` converts and validates dates, merges prices with news by symbol and date, and calculates daily price ranges. The expected output is `cleaned_sample.csv`, containing the 50 price records with the largest daily price ranges because unusually wide price movements are the focus of the project. This sample contains price data and the calculated range; reviewing news and filings provides context for the broader project.

## Run the Script

Dependencies are listed in `requirements.txt`. With Python installed and the three raw files in `Data/`, run these commands from the project directory:

```bash
python -m pip install -r requirements.txt
python data_cleaning.py
```

The script writes `cleaned_sample.csv` to the project directory.

## Git Submission Details

- **Branch name:** `branch_Victor`
- **Branch URL:** https://github.com/04Shreya13/Stock_Movement_Context_Dashboard/tree/branch_Victor
- **Commit ID:** b8e658dacdf568b996f93cf4758dddccf8ef3677
