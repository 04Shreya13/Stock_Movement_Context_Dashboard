/* Controls, state and page updates for the dashboard.

   Every number comes from web/data.js, which is written by the tested Python
   backend (src/dso576_python/export_web.py). This file looks values up and
   formats them; it does not decide what is flagged or which news matches. */

const DATA = window.STOCK_DATA;
const SYMBOLS = Object.keys(DATA.companies);
const SHORTLIST_KEY = 'stock-context-shortlist';
const MISSING = 'Unavailable';

/* One colour per stock, the same everywhere. MSFT, NVDA and TSLA also have
   dashes, because eight colours can't all be told apart by colour alone. */
const STOCK_STYLES = {
  AAPL: { color: '#2a78d6' },
  ADBE: { color: '#eb6834' },
  AMZN: { color: '#1baf7a' },
  GOOGL: { color: '#eda100' },
  META: { color: '#e87ba4' },
  MSFT: { color: '#008300', dash: '7 4' },
  NVDA: { color: '#6250d6', dash: '2 4' },
  TSLA: { color: '#9b1d3a', dash: '10 3 2 3' },
};

const state = {
  period: 'full',
  stock: 'AAPL',
  selected: null,
  chartMode: 'close',
  sortColumn: null,
  sortAscending: true,
  hiddenLines: new Set(),
};

let shortlist = loadShortlist();

/* ---------- small helpers ---------- */

function byId(id) {
  return document.getElementById(id);
}

function escapeHtml(text) {
  const replacements = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  return String(text === null || text === undefined ? '' : text).replace(/[&<>"']/g, function (ch) {
    return replacements[ch];
  });
}

function money(value) {
  if (value === null || value === undefined) return MISSING;
  return '$' + value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function percent(value) {
  if (value === null || value === undefined) return MISSING;
  return (value * 100).toFixed(2) + '%';
}

function signedPercent(value) {
  if (value === null || value === undefined) return MISSING;
  return (value >= 0 ? '+' : '') + percent(value);
}

function showToast(message) {
  byId('toast').textContent = message;
  byId('toast').style.display = 'block';
  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(function () { byId('toast').style.display = 'none'; }, 2600);
}

/* ---------- lookups (no calculations) ---------- */

const dayLookup = {};
SYMBOLS.forEach(function (symbol) {
  dayLookup[symbol] = {};
  DATA.days[symbol].forEach(function (day) { dayLookup[symbol][day.date] = day; });
});

const newsById = {};
DATA.news.forEach(function (item) { newsById[item.id] = item; });

const filingById = {};
DATA.filings.forEach(function (item) { filingById[item.id] = item; });

function daysInPeriod(symbol) {
  return DATA.days[symbol].filter(function (day) {
    return state.period === 'full' || day.date.startsWith(state.period);
  });
}

function flaggedDates() {
  return DATA.flagged[state.period][state.stock];
}

function selectedDay() {
  return state.selected ? dayLookup[state.stock][state.selected] : null;
}

/* The default day is the first flagged date, already ranked by the backend. */
function chooseDefaultDay() {
  const dates = flaggedDates();
  state.selected = dates.length > 0 ? dates[0] : null;
}

/* ---------- overview: relative chart and summary table ---------- */

function renderCoverage() {
  const info = DATA.coverage[state.period];
  byId('coverage').textContent = info.label + ': ' + info.start_date + ' to ' + info.end_date +
    ' · ' + info.companies + ' companies · ' + info.trading_dates + ' trading dates';
}

function renderLegend() {
  let html = '';
  SYMBOLS.forEach(function (symbol) {
    const style = STOCK_STYLES[symbol];
    const isOn = !state.hiddenLines.has(symbol);
    const dash = style.dash ? ' stroke-dasharray="' + style.dash + '"' : '';
    html += '<button class="legend-button' + (isOn ? '' : ' off') + '" data-line="' + symbol + '" aria-pressed="' + isOn + '">' +
      '<svg width="26" height="8" aria-hidden="true"><line x1="1" x2="25" y1="4" y2="4" stroke="' + style.color + '" stroke-width="2"' + dash + '/></svg>' +
      symbol + '</button>';
  });
  byId('relativeLegend').innerHTML = html;
}

function drawRelativeChart() {
  const indexed = DATA.indexed[state.period];
  Charts.drawRelative(byId('relativeChart'), {
    dates: indexed.dates,
    series: indexed.series,
    symbols: SYMBOLS,
    styles: STOCK_STYLES,
    hidden: state.hiddenLines,
    selected: state.stock,
    formatChange: signedPercent,
  });
}

const SUMMARY_COLUMNS = [
  { key: 'company', label: 'Company' },
  { key: 'symbol', label: 'Ticker' },
  { key: 'last_close', label: 'Last close', numeric: true },
  { key: 'period_change', label: 'Change over period', numeric: true },
  { key: 'flagged_days', label: 'Flagged days', numeric: true },
  { key: 'largest_daily_range', label: 'Largest daily range', numeric: true },
  { key: 'trading_days', label: 'Trading days', numeric: true },
];

function summaryRowsInOrder() {
  const rows = DATA.summary[state.period].slice();
  if (state.sortColumn === null) return rows;
  const direction = state.sortAscending ? 1 : -1;
  rows.sort(function (a, b) {
    const first = a[state.sortColumn];
    const second = b[state.sortColumn];
    // Missing values always go last, whichever way the column is sorted
    if (first === null) return 1;
    if (second === null) return -1;
    if (first < second) return -1 * direction;
    if (first > second) return direction;
    return 0;
  });
  return rows;
}

function renderSummary() {
  let head = '<tr>';
  SUMMARY_COLUMNS.forEach(function (column) {
    let sortState = 'none';
    let arrow = '';
    if (state.sortColumn === column.key) {
      sortState = state.sortAscending ? 'ascending' : 'descending';
      arrow = state.sortAscending ? ' ↑' : ' ↓';
    }
    head += '<th aria-sort="' + sortState + '"' + (column.numeric ? ' class="num"' : '') + '>' +
      '<button data-sort="' + column.key + '">' + column.label + arrow + '</button></th>';
  });
  byId('summaryHead').innerHTML = head + '</tr>';

  let body = '';
  summaryRowsInOrder().forEach(function (row) {
    const flagged = row.flagged_days === null ? MISSING : row.flagged_days;
    body += '<tr data-stock="' + row.symbol + '"' + (row.symbol === state.stock ? ' class="chosen"' : '') + '>' +
      '<td><button aria-label="Investigate ' + escapeHtml(row.company) + '">' + escapeHtml(row.company) + '</button></td>' +
      '<td>' + row.symbol + '</td>' +
      '<td class="num">' + money(row.last_close) + '</td>' +
      '<td class="num">' + signedPercent(row.period_change) + '</td>' +
      '<td class="num">' + flagged + '</td>' +
      '<td class="num">' + percent(row.largest_daily_range) + '</td>' +
      '<td class="num">' + row.trading_days + '</td></tr>';
  });
  byId('summaryRows').innerHTML = body;
}

/* ---------- stock section ---------- */

function renderCards() {
  let html = '';
  DATA.summary[state.period].forEach(function (row) {
    const isActive = row.symbol === state.stock;
    html += '<button class="company-card' + (isActive ? ' active' : '') + '" data-stock="' + row.symbol + '" aria-pressed="' + isActive + '">' +
      '<strong><i class="card-key" style="background:' + STOCK_STYLES[row.symbol].color + '"></i>' + row.symbol + '</strong>' +
      '<small>' + escapeHtml(row.company) + '</small>' +
      '<b>' + money(row.last_close) + '</b>' +
      '<em>' + (row.flagged_days === null ? MISSING : row.flagged_days) + ' flagged days</em></button>';
  });
  byId('companyCards').innerHTML = html;
}

function renderEvents() {
  const dates = flaggedDates();
  byId('eventCount').textContent = dates.length;
  if (dates.length === 0) {
    byId('eventRows').innerHTML = '<tr><td colspan="6"><div class="empty">No flagged trading days for this stock in the selected period.<br>' +
      'Choose another period or stock, or click the chart above to inspect any day.</div></td></tr>';
    return;
  }
  let html = '';
  dates.forEach(function (date) {
    const day = dayLookup[state.stock][date];
    html += '<tr data-date="' + date + '"><td><button aria-label="Inspect ' + date + '">' + date + '</button></td>' +
      '<td class="num">' + money(day.close) + '</td><td class="num">' + money(day.high) + '</td><td class="num">' + money(day.low) + '</td>' +
      '<td class="num range">' + percent(day.daily_range_pct) + '</td><td class="num">' + day.co_flag_count + ' / 8</td></tr>';
  });
  byId('eventRows').innerHTML = html;
}

function drawDetailChart() {
  Charts.drawDetail(byId('detailChart'), {
    symbol: state.stock,
    rows: daysInPeriod(state.stock),
    mode: state.chartMode,
    selected: state.selected,
    onSelect: selectDay,
    tooltipRows: function (day) {
      return [
        { value: money(day.close), label: 'close' },
        { value: money(day.high), label: 'high' },
        { value: money(day.low), label: 'low' },
        { value: percent(day.daily_range_pct), label: 'daily range' },
        { value: day.is_flagged ? 'Yes' : 'No', label: 'flagged' },
        { value: day.co_flag_count + ' of 8', label: 'stocks flagged' },
      ];
    },
  });
}

/* ---------- selected day ---------- */

function renderSelectedMetrics(day) {
  byId('selectedPrice').textContent = day ? money(day.close) : '—';
  byId('selectedDate').textContent = day ? day.date : 'No day selected';
  byId('rangeMetric').textContent = day ? percent(day.daily_range_pct) : '—';
  byId('coMetric').textContent = day ? day.co_flag_count + ' of 8' : '—';
}

function renderFacts(day) {
  const flagText = day.is_flagged ? 'Flagged day' : 'Not a flagged day';
  byId('selectedFacts').innerHTML = 'Close <b>' + money(day.close) + '</b> &nbsp; High <b>' + money(day.high) +
    '</b> &nbsp; Low <b>' + money(day.low) + '</b> &nbsp; Range <b>' + percent(day.daily_range_pct) +
    '</b><br>' + flagText;
}

function renderComparison(day) {
  byId('compareTitle').textContent = day.co_flag_count + ' of 8 stocks flagged on ' + day.date;
  // Bars share one scale so the eight ranges can be compared directly
  let largest = 0;
  SYMBOLS.forEach(function (symbol) {
    const other = dayLookup[symbol][day.date];
    if (other && other.daily_range_pct > largest) largest = other.daily_range_pct;
  });
  let html = '';
  SYMBOLS.forEach(function (symbol) {
    const other = dayLookup[symbol][day.date];
    const isCurrent = symbol === state.stock ? ' current' : '';
    if (!other) {
      html += '<div class="compare-row' + isCurrent + '"><span class="compare-name">' + symbol + '</span><span class="compare-track"></span><span class="compare-value">' + MISSING + '</span><span class="compare-flag"></span></div>';
      return;
    }
    const width = (other.daily_range_pct / largest) * 100;
    html += '<div class="compare-row' + isCurrent + '"><span class="compare-name">' + symbol + '</span>' +
      '<span class="compare-track"><i class="' + (other.is_flagged ? 'is-flagged' : '') + '" style="width:' + width + '%"></i></span>' +
      '<span class="compare-value">' + percent(other.daily_range_pct) + '</span>' +
      '<span class="compare-flag">' + (other.is_flagged ? 'Flagged' : '') + '</span></div>';
  });
  byId('compareRows').innerHTML = html;
}

function selectedSentences(text, kind) {
  const points = window.summarizeSource(text, kind);
  if (points.length === 0) {
    return '<p class="data-note">No suitable sentence could be selected. Review the full text below.</p>';
  }
  let items = '';
  points.forEach(function (point) {
    items += '<li><strong>' + escapeHtml(point.label) + '</strong><span>' + escapeHtml(point.text) + '</span></li>';
  });
  return '<div class="quick-summary"><span class="summary-label">SELECTED SENTENCES · NOT A SUMMARY</span><ul>' + items + '</ul></div>';
}

function fullText(title, text) {
  return '<details class="filing-section"><summary>' + escapeHtml(title) + '</summary><div class="filing-text">' + escapeHtml(text) + '</div></details>';
}

function renderNews(day) {
  if (day.news_ids.length === 0) {
    byId('newsPanel').innerHTML = '<div class="empty">No news summaries are available for this company in the selected date window.</div>';
    return;
  }
  let html = '<p class="data-note">Selected day and the 7 calendar days before it · ' + day.news_ids.length + ' daily summaries, newest first.</p>';
  day.news_ids.forEach(function (id) {
    const item = newsById[id];
    const isSelectedDay = item.date === day.date;
    let label = item.date + (isSelectedDay ? ' · SELECTED DAY' : '') + ' · AI-generated news summary';
    if (item.highlights_low_info) label += ' · Limited information';
    // Only the selected day starts open, so the list stays easy to scan
    html += '<details class="news-item"' + (isSelectedDay ? ' open' : '') + '><summary class="news-date">' + escapeHtml(label) + '</summary>' +
      selectedSentences(item.highlights, 'news') + fullText('Read full AI summary', item.highlights) + '</details>';
  });
  byId('newsPanel').innerHTML = html;
}

function filingAgeText(day) {
  if (day.filed_same_day) return 'Filed on selected date; publication time unavailable.';
  const unit = day.filing_age_days === 1 ? ' day' : ' days';
  return 'Filed ' + day.filing_age_days + unit + ' before the selected day';
}

function renderFiling(day) {
  if (day.filing_id === null) {
    byId('filingPanel').innerHTML = '<div class="empty">No eligible 10-K or 10-Q filing is available for this company as of the selected date.</div>';
    return;
  }
  const filing = filingById[day.filing_id];
  const riskLabel = filing.risk_refers_to_10k ? 'Risk factors · refers to 10-K' : 'Risk factors';
  let html = '<div class="filing-meta"><span class="filing-type">' + escapeHtml(filing.document_type) + '</span>' +
    '<span class="muted">Filed ' + filing.date + '</span></div>' +
    '<p class="filing-age">' + filingAgeText(day) + '</p>' +
    '<p class="data-note">Latest filing dated on or before the selected day. Filing text is excerpted from the filings, not the complete documents.</p>' +
    '<h3 class="summary-heading">Management discussion (MD&amp;A)</h3>' + selectedSentences(filing.mda_content, 'mda') + fullText('Read full MD&A excerpt', filing.mda_content) +
    '<h3 class="summary-heading">' + riskLabel + '</h3>' + selectedSentences(filing.risk_content, 'risk') + fullText('Read full risk excerpt', filing.risk_content);
  if (day.annual_risk_id !== null) {
    const annual = filingById[day.annual_risk_id];
    html += '<h3 class="summary-heading">Risk factors from the latest 10-K (filed ' + annual.date + ')</h3>' +
      selectedSentences(annual.risk_content, 'risk') + fullText('Read full annual risk excerpt', annual.risk_content);
  }
  byId('filingPanel').innerHTML = html;
}

function updateSaveButton() {
  const key = state.stock + '|' + state.selected;
  const isSaved = shortlist.some(function (item) { return item.key === key; });
  byId('saveBtn').textContent = isSaved ? '★ Shortlisted' : '☆ Shortlist';
  byId('saveBtn').setAttribute('aria-pressed', isSaved);
}

function renderSelection() {
  const day = selectedDay();
  renderSelectedMetrics(day);
  byId('contextPanel').hidden = !day;
  if (day) {
    byId('contextTitle').textContent = DATA.companies[state.stock] + ' (' + state.stock + ') · ' + day.date;
    renderFacts(day);
    renderComparison(day);
    renderNews(day);
    renderFiling(day);
    updateSaveButton();
  }
  drawDetailChart();
  document.querySelectorAll('#eventRows tr[data-date]').forEach(function (row) {
    row.classList.toggle('chosen', row.dataset.date === state.selected);
  });
}

function selectDay(date) {
  state.selected = date;
  renderSelection();
}

function renderStock() {
  byId('stock').value = state.stock;
  byId('chartTitle').textContent = DATA.companies[state.stock] + ' · ' + state.stock;
  const days = daysInPeriod(state.stock);
  byId('stockCoverage').textContent = days[0].date + ' to ' + days[days.length - 1].date + ' · ' + days.length + ' trading days';
  renderCards();
  renderEvents();
  renderSelection();
}

function renderOverview() {
  renderCoverage();
  renderLegend();
  drawRelativeChart();
  renderSummary();
}

function renderAll() {
  byId('period').value = state.period;
  renderOverview();
  renderStock();
}

/* Changing period or stock always selects that view's largest flagged day. */
function changePeriod(period) {
  state.period = period;
  chooseDefaultDay();
  renderAll();
}

function changeStock(symbol) {
  state.stock = symbol;
  chooseDefaultDay();
  renderStock();
  renderSummary();
  drawRelativeChart();
}

/* ---------- shortlist ---------- */

function loadShortlist() {
  // Browser storage can be blocked, so a failure just means an empty list
  try {
    const saved = JSON.parse(localStorage.getItem(SHORTLIST_KEY) || '[]');
    return Array.isArray(saved) ? saved : [];
  } catch (error) {
    return [];
  }
}

function saveShortlist() {
  try {
    localStorage.setItem(SHORTLIST_KEY, JSON.stringify(shortlist));
  } catch (error) {
    showToast('Browser storage unavailable. Export to keep your shortlist.');
  }
  updateSaveButton();
  renderShortlist();
}

/* Saved items that no longer match a record in the data are skipped. */
function validShortlistItems() {
  const items = [];
  shortlist.forEach(function (item) {
    const parts = String(item.key).split('|');
    const lookup = dayLookup[parts[0]];
    const day = lookup ? lookup[parts[1]] : null;
    if (day) items.push({ key: item.key, symbol: parts[0], day: day });
  });
  return items;
}

function renderShortlist() {
  const items = validShortlistItems();
  byId('savedCount').textContent = items.length;
  if (items.length === 0) {
    byId('shortlistItems').innerHTML = '<div class="panel empty">Your shortlist is empty.<br>Open a trading day in the explorer and press ☆ Shortlist to save it here.</div>';
    return;
  }
  let html = '';
  items.forEach(function (item) {
    html += '<article class="saved-card"><div><h3>' + item.symbol + ' <span class="muted">' + item.day.date + '</span></h3>' +
      '<p>Daily range ' + percent(item.day.daily_range_pct) + ' · Close ' + money(item.day.close) + ' · ' + item.day.co_flag_count + ' of 8 stocks flagged · For human follow-up</p></div>' +
      '<button class="outline" data-open="' + item.key + '">Review context ↗</button>' +
      '<button class="outline" data-remove="' + item.key + '" aria-label="Remove ' + item.symbol + ' ' + item.day.date + '">Remove</button></article>';
  });
  byId('shortlistItems').innerHTML = html;
}

function toggleShortlist() {
  const key = state.stock + '|' + state.selected;
  const position = shortlist.findIndex(function (item) { return item.key === key; });
  if (position >= 0) {
    shortlist.splice(position, 1);
    showToast('Removed from shortlist');
  } else {
    shortlist.push({ key: key });
    showToast('Added to review shortlist');
  }
  saveShortlist();
}

function showShortlistView(isShortlist) {
  byId('explorer').hidden = isShortlist;
  byId('filters').hidden = isShortlist;
  byId('shortlistView').hidden = !isShortlist;
  byId('overviewNav').classList.toggle('active', !isShortlist);
  byId('shortlistNav').classList.toggle('active', isShortlist);
  // Charts measure their width, so they must be redrawn once visible again
  if (!isShortlist) {
    drawRelativeChart();
    drawDetailChart();
  }
}

function openShortlistItem(key) {
  const parts = key.split('|');
  state.stock = parts[0];
  state.period = 'full';
  state.selected = parts[1];
  showShortlistView(false);
  renderAll();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function exportShortlist() {
  const items = validShortlistItems();
  if (items.length === 0) {
    showToast('Add a movement to your shortlist first.');
    return;
  }
  const lines = ['symbol,date,close,high,low,daily_range_percent,stocks_flagged_that_day,latest_filing_type,latest_filing_date,review_status'];
  items.forEach(function (item) {
    const filing = item.day.filing_id === null ? null : filingById[item.day.filing_id];
    lines.push([
      item.symbol, item.day.date, item.day.close.toFixed(2), item.day.high.toFixed(2), item.day.low.toFixed(2),
      (item.day.daily_range_pct * 100).toFixed(4), item.day.co_flag_count,
      filing ? filing.document_type : MISSING, filing ? filing.date : MISSING, 'For human follow-up',
    ].join(','));
  });
  const url = URL.createObjectURL(new Blob([lines.join('\r\n')], { type: 'text/csv;charset=utf-8' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'stock-context-shortlist.csv';
  link.click();
  setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  showToast('Shortlist exported');
}

/* ---------- connect the controls ---------- */

function connectControls() {
  let options = '';
  SYMBOLS.forEach(function (symbol) {
    options += '<option value="' + symbol + '">' + escapeHtml(DATA.companies[symbol]) + ' (' + symbol + ')</option>';
  });
  byId('stock').innerHTML = options;

  byId('period').addEventListener('change', function (event) { changePeriod(event.target.value); });
  byId('stock').addEventListener('change', function (event) { changeStock(event.target.value); });

  byId('relativeLegend').addEventListener('click', function (event) {
    const button = event.target.closest('[data-line]');
    if (!button) return;
    const symbol = button.dataset.line;
    if (state.hiddenLines.has(symbol)) state.hiddenLines.delete(symbol);
    else state.hiddenLines.add(symbol);
    renderLegend();
    drawRelativeChart();
  });

  byId('summaryHead').addEventListener('click', function (event) {
    const button = event.target.closest('[data-sort]');
    if (!button) return;
    const column = button.dataset.sort;
    if (state.sortColumn === column) state.sortAscending = !state.sortAscending;
    else {
      state.sortColumn = column;
      state.sortAscending = true;
    }
    renderSummary();
  });

  byId('summaryRows').addEventListener('click', function (event) {
    const row = event.target.closest('[data-stock]');
    if (row) changeStock(row.dataset.stock);
  });

  byId('companyCards').addEventListener('click', function (event) {
    const card = event.target.closest('[data-stock]');
    if (card) changeStock(card.dataset.stock);
  });

  byId('eventRows').addEventListener('click', function (event) {
    const row = event.target.closest('[data-date]');
    if (row) selectDay(row.dataset.date);
  });

  document.querySelectorAll('[data-mode]').forEach(function (button) {
    button.addEventListener('click', function () {
      state.chartMode = button.dataset.mode;
      byId('detailSeriesName').textContent = state.chartMode === 'close' ? 'Close price' : 'Daily range %';
      document.querySelectorAll('[data-mode]').forEach(function (other) {
        other.classList.toggle('selected', other === button);
      });
      drawDetailChart();
    });
  });

  document.querySelectorAll('[data-tab]').forEach(function (button) {
    button.addEventListener('click', function () {
      byId('newsPanel').hidden = button.dataset.tab !== 'news';
      byId('filingPanel').hidden = button.dataset.tab !== 'filing';
      document.querySelectorAll('[data-tab]').forEach(function (other) {
        other.classList.toggle('selected', other === button);
      });
    });
  });

  byId('saveBtn').addEventListener('click', toggleShortlist);
  byId('exportBtn').addEventListener('click', exportShortlist);
  byId('overviewNav').addEventListener('click', function () { showShortlistView(false); });
  byId('shortlistNav').addEventListener('click', function () { showShortlistView(true); });

  byId('shortlistItems').addEventListener('click', function (event) {
    const button = event.target.closest('[data-open],[data-remove]');
    if (!button) return;
    if (button.dataset.open) {
      openShortlistItem(button.dataset.open);
      return;
    }
    shortlist = shortlist.filter(function (item) { return item.key !== button.dataset.remove; });
    saveShortlist();
  });

  ['methodBtn', 'aboutBtn'].forEach(function (id) {
    byId(id).addEventListener('click', function () { byId('methodDialog').showModal(); });
  });
  byId('closeDialog').addEventListener('click', function () { byId('methodDialog').close(); });
  byId('methodDialog').addEventListener('click', function (event) {
    // A click on the dark area outside the box closes it
    if (event.target === byId('methodDialog')) byId('methodDialog').close();
  });

  // Charts are sized in pixels, so redraw them when the window width changes
  let lastWidth = window.innerWidth;
  window.addEventListener('resize', function () {
    if (window.innerWidth === lastWidth) return;
    lastWidth = window.innerWidth;
    if (!byId('explorer').hidden) {
      drawRelativeChart();
      drawDetailChart();
    }
  });
}

function start() {
  connectControls();
  byId('loading').hidden = true;
  byId('explorer').hidden = false;
  chooseDefaultDay();
  renderAll();
  renderShortlist();
}

start();
