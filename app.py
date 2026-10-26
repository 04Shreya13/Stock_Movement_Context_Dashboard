"""Stock Movement Context Dashboard (Phase 3 interface, built from BUILD_SPEC.md).

Run from the project root:
    PYTHONPATH=src uv run streamlit run app.py

This file only handles controls, state and layout. Numbers come from
dso576_python.analysis and figures from dso576_python.charts.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

from dso576_python import analysis
from dso576_python.charts import detail_chart, relative_price_chart
from dso576_python.constants import COMPANIES, FULL_RANGE, PERIODS
from dso576_python.data_loader import REQUIRED, load_cleaned

DATA_DIR = 'data/cleaned'
EXCERPT_CHARS = 2000  # filing text shown before the "show the rest" expander
MISSING = 'Unavailable'  # shown for any missing value, never 0

TITLE = 'Stock Movement Context Dashboard'
SUBTITLE = ('Compare eight stocks, identify unusually wide daily ranges, '
            'and review related news and company filings.')
NO_FLAGS = 'No flagged trading days for this stock in the selected period.'
NO_NEWS = 'No news summaries are available for this company in the selected date window.'
NO_FILING = 'No eligible 10-K or 10-Q filing is available for this company as of the selected date.'
CO_FLAG_CAPTION = 'A higher count may suggest shared conditions; it does not establish a market-wide cause.'


# ---------- data loading ----------

def file_signature(directory):
    """Path, size and modified time of each canonical file.

    Passed to the cached loader so the cache refreshes when a file changes.
    """
    signature = []
    for name in REQUIRED:
        path = Path(directory) / f'{name}.parquet'
        if path.exists():
            info = path.stat()
            signature.append((str(path), info.st_size, info.st_mtime))
        else:
            signature.append((str(path), None, None))
    return tuple(signature)


@st.cache_data
def load_data(directory, signature):
    # `signature` is unused inside; it is part of the cache key on purpose
    return load_cleaned(directory)


# ---------- small display helpers ----------

def period_label(period):
    return 'Full range' if period == FULL_RANGE else str(period)


def stock_label(symbol):
    return f'{COMPANIES[symbol]} ({symbol})'


def fmt_date(value):
    return MISSING if pd.isna(value) else pd.Timestamp(value).strftime('%Y-%m-%d')


def fmt_usd(value):
    return MISSING if pd.isna(value) else f'${value:,.2f}'


def fmt_pct(value):
    # Backend ratios are decimals; format once here (0.05 -> 5.00%)
    return MISSING if pd.isna(value) else f'{value:.2%}'


def show_long_text(text):
    """Plain text (so $ amounts display literally): ~2,000 characters, then an expander."""
    if len(text) <= EXCERPT_CHARS:
        st.text(text, width='stretch')
        return
    # Cut at the last space before the limit so no word is split in half
    cut = text.rfind(' ', 0, EXCERPT_CHARS)
    if cut == -1:
        cut = EXCERPT_CHARS
    st.text(text[:cut], width='stretch')
    with st.expander('Show the rest'):
        st.text(text[cut:].lstrip(), width='stretch')


# ---------- page sections ----------

def show_overview(prices, context, period):
    """Sections 2-4: coverage banner, relative price chart, summary table."""
    coverage = analysis.year_coverage(prices, period)
    st.info(f"{coverage['coverage_label']}: {fmt_date(coverage['start_date'])} to "
            f"{fmt_date(coverage['end_date'])} · {coverage['companies']} companies · "
            f"{coverage['trading_dates']} trading dates")

    indexed = analysis.indexed_prices(prices, period)
    st.plotly_chart(relative_price_chart(indexed), width='stretch')

    summary = analysis.year_summary(prices, context, period)
    table = summary[['company', 'symbol', 'last_close', 'period_change', 'flagged_days',
                     'largest_daily_range', 'trading_days']]
    # Numbers stay numeric so column sorting works; formatting happens in column_config
    st.dataframe(table, hide_index=True, placeholder=MISSING, column_config={
        'company': 'Company',
        'symbol': 'Ticker',
        'last_close': st.column_config.NumberColumn('Last close', format='dollar'),
        'period_change': st.column_config.NumberColumn('Change over period', format='percent'),
        'flagged_days': st.column_config.NumberColumn('Flagged days', format='%d'),
        'largest_daily_range': st.column_config.NumberColumn('Largest daily range', format='percent'),
        'trading_days': st.column_config.NumberColumn('Trading days', format='%d'),
    })


def choose_flagged_day(flags, period, symbol):
    """Section 6: flagged-day table. Returns the selected row, or None if no flags."""
    st.subheader('Flagged days')
    if flags.empty:
        st.info(NO_FLAGS)
        return None

    table = flags[['date', 'close', 'high', 'low', 'daily_range_pct', 'co_flag_count']]
    # A new key per period and stock resets the selection to the default
    # (row 0 = largest range, ties -> earliest date, as sorted by analysis.flagged_days)
    event = st.dataframe(
        table, hide_index=True, placeholder=MISSING,
        key=f'flagged_{period}_{symbol}', on_select='rerun', selection_mode='single-row',
        selection_default={'selection': {'rows': [0]}},
        column_config={
            'date': st.column_config.DateColumn('Date', format='YYYY-MM-DD'),
            'close': st.column_config.NumberColumn('Close', format='dollar'),
            'high': st.column_config.NumberColumn('High', format='dollar'),
            'low': st.column_config.NumberColumn('Low', format='dollar'),
            'daily_range_pct': st.column_config.NumberColumn('Daily range', format='percent'),
            'co_flag_count': st.column_config.NumberColumn('Co-flag count', format='%d'),
        })
    rows = event.selection.rows
    # If the user clears the selection, fall back to the default day
    position = rows[0] if rows else 0
    return flags.iloc[position]


def show_selected_day(context, row, symbol):
    """Section 7: selected-day metrics and the eight-stock comparison."""
    st.subheader(f'{stock_label(symbol)} on {fmt_date(row["date"])}')
    columns = st.columns(5)
    columns[0].metric('Close', fmt_usd(row['close']))
    columns[1].metric('High', fmt_usd(row['high']))
    columns[2].metric('Low', fmt_usd(row['low']))
    columns[3].metric('Daily range', fmt_pct(row['daily_range_pct']))
    columns[4].metric('Stocks flagged', f"{int(row['co_flag_count'])} of 8 stocks flagged")

    comparison = analysis.date_comparison(context, row['date'])
    comparison.insert(1, 'company', comparison['symbol'].map(COMPANIES))
    # is_flagged is missing when a stock did not trade that date: keep it missing
    comparison['flag_status'] = comparison['is_flagged'].map({True: 'Flagged', False: 'Not flagged'})
    st.markdown('**All eight stocks on this date**')
    st.dataframe(comparison[['symbol', 'company', 'daily_range_pct', 'flag_status']],
                 hide_index=True, placeholder=MISSING, column_config={
                     'symbol': 'Ticker',
                     'company': 'Company',
                     'daily_range_pct': st.column_config.NumberColumn('Daily range', format='percent'),
                     'flag_status': 'Flag status',
                 })
    st.caption(CO_FLAG_CAPTION)


def show_news(news, symbol, day):
    """Section 8a: news summaries from D-7 through D, newest first."""
    st.subheader('News (selected day and 7 days before)')
    items = analysis.news_context(news, symbol, day)
    if items.empty:
        st.info(NO_NEWS)
        return
    for item in items.itertuples():
        label = f'{fmt_date(item.date)} · AI-generated news summary'
        if item.highlights_low_info:
            label += ' · Limited information'
        # Only the selected day's summary starts open
        with st.expander(label, expanded=(item.date == day)):
            st.text(item.highlights, width='stretch')


def show_filing(filings, symbol, day):
    """Section 8b: latest 10-K or 10-Q filed on or before the selected day."""
    st.subheader('Latest filing')
    result = analysis.filing_context(filings, symbol, day)
    filing = result['filing']
    if filing is None:
        st.info(NO_FILING)
        return

    st.markdown(f"**{filing['document_type']}** filed {fmt_date(filing['date'])}")
    if result['filed_same_day']:
        st.warning('Filed on selected date; publication time unavailable.')

    st.markdown('**MD&A** (Management’s Discussion and Analysis)')
    show_long_text(filing['mda_content'])

    risk_heading = '**Risk Factors**'
    if filing['risk_refers_to_10k']:
        risk_heading += ' · refers to 10-K'
    st.markdown(risk_heading)
    show_long_text(filing['risk_content'])

    annual = result['annual_risk_fallback']
    if annual is not None:
        st.markdown(f"**Risk Factors from the latest 10-K** (filed {fmt_date(annual['date'])})")
        show_long_text(annual['risk_content'])

    st.caption('Filing text is excerpted from the filings, not the complete documents.')


# ---------- main layout ----------

def main():
    st.set_page_config(page_title=TITLE, layout='wide')
    st.title(TITLE)
    st.write(SUBTITLE)

    try:
        data = load_data(DATA_DIR, file_signature(DATA_DIR))
    except (FileNotFoundError, ValueError) as error:
        st.error(f'Could not load the canonical data: {error}')
        st.stop()
    prices, news, filings, context = (data['prices'], data['news'],
                                      data['filings'], data['price_context'])

    # 1. Period selector (changes price views and counts, never flags or thresholds)
    period = st.radio('Period', PERIODS, format_func=period_label, horizontal=True, key='period')

    # 2-4. Coverage banner, relative price chart, summary table
    show_overview(prices, context, period)

    # 5. Stock selector and detail chart (does not filter the overview above)
    st.divider()
    symbol = st.selectbox('Select a stock to investigate', list(COMPANIES),
                          format_func=stock_label, key='symbol')
    series = analysis.stock_series(context, period, symbol)
    st.plotly_chart(detail_chart(series, symbol), width='stretch')

    # 6. Flagged-day table; the only way to choose a day
    flags = analysis.flagged_days(context, period, symbol)
    row = choose_flagged_day(flags, period, symbol)
    if row is None:
        return  # no flags: keep the detail chart, hide sections 7-8

    # 7. Selected-day metrics and eight-stock comparison
    st.divider()
    show_selected_day(context, row, symbol)

    # 8. News and filing panels, side by side
    st.divider()
    day = row['date']
    news_column, filing_column = st.columns(2)
    with news_column:
        show_news(news, symbol, day)
    with filing_column:
        show_filing(filings, symbol, day)


main()
