# NSW Crime Dashboard

An interactive data dashboard for a community resource centre that visualises NSW Police incident data sourced directly from a published Google Sheets CSV feed.

## Features

### KPI Cards
- **Total Incidents** — sum of all crime reports in the filtered view
- **Most Common Offence** — the offence category with the highest incident count
- **Highest Incident Area** — the NSW Statistical Area with the most incidents
- **Latest Reporting Month** — the most recent month with recorded data

### Visualisations
1. **Crime Incidents Over Time** — monthly line chart showing total incident trends
2. **Incidents by Offence Category** — horizontal bar chart of incident counts per category
3. **Incidents by Geographic Area** — horizontal bar chart of incident counts per statistical area
4. **Top Areas by Incident Count** — ranked horizontal bar chart (top 10 areas)

### Interactive Filters
- **Year** — narrow data to a specific calendar year
- **Month** — narrow data to a specific month (e.g. January across all years)
- **NSW Statistical Area** — filter by geographic statistical area
- **Offence Category** — filter by primary offence classification
- **Offence Subcategory** — cascading filter that updates based on the selected category

When any filter changes, all KPI cards, charts, and rankings update instantly. Active filters appear as removable chips.

## Technical Details

### Architecture
- **HTML** — semantic dashboard structure (`index.html`)
- **CSS** — modern, responsive styling with CSS variables, grid, and flexbox (`style.css`)
- **JavaScript** — data fetching, parsing, filtering, and Chart.js rendering (`script.js`)
- No build step — open `index.html` directly in any modern browser

### Data Source
The dashboard loads data dynamically from:
```
https://docs.google.com/spreadsheets/d/e/2PACX-1vRZsJ4mONV7eOlJyAYTmisfZinYm1NbTqG_1aVBqBgGuT8Mo90WeqYT18hq38def1enoA3E3vvmE-cv/pub?output=csv
```

The CSV uses a **wide format**: each row represents one (Statistical Area, Offence Category, Subcategory) combination, with one column per month from January 1995 to March 2026. The script unpivots this into a long-format data model for aggregation.

### Dependencies (CDN)
- **Chart.js 4.4** — charting library loaded from `cdn.jsdelivr.net`
- **Google Fonts** — Inter (UI) and Archivo (display headings)

### Error Handling
- Network failures and HTTP errors are caught and displayed in a user-friendly error banner
- Empty or malformed CSV responses are detected and reported
- Each chart shows a "No data" message when filters produce an empty result set

## Known Issue Fixed: "Maximum call stack size exceeded"

A previous version of this dashboard caused a `RangeError: Maximum call stack size exceeded` when loading. The root cause and the fix are documented below.

### Root Cause
The error was triggered by one or more of the following anti-patterns:

1. **Recursive CSV parsing** — a naive parser that called itself per field/row exhausted the JavaScript call stack on the large dataset (~1.7 MB, ~375 month columns).
2. **Recursive data unpivoting** — transforming wide-format CSV rows into long-format data points using `.map()` inside `.map()` or a recursive flatten created deep call stacks.
3. **Circular re-render loop** — updating select elements programmatically triggered `change` events, which fired the render cycle again, leading to unbounded recursion before a guard flag was in place.
4. **`JSON.stringify` on the full dataset** — serialising the entire parsed dataset for debugging purposes caused the engine to recurse over a very large object graph.

### Fix
This implementation addresses all four root causes:

1. **Iterative CSV parser** — `parseCSV()` uses a character-level state machine with a `for` loop. No recursive function calls. It correctly handles quoted fields containing commas (e.g. `"Dealing, trafficking in cocaine"`).

2. **Iterative data processing** — all aggregation functions (`aggregateByMonth`, `aggregateByCategory`, `aggregateByArea`, `computeKPIs`) use plain `for` loops. No nested `.map()` or `.reduce()` chains that could deepen the call stack.

3. **Re-entrancy guard** — `renderAll()` uses an `isRendering` flag to short-circuit any re-entrant calls before they accumulate. The `isPopulating` flag prevents cascading filter updates from triggering recursive renders.

4. **No full-dataset serialisation** — the code never calls `JSON.stringify` on the raw or transformed data.

Additionally, every `Chart` instance is explicitly `destroy()`ed before a new one is created (`destroyChart()`), preventing memory leaks and Chart.js internal state issues that can degrade performance on repeated filter changes.

## How to Run

1. **Download/clone** this repository.
2. Open `index.html` in a modern browser (Chrome, Edge, Firefox, or Safari).

No server or build step is required — the dashboard loads the CSV directly from Google Sheets via `fetch()`.

If your browser blocks the request due to CORS or mixed-content policies, serve the files via a local static server:
```bash
# Python
python -m http-server

# Node.js
npx serve .
```

## File Structure
```
NSW Crime Dashboard/
  index.html      — dashboard markup, Chart.js & font CDN includes
  style.css       — responsive, modern CSS with CSS variables
  script.js       — data loading, parsing, filtering, chart rendering
  README.md       — this file
```

## Design Notes

- The dashboard is **responsive**: KPI cards use a 4-column grid on desktop, 2-column on tablet, and 1-column on mobile.
- Charts use a **professional colour palette**: dark blue (`#0c2443`) for text, royal blue (`#2563eb`) for chart elements, with a subtle gradient accent on KPI cards.
- **Tooltips** are styled with a dark background and clear typography.
- **Reduced motion** is respected via `prefers-reduced-motion`.
- **Animations** use `requestAnimationFrame` for KPI value count-up, with a fallback to instant display when motion is reduced.
