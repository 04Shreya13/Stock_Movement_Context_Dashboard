/* Draws the two SVG charts. It only draws what it is given: it knows nothing
   about the page, and it does no analysis. app.js calls the two functions at
   the bottom of this file. */
(function () {
  const HEIGHT = 300;
  const PAD = { left: 52, right: 20, top: 16, bottom: 30 };

  /* Pick round numbers for the y-axis, for example 80, 100, 120. */
  function niceTicks(min, max) {
    const rough = (max - min) / 5 || 1;
    const power = Math.pow(10, Math.floor(Math.log10(rough)));
    const scaled = rough / power;
    let step = 10 * power;
    if (scaled <= 1) step = power;
    else if (scaled <= 2) step = 2 * power;
    else if (scaled <= 2.5) step = 2.5 * power;
    else if (scaled <= 5) step = 5 * power;
    const ticks = [];
    for (let value = Math.ceil(min / step) * step; value <= max + step / 1000; value += step) {
      ticks.push(value);
    }
    return ticks;
  }

  /* Axis labels: month and year for long spans, month and day for short ones. */
  function axisLabel(dateText, isShortSpan) {
    const date = new Date(dateText + 'T12:00:00Z');
    const options = isShortSpan
      ? { month: 'short', day: 'numeric', timeZone: 'UTC' }
      : { month: 'short', year: 'numeric', timeZone: 'UTC' };
    return date.toLocaleDateString('en-US', options);
  }

  /* The usable width inside the chart box, leaving out its side padding. */
  function innerWidth(container) {
    const style = window.getComputedStyle(container);
    const padding = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
    return Math.max(260, container.clientWidth - padding);
  }

  /* Shared layout: converts data values to pixel positions. */
  function makeScales(width, pointCount, min, max) {
    const plotWidth = width - PAD.left - PAD.right;
    const plotHeight = HEIGHT - PAD.top - PAD.bottom;
    return {
      x: function (index) { return PAD.left + (index / Math.max(1, pointCount - 1)) * plotWidth; },
      y: function (value) { return HEIGHT - PAD.bottom - ((value - min) / (max - min)) * plotHeight; },
    };
  }

  function linePath(values, scales) {
    const parts = [];
    values.forEach(function (value, index) {
      parts.push((index === 0 ? 'M' : 'L') + scales.x(index).toFixed(1) + ',' + scales.y(value).toFixed(1));
    });
    return parts.join(' ');
  }

  function gridAndAxes(width, ticks, scales, dates, formatTick) {
    let svg = '';
    ticks.forEach(function (tick) {
      const y = scales.y(tick);
      svg += '<line class="grid" x1="' + PAD.left + '" x2="' + (width - PAD.right) + '" y1="' + y + '" y2="' + y + '"/>';
      svg += '<text x="' + (PAD.left - 9) + '" y="' + (y + 3) + '" text-anchor="end">' + formatTick(tick) + '</text>';
    });
    // Fewer date labels on narrow screens so they never collide
    const labelCount = width < 560 ? 3 : 6;
    const isShortSpan = dates.length <= 31;
    for (let i = 0; i < labelCount; i++) {
      const index = Math.round((i / (labelCount - 1)) * (dates.length - 1));
      let anchor = 'middle';
      if (i === 0) anchor = 'start';
      if (i === labelCount - 1) anchor = 'end';
      svg += '<text x="' + scales.x(index) + '" y="' + (HEIGHT - 8) + '" text-anchor="' + anchor + '">' + axisLabel(dates[index], isShortSpan) + '</text>';
    }
    return svg;
  }

  /* Tooltip rows are built with textContent, so data text can never become HTML. */
  function showTooltip(event, title, rows) {
    const tooltip = document.getElementById('chartTooltip');
    tooltip.textContent = '';
    const heading = document.createElement('div');
    heading.className = 'tip-title';
    heading.textContent = title;
    tooltip.appendChild(heading);
    rows.forEach(function (row) {
      const line = document.createElement('div');
      line.className = 'tip-row';
      if (row.color) {
        const key = document.createElement('i');
        key.style.background = row.color;
        line.appendChild(key);
      }
      const value = document.createElement('b');
      value.textContent = row.value;
      line.appendChild(value);
      const label = document.createElement('span');
      label.textContent = row.label;
      line.appendChild(label);
      tooltip.appendChild(line);
    });
    tooltip.hidden = false;
    // Keep the tooltip on screen, flipping it to the left near the right edge
    const box = tooltip.getBoundingClientRect();
    let left = event.clientX + 14;
    if (left + box.width > window.innerWidth - 8) left = event.clientX - box.width - 14;
    let top = event.clientY + 14;
    if (top + box.height > window.innerHeight - 8) top = window.innerHeight - box.height - 8;
    tooltip.style.left = Math.max(8, left) + 'px';
    tooltip.style.top = Math.max(8, top) + 'px';
  }

  function hideTooltip() {
    document.getElementById('chartTooltip').hidden = true;
  }

  /* Find the data point nearest the pointer, and move the crosshair to it. */
  function nearestIndex(event, container, scales, pointCount) {
    const box = container.querySelector('svg').getBoundingClientRect();
    const pointerX = event.clientX - box.left;
    let best = 0;
    for (let i = 1; i < pointCount; i++) {
      if (Math.abs(scales.x(i) - pointerX) < Math.abs(scales.x(best) - pointerX)) best = i;
    }
    const crosshair = container.querySelector('.crosshair');
    crosshair.setAttribute('x1', scales.x(best));
    crosshair.setAttribute('x2', scales.x(best));
    crosshair.style.display = 'block';
    return best;
  }

  function hideCrosshair(container) {
    container.querySelector('.crosshair').style.display = 'none';
  }

  /* Eight lines rebased to 100. "selected" is drawn last, so it sits on top. */
  function drawRelative(container, options) {
    const dates = options.dates;
    const shown = options.symbols.filter(function (symbol) { return !options.hidden.has(symbol); });
    if (shown.length === 0) {
      container.innerHTML = '<div class="empty">All stocks are hidden. Click a name above to show its line.</div>';
      return;
    }
    let min = Infinity;
    let max = -Infinity;
    shown.forEach(function (symbol) {
      options.series[symbol].indexed.forEach(function (value) {
        if (value < min) min = value;
        if (value > max) max = value;
      });
    });
    const gap = (max - min) * 0.08 || 1;
    min -= gap;
    max += gap;

    const width = innerWidth(container);
    const scales = makeScales(width, dates.length, min, max);
    let svg = '<svg width="' + width + '" height="' + HEIGHT + '" role="img" aria-label="Relative price of the eight stocks; the same values are in the table below">';
    svg += gridAndAxes(width, niceTicks(min, max), scales, dates, function (tick) { return tick.toFixed(0); });
    if (min < 100 && max > 100) {
      svg += '<line class="base-line" x1="' + PAD.left + '" x2="' + (width - PAD.right) + '" y1="' + scales.y(100) + '" y2="' + scales.y(100) + '"/>';
    }
    const drawOrder = shown.filter(function (symbol) { return symbol !== options.selected; });
    if (shown.indexOf(options.selected) >= 0) drawOrder.push(options.selected);
    drawOrder.forEach(function (symbol) {
      const style = options.styles[symbol];
      const dash = style.dash ? ' stroke-dasharray="' + style.dash + '"' : '';
      const faded = symbol === options.selected ? '' : ' class="faded"';
      svg += '<path' + faded + ' d="' + linePath(options.series[symbol].indexed, scales) + '" stroke="' + style.color + '"' + dash + ' fill="none" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>';
    });
    svg += '<line class="crosshair" y1="' + PAD.top + '" y2="' + (HEIGHT - PAD.bottom) + '" style="display:none"/>';
    svg += '</svg>';
    container.innerHTML = svg;

    const plot = container.querySelector('svg');
    plot.addEventListener('pointermove', function (event) {
      const index = nearestIndex(event, container, scales, dates.length);
      const rows = shown.map(function (symbol) {
        return {
          sortValue: options.series[symbol].indexed[index],
          value: options.series[symbol].indexed[index].toFixed(2),
          label: symbol + ' · ' + options.formatChange(options.series[symbol].change[index]),
          color: options.styles[symbol].color,
        };
      });
      rows.sort(function (a, b) { return b.sortValue - a.sortValue; });
      showTooltip(event, dates[index], rows);
    });
    plot.addEventListener('pointerleave', function () {
      hideCrosshair(container);
      hideTooltip();
    });
  }

  /* One stock over time, with flagged days marked. */
  function drawDetail(container, options) {
    const rows = options.rows;
    if (rows.length === 0) {
      container.innerHTML = '<div class="empty">No price records in this period.</div>';
      return;
    }
    const isClose = options.mode === 'close';
    const valueOf = function (row) { return isClose ? row.close : row.daily_range_pct * 100; };
    const values = rows.map(valueOf);
    let min = Math.min.apply(null, values);
    let max = Math.max.apply(null, values);
    const gap = (max - min) * 0.12 || 1;
    min = Math.max(0, min - gap);
    max += gap;

    const width = innerWidth(container);
    const dates = rows.map(function (row) { return row.date; });
    const scales = makeScales(width, rows.length, min, max);
    const line = linePath(values, scales);
    const baseline = HEIGHT - PAD.bottom;
    const formatTick = function (tick) { return isClose ? '$' + tick.toFixed(0) : tick.toFixed(1) + '%'; };

    let svg = '<svg width="' + width + '" height="' + HEIGHT + '" role="img" aria-label="' + options.symbol + (isClose ? ' closing price' : ' daily range') + ' in the selected period">';
    svg += '<defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#16816f" stop-opacity=".14"/><stop offset="1" stop-color="#16816f" stop-opacity="0"/></linearGradient></defs>';
    svg += gridAndAxes(width, niceTicks(min, max), scales, dates, formatTick);
    svg += '<path d="' + line + ' L' + scales.x(rows.length - 1) + ',' + baseline + ' L' + scales.x(0) + ',' + baseline + ' Z" fill="url(#area)"/>';
    svg += '<path d="' + line + '" stroke="#16816f" fill="none" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>';

    const selectedIndex = dates.indexOf(options.selected);
    if (selectedIndex >= 0) {
      svg += '<line class="selected-line" x1="' + scales.x(selectedIndex) + '" x2="' + scales.x(selectedIndex) + '" y1="' + PAD.top + '" y2="' + baseline + '"/>';
    }
    rows.forEach(function (row, index) {
      if (row.is_flagged && index !== selectedIndex) {
        svg += '<circle class="flag-dot" data-day="' + row.date + '" cx="' + scales.x(index) + '" cy="' + scales.y(values[index]) + '" r="4" tabindex="0" role="button" aria-label="Flagged day ' + row.date + '"/>';
      }
    });
    if (selectedIndex >= 0) {
      svg += '<circle class="selected-dot" cx="' + scales.x(selectedIndex) + '" cy="' + scales.y(values[selectedIndex]) + '" r="6"/>';
    }
    svg += '<line class="crosshair" y1="' + PAD.top + '" y2="' + baseline + '" style="display:none"/>';
    svg += '</svg>';
    container.innerHTML = svg;

    const plot = container.querySelector('svg');
    plot.addEventListener('pointermove', function (event) {
      const row = rows[nearestIndex(event, container, scales, rows.length)];
      showTooltip(event, options.symbol + ' · ' + row.date, options.tooltipRows(row));
    });
    plot.addEventListener('pointerleave', function () {
      hideCrosshair(container);
      hideTooltip();
    });
    plot.addEventListener('click', function (event) {
      options.onSelect(rows[nearestIndex(event, container, scales, rows.length)].date);
    });
    plot.addEventListener('keydown', function (event) {
      const day = event.target.getAttribute('data-day');
      if (day && (event.key === 'Enter' || event.key === ' ')) {
        event.preventDefault();
        options.onSelect(day);
      }
    });
  }

  window.Charts = { drawRelative: drawRelative, drawDetail: drawDetail, hideTooltip: hideTooltip };
})();
