# Stock Movement Context Dashboard

## Project Overview

This project analyzes stock price movements for eight major technology companies using stock prices, news highlights, and SEC filing data.

## Data Source

- Source: TheFinAI/Herculean
- Files used:
  - `prices.parquet`
  - `news.parquet`
  - `filings.parquet`
- The original parquet files are preserved without modification.
- The data was downloaded from the Herculean dataset on Hugging Face.

## Data Cleaning

The cleaning process is documented in `cleaning_Sumin.ipynb`.

The main cleaning decision was to convert the `date` columns in all three datasets from object to datetime. Checks were also performed for missing values, duplicates, repeated IDs, suspicious price and volume values, and invalid dates.

## How to Run

1. Open `cleaning_Sumin.ipynb`.
2. Select the project Python environment.
3. Restart the kernel.
4. Run all cells from top to bottom.

## Expected Output

Running the notebook creates:

- `prices_cleaned_sample.csv` — a reproducible 50-row sample of the cleaned prices data.

## Branch

Branch name: `branch_Sumin`

Branch URL: `https://github.com/04Shreya13/Stock_Movement_Context_Dashboard/tree/branch_Sumin`

Commit ID: `12a7edd`