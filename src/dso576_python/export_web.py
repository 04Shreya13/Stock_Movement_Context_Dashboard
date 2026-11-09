"""Write web/data.js, the only data file the HTML dashboard reads.

The browser only displays what is written here. Flags, rankings, news windows
and filing lookups are all decided by the tested functions in analysis.py, so
the website cannot disagree with them.

Run from the project root:
    PYTHONPATH=src uv run python -m dso576_python.export_web
"""
import json
from pathlib import Path

import pandas as pd

from .analysis import (filing_age_days, filing_context, flagged_days, indexed_prices,
                       news_context, year_coverage, year_summary)
from .constants import COMPANIES, PERIODS
from .data_loader import load_cleaned, validate_data

OUTPUT_FILE = 'web/data.js'


def clean_value(value):
    """Turn one pandas value into a plain value that JSON can store."""
    # JSON has no NaN or NaT, so every kind of missing value becomes null
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.strftime('%Y-%m-%d')
    # NumPy numbers are not JSON-friendly; .item() gives a normal Python number
    if hasattr(value, 'item'):
        return value.item()
    return value


def table_to_records(frame, columns):
    """Turn a DataFrame into a list of plain dictionaries."""
    records = []
    for row in frame[columns].to_dict('records'):
        record = {}
        for column in columns:
            record[column] = clean_value(row[column])
        records.append(record)
    return records


def build_coverage(prices):
    coverage = {}
    for period in PERIODS:
        info = year_coverage(prices, period)
        coverage[str(period)] = {
            'label': info['coverage_label'],
            'start_date': clean_value(info['start_date']),
            'end_date': clean_value(info['end_date']),
            'companies': info['companies'],
            'trading_dates': info['trading_dates'],
        }
    return coverage


def build_summaries(prices, context):
    columns = ['symbol', 'company', 'trading_days', 'last_close', 'period_change',
               'flagged_days', 'largest_daily_range']
    summaries = {}
    for period in PERIODS:
        summary = year_summary(prices, context, period)
        summaries[str(period)] = table_to_records(summary, columns)
    return summaries


def build_indexed(prices):
    """One list of dates per period, plus one list of values per stock."""
    indexed = {}
    for period in PERIODS:
        frame = indexed_prices(prices, period)
        series = {}
        dates = []
        for symbol in COMPANIES:
            stock = frame.loc[frame['symbol'].eq(symbol)]
            dates = [clean_value(day) for day in stock['date']]
            series[symbol] = {
                'indexed': [clean_value(value) for value in stock['indexed_price']],
                'change': [clean_value(value) for value in stock['period_change']],
            }
        indexed[str(period)] = {'dates': dates, 'series': series}
    return indexed


def build_flagged(context):
    """Flagged dates in display order; the first one is the default selection."""
    flagged = {}
    for period in PERIODS:
        flagged[str(period)] = {}
        for symbol in COMPANIES:
            days = flagged_days(context, period, symbol)
            flagged[str(period)][symbol] = [clean_value(day) for day in days['date']]
    return flagged


def build_day(row, news, filings):
    """Everything the page needs about one stock on one trading day."""
    symbol = row['symbol']
    day = row['date']
    nearby_news = news_context(news, symbol, day)
    found = filing_context(filings, symbol, day)
    filing = found['filing']
    annual = found['annual_risk_fallback']

    filing_id = None
    age_days = None
    if filing is not None:
        filing_id = filing['id']
        age_days = filing_age_days(filing['date'], day)

    annual_id = None
    if annual is not None:
        annual_id = annual['id']

    return {
        'date': clean_value(day),
        'close': clean_value(row['close']),
        'high': clean_value(row['high']),
        'low': clean_value(row['low']),
        'daily_range_pct': clean_value(row['daily_range_pct']),
        'is_flagged': clean_value(row['is_flagged']),
        'co_flag_count': clean_value(row['co_flag_count']),
        'news_ids': [clean_value(news_id) for news_id in nearby_news['id']],
        'filing_id': clean_value(filing_id),
        'annual_risk_id': clean_value(annual_id),
        'filed_same_day': found['filed_same_day'],
        'filing_age_days': age_days,
    }


def build_days(context, news, filings):
    days = {}
    for symbol in COMPANIES:
        stock = context.loc[context['symbol'].eq(symbol)].sort_values('date')
        days[symbol] = []
        for row in stock.to_dict('records'):
            days[symbol].append(build_day(row, news, filings))
    return days


def build_web_data(data):
    """Return everything the website shows, as plain Python values."""
    prices = data['prices']
    context = data['price_context']
    news_columns = ['id', 'symbol', 'date', 'highlights', 'highlights_low_info']
    filing_columns = ['id', 'symbol', 'date', 'document_type', 'mda_content',
                      'risk_content', 'risk_refers_to_10k']
    return {
        'companies': COMPANIES,
        'periods': [str(period) for period in PERIODS],
        'coverage': build_coverage(prices),
        'summary': build_summaries(prices, context),
        'indexed': build_indexed(prices),
        'flagged': build_flagged(context),
        'days': build_days(context, data['news'], data['filings']),
        'news': table_to_records(data['news'], news_columns),
        'filings': table_to_records(data['filings'], filing_columns),
    }


def main():
    data = load_cleaned()
    validate_data(data)
    web_data = build_web_data(data)
    text = 'window.STOCK_DATA=' + json.dumps(web_data, ensure_ascii=False, separators=(',', ':')) + ';\n'
    Path(OUTPUT_FILE).write_text(text, encoding='utf-8')
    print(f'Wrote {OUTPUT_FILE} ({len(text.encode("utf-8")):,} bytes)')


if __name__ == '__main__':
    main()
