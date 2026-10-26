"""Plotly figures for the dashboard; no Streamlit code here.

Each function takes a DataFrame from analysis.py and returns a figure, so the
charts can be built and checked without running the app.
"""
import plotly.graph_objects as go

from .constants import COMPANIES

# One fixed color per ticker, used in every view (validated categorical palette,
# assigned in the ticker order from constants.py, never by rank)
TICKER_COLORS = {
    'AAPL': '#2a78d6', 'ADBE': '#eb6834', 'AMZN': '#1baf7a', 'GOOGL': '#eda100',
    'META': '#e87ba4', 'MSFT': '#008300', 'NVDA': '#6250d6', 'TSLA': '#e34948',
}

RELATIVE_TITLE = 'Relative price performance — first trading day of period = 100'


def relative_price_chart(indexed):
    """Eight lines of adjusted close indexed to 100 (input: analysis.indexed_prices)."""
    fig = go.Figure()
    for symbol, company in COMPANIES.items():
        stock = indexed[indexed['symbol'] == symbol]
        if stock.empty:
            continue
        # customdata carries the extra hover fields that are not on the axes
        fig.add_trace(go.Scatter(
            x=stock['date'], y=stock['indexed_price'], mode='lines', name=symbol,
            line={'color': TICKER_COLORS[symbol], 'width': 2},
            customdata=list(zip([company] * len(stock), stock['period_change'])),
            hovertemplate=(f'<b>{symbol}</b> (%{{customdata[0]}})<br>'
                           'Date: %{x|%Y-%m-%d}<br>'
                           'Indexed price: %{y:.2f}<br>'
                           'Change since first day: %{customdata[1]:.2%}<extra></extra>'),
        ))
    # Reference line: above 100 = up since the first day of the period, below = down
    fig.add_hline(y=100, line={'color': 'gray', 'width': 1, 'dash': 'dash'})
    fig.update_layout(title=RELATIVE_TITLE, xaxis_title='Date',
                      yaxis_title='Indexed adjusted close (first day = 100)',
                      legend_title_text='Ticker', hovermode='closest')
    return fig


def detail_chart(series, symbol):
    """Unadjusted close for one stock, with flagged days marked (input: analysis.stock_series)."""
    color = TICKER_COLORS[symbol]
    # Same hover fields on the line and on the flag markers
    customdata = list(zip(series['high'], series['low'], series['daily_range_pct'],
                          series['is_flagged'].map({True: 'Yes', False: 'No'}),
                          series['co_flag_count']))
    hover = (f'<b>{symbol}</b><br>'
             'Date: %{x|%Y-%m-%d}<br>'
             'Close: $%{y:,.2f}<br>'
             'High: $%{customdata[0]:,.2f}<br>'
             'Low: $%{customdata[1]:,.2f}<br>'
             'Daily range: %{customdata[2]:.2%}<br>'
             'Flagged: %{customdata[3]}<br>'
             'Co-flag count: %{customdata[4]} of 8<extra></extra>')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=series['date'], y=series['close'], mode='lines', name=f'{symbol} close',
        line={'color': color, 'width': 2}, customdata=customdata, hovertemplate=hover,
    ))

    flagged = series[series['is_flagged']]
    if not flagged.empty:
        flag_data = [row for row, is_flag in zip(customdata, series['is_flagged']) if is_flag]
        # Diamonds with a dark outline so flagged days stand out from the line
        fig.add_trace(go.Scatter(
            x=flagged['date'], y=flagged['close'], mode='markers', name='Flagged day',
            marker={'symbol': 'diamond', 'size': 11, 'color': color,
                    'line': {'color': '#222222', 'width': 1.5}},
            customdata=flag_data, hovertemplate=hover,
        ))

    fig.update_layout(title=f'{COMPANIES[symbol]} ({symbol}) closing price',
                      xaxis_title='Date', yaxis_title='Close (USD)', hovermode='closest')
    return fig
