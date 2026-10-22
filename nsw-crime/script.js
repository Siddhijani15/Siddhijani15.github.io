/*
 * NSW Crime Dashboard — script.js
 *
 * Key design decisions to prevent "Maximum call stack size exceeded":
 *   - CSV parsing uses an iterative state machine (no recursion).
 *   - All data processing uses plain for-loops (no recursive map/reduce chains).
 *   - A guard flag (isRendering) prevents re-entrant render cycles.
 *   - Chart.js instances are destroyed before re-creation.
 *   - No JSON.stringify on the full dataset.
 */

'use strict';

// ===== Configuration =====
const CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRZsJ4mONV7eOlJyAYTmisfZinYm1NbTqG_1aVBqBgGuT8Mo90WeqYT18hq38def1enoA3E3vvmE-cv/pub?output=csv';
const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const MAX_BARS = 25;

// ===== Global State =====
let monthColumns = [];        // [{ csvIndex, key, year, monthName, monthIndex, sortKey }]
let dataRows = [];            // [{ area, category, subcategory, values: [int, ...] }]
let cachedTotalRecord = 0;    // grand total across all data (computed once)
let allYears = [];
let allAreas = [];
let allCategories = [];
let allSubcategories = [];
let charts = {};
let filters = { year: 'all', month: 'all', area: 'all', category: 'all', subcategory: 'all' };
let isRendering = false;

// ===== DOM references =====
const els = {};

// ===== Utility =====
function fmt(n) {
  return Number(n).toLocaleString('en-AU');
}

function qs(selector) {
  return document.querySelector(selector);
}

// ===== Initialization =====
document.addEventListener('DOMContentLoaded', function () {
  els.loadingOverlay = document.getElementById('loadingOverlay');
  els.errorBanner = document.getElementById('errorBanner');
  els.errorMessage = document.getElementById('errorMessage');
  els.errorHint = document.getElementById('errorHint');
  els.dashboard = document.getElementById('dashboard');
  els.recordRange = document.getElementById('recordRange');
  els.chipsRow = document.getElementById('chipsRow');
  els.fYear = document.getElementById('fYear');
  els.fMonth = document.getElementById('fMonth');
  els.fArea = document.getElementById('fArea');
  els.fCategory = document.getElementById('fCategory');
  els.fSubcategory = document.getElementById('fSubcategory');
  els.resetBtn = document.getElementById('resetBtn');

  init();
});

async function init() {
  showLoading(true);
  hideError();
  try {
    const csvText = await loadData();
    processData(csvText);
    populateFilterDropdowns();
    bindEvents();
    showLoading(false);
    showDashboard(true);
    renderAll();
  } catch (err) {
    showLoading(false);
    showError(err.message, 'Please check your internet connection and try refreshing the page.');
  }
}

// ===== Data Loading =====
async function loadData() {
  const response = await fetch(CSV_URL, { mode: 'cors' });
  if (!response.ok) {
    throw new Error('Failed to load data: HTTP ' + response.status);
  }
  return await response.text();
}

// ===== CSV Parsing (iterative state machine — no recursion) =====
function parseCSV(text) {
  const rows = [];
  let row = [];
  let field = '';
  let inQuotes = false;

  for (let i = 0; i < text.length; i++) {
    const ch = text[i];

    if (inQuotes) {
      if (ch === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        field += ch;
      }
    } else {
      if (ch === '"') {
        inQuotes = true;
      } else if (ch === ',') {
        row.push(field);
        field = '';
      } else if (ch === '\n') {
        row.push(field);
        rows.push(row);
        row = [];
        field = '';
      } else if (ch !== '\r') {
        field += ch;
      }
    }
  }

  // Flush the last field/row if there's no trailing newline
  if (field.length > 0 || row.length > 0) {
    row.push(field);
    rows.push(row);
  }

  return rows;
}

// ===== Data Processing =====
function processData(csvText) {
  const rows = parseCSV(csvText);
  if (rows.length < 2) {
    throw new Error('No data found in the CSV response. The sheet may be empty.');
  }

  const header = rows[0];

  // ---- Build month column descriptors (columns from index 3 onward) ----
  monthColumns = [];
  const seenSortKeys = new Set();

  for (let c = 3; c < header.length; c++) {
    const colName = header[c];
    if (!colName || !colName.trim()) continue;

    const parts = colName.trim().split(' ');
    if (parts.length < 2) continue;

    const monthName = parts[0];
    const yearStr = parts[parts.length - 1];
    const year = parseInt(yearStr, 10);
    const monthIndex = MONTH_NAMES.indexOf(monthName);

    if (isNaN(year) || monthIndex === -1) continue;

    const sortKey = year * 12 + monthIndex;
    if (seenSortKeys.has(sortKey)) continue;
    seenSortKeys.add(sortKey);

    monthColumns.push({
      csvIndex: c,
      key: monthName + ' ' + year,
      year: year,
      monthName: monthName,
      monthIndex: monthIndex,
      sortKey: sortKey
    });
  }

  if (monthColumns.length === 0) {
    throw new Error('Could not parse month columns from the CSV header.');
  }

  // Sort chronologically
  monthColumns.sort(function (a, b) { return a.sortKey - b.sortKey; });

  // ---- Build data rows ----
  dataRows = [];
  for (let r = 1; r < rows.length; r++) {
    const row = rows[r];
    if (!row || row.length === 0) continue;

    let hasData = false;
    for (let i = 0; i < row.length; i++) {
      if (row[i] && row[i].trim().length > 0) { hasData = true; break; }
    }
    if (!hasData) continue;

    const area = row[0] || '';
    const category = row[1] || '';
    const subcategory = row[2] || '';

    const values = new Array(monthColumns.length);
    for (let i = 0; i < monthColumns.length; i++) {
      const rawVal = row[monthColumns[i].csvIndex];
      values[i] = rawVal ? parseInt(rawVal, 10) || 0 : 0;
    }

    dataRows.push({ area: area, category: category, subcategory: subcategory, values: values });
  }

  if (dataRows.length === 0) {
    throw new Error('No valid data rows found after the header.');
  }

  // Cache the grand total for KPI context (computed once, not on every render)
  cachedTotalRecord = 0;
  for (let r = 0; r < dataRows.length; r++) {
    const vals = dataRows[r].values;
    for (let i = 0; i < vals.length; i++) {
      cachedTotalRecord += vals[i];
    }
  }

  extractUniqueValues();
}

function extractUniqueValues() {
  const yearSet = new Set();
  const areaSet = new Set();
  const categorySet = new Set();
  const subcategorySet = new Set();

  for (let i = 0; i < monthColumns.length; i++) {
    yearSet.add(monthColumns[i].year);
  }

  for (let r = 0; r < dataRows.length; r++) {
    const row = dataRows[r];
    if (row.area) areaSet.add(row.area);
    if (row.category) categorySet.add(row.category);
    if (row.subcategory && row.subcategory.trim()) subcategorySet.add(row.subcategory);
  }

  allYears = Array.from(yearSet).sort(function (a, b) { return a - b; });
  allAreas = Array.from(areaSet).sort();
  allCategories = Array.from(categorySet).sort();
  allSubcategories = Array.from(subcategorySet).sort();
}

// ===== Filter dropdown population =====
function populateFilterDropdowns() {
  populateSelect(els.fYear, allYears, 'All Years', function (v) { return String(v); });

  els.fMonth.innerHTML = '<option value="all">All Months</option>';
  for (let i = 0; i < MONTH_NAMES.length; i++) {
    const opt = document.createElement('option');
    opt.value = i;
    opt.textContent = MONTH_NAMES[i];
    els.fMonth.appendChild(opt);
  }

  populateSelect(els.fArea, allAreas, 'All Areas');
  populateSelect(els.fCategory, allCategories, 'All Categories');
  populateSelect(els.fSubcategory, allSubcategories, 'All Subcategories');
}

function populateSelect(selectEl, values, allLabel, valueMapper) {
  selectEl.innerHTML = '<option value="all">' + allLabel + '</option>';
  for (let i = 0; i < values.length; i++) {
    const opt = document.createElement('option');
    opt.value = valueMapper ? valueMapper(values[i]) : values[i];
    opt.textContent = values[i];
    selectEl.appendChild(opt);
  }
}

// Cascade: update subcategory dropdown based on selected category
function updateSubcategoryOptions() {
  const category = filters.category;
  const subSet = new Set();

  if (category === 'all') {
    for (let i = 0; i < allSubcategories.length; i++) {
      subSet.add(allSubcategories[i]);
    }
  } else {
    for (let r = 0; r < dataRows.length; r++) {
      if (dataRows[r].category === category) {
        const sub = dataRows[r].subcategory;
        if (sub && sub.trim()) subSet.add(sub);
      }
    }
  }

  const subs = Array.from(subSet).sort();
  els.fSubcategory.innerHTML = '<option value="all">All Subcategories</option>';
  for (let i = 0; i < subs.length; i++) {
    const opt = document.createElement('option');
    opt.value = subs[i];
    opt.textContent = subs[i];
    els.fSubcategory.appendChild(opt);
  }
  filters.subcategory = 'all';
}

// ===== Event Binding =====
function bindEvents() {
  els.fYear.addEventListener('change', function () {
    const v = this.value;
    setFilter('year', v === 'all' ? 'all' : Number(v));
  });
  els.fMonth.addEventListener('change', function () {
    const v = this.value;
    setFilter('month', v === 'all' ? 'all' : Number(v));
  });
  els.fArea.addEventListener('change', function () { setFilter('area', this.value); });
  els.fCategory.addEventListener('change', function () {
    // Update category first, then cascade subcategory dropdown, then render.
    // Order matters: rendering with a stale subcategory (from a different category)
    // would produce empty results.
    filters.category = this.value;
    updateSubcategoryOptions();
    syncSelects();
    renderAll();
  });
  els.fSubcategory.addEventListener('change', function () { setFilter('subcategory', this.value); });
  els.resetBtn.addEventListener('click', function () {
    filters = { year: 'all', month: 'all', area: 'all', category: 'all', subcategory: 'all' };
    updateSubcategoryOptions();
    syncSelects();
    renderAll();
  });
}

function setFilter(key, value) {
  filters[key] = value;
  syncSelects();
  renderAll();
}

function syncSelects() {
  els.fYear.value = filters.year === 'all' ? 'all' : String(filters.year);
  els.fMonth.value = filters.month === 'all' ? 'all' : filters.month;
  els.fArea.value = filters.area;
  els.fCategory.value = filters.category;
  els.fSubcategory.value = filters.subcategory;
}

// ===== Data Filtering =====
function getFilteredDataset() {
  // Determine active month indices based on year/month filters
  const activeMonthIndices = [];
  for (let i = 0; i < monthColumns.length; i++) {
    const mc = monthColumns[i];
    if (filters.year !== 'all' && mc.year !== filters.year) continue;
    if (filters.month !== 'all' && mc.monthIndex !== filters.month) continue;
    activeMonthIndices.push(i);
  }

  // Determine active rows based on area/category/subcategory filters
  const activeRows = [];
  for (let r = 0; r < dataRows.length; r++) {
    const row = dataRows[r];
    if (filters.area !== 'all' && row.area !== filters.area) continue;
    if (filters.category !== 'all' && row.category !== filters.category) continue;
    if (filters.subcategory !== 'all' && row.subcategory !== filters.subcategory) continue;
    activeRows.push(row);
  }

  return { activeMonthIndices: activeMonthIndices, activeRows: activeRows };
}

// ===== Aggregations (all iterative — no recursion) =====

function aggregateByMonth(activeMonthIndices, activeRows) {
  const accum = {};
  const monthMeta = {};

  for (let r = 0; r < activeRows.length; r++) {
    const row = activeRows[r];
    const values = row.values;
    for (let m = 0; m < activeMonthIndices.length; m++) {
      const mi = activeMonthIndices[m];
      const count = values[mi];
      if (count > 0) {
        const mc = monthColumns[mi];
        const sk = mc.sortKey;
        accum[sk] = (accum[sk] || 0) + count;
        if (!monthMeta[sk]) monthMeta[sk] = mc;
      }
    }
  }

  const sortedKeys = Object.keys(accum).map(Number).sort(function (a, b) { return a - b; });
  const labels = [];
  const values = [];
  for (let i = 0; i < sortedKeys.length; i++) {
    labels.push(monthMeta[sortedKeys[i]].key);
    values.push(accum[sortedKeys[i]]);
  }
  return { labels: labels, values: values };
}

function aggregateByCategory(activeMonthIndices, activeRows) {
  const accum = {};

  for (let r = 0; r < activeRows.length; r++) {
    const row = activeRows[r];
    const cat = row.category;
    if (!cat) continue;
    const values = row.values;
    let rowTotal = 0;
    for (let m = 0; m < activeMonthIndices.length; m++) {
      rowTotal += values[activeMonthIndices[m]];
    }
    accum[cat] = (accum[cat] || 0) + rowTotal;
  }

  const entries = [];
  for (const cat in accum) {
    entries.push({ label: cat, value: accum[cat] });
  }
  entries.sort(function (a, b) { return b.value - a.value; });

  const labels = [];
  const values = [];
  for (let i = 0; i < entries.length; i++) {
    labels.push(entries[i].label);
    values.push(entries[i].value);
  }
  const total = entries.reduce(function (s, e) { return s + e.value; }, 0);
  return { labels: labels, values: values, total: total };
}

function aggregateByArea(activeMonthIndices, activeRows) {
  const accum = {};

  for (let r = 0; r < activeRows.length; r++) {
    const row = activeRows[r];
    const area = row.area;
    if (!area) continue;
    const values = row.values;
    let rowTotal = 0;
    for (let m = 0; m < activeMonthIndices.length; m++) {
      rowTotal += values[activeMonthIndices[m]];
    }
    accum[area] = (accum[area] || 0) + rowTotal;
  }

  const entries = [];
  for (const area in accum) {
    entries.push({ label: area, value: accum[area] });
  }
  entries.sort(function (a, b) { return b.value - a.value; });

  const labels = [];
  const values = [];
  for (let i = 0; i < entries.length; i++) {
    labels.push(entries[i].label);
    values.push(entries[i].value);
  }
  return { labels: labels, values: values };
}

function computeKPIs(activeMonthIndices, activeRows) {
  let total = 0;
  const categoryTotals = {};
  const areaTotals = {};
  let latestSortKey = -1;
  let latestMonthKey = '';

  for (let r = 0; r < activeRows.length; r++) {
    const row = activeRows[r];
    const values = row.values;
    for (let m = 0; m < activeMonthIndices.length; m++) {
      const mi = activeMonthIndices[m];
      const count = values[mi];
      if (count > 0) {
        total += count;
        const mc = monthColumns[mi];
        if (row.category) {
          categoryTotals[row.category] = (categoryTotals[row.category] || 0) + count;
        }
        if (row.area) {
          areaTotals[row.area] = (areaTotals[row.area] || 0) + count;
        }
        if (mc.sortKey > latestSortKey) {
          latestSortKey = mc.sortKey;
          latestMonthKey = mc.key;
        }
      }
    }
  }

  // Most common category
  let topCat = '—', topCatCount = 0;
  for (const cat in categoryTotals) {
    if (categoryTotals[cat] > topCatCount) {
      topCatCount = categoryTotals[cat];
      topCat = cat;
    }
  }

  // Highest area
  let topArea = '—', topAreaCount = 0;
  for (const area in areaTotals) {
    if (areaTotals[area] > topAreaCount) {
      topAreaCount = areaTotals[area];
      topArea = area;
    }
  }

  return {
    total: total,
    topCategory: topCat,
    topCategoryCount: topCatCount,
    topArea: topArea,
    topAreaCount: topAreaCount,
    latestMonth: latestMonthKey || '—'
  };
}

// ===== KPI Rendering =====
function animateValue(el, to, duration) {
  const from = parseFloat(el.dataset.raw || '0');
  el.dataset.raw = to;

  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    el.textContent = fmt(to);
    return;
  }

  const start = performance.now();

  function step(now) {
    const elapsed = now - start;
    const progress = Math.min(1, elapsed / duration);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = from + (to - from) * eased;
    el.innerHTML = fmt(Math.round(current));
    if (progress < 1) {
      requestAnimationFrame(step);
    }
  }
  requestAnimationFrame(step);
}

function renderKPIs(kpis) {
  const totalEl = qs('#kpi-total .value');
  totalEl.dataset.raw = '0';
  animateValue(totalEl, kpis.total, 600);
  qs('#kpi-total-ctx').textContent = 'of ' + fmt(cachedTotalRecord) + ' recorded incidents';

  qs('#kpi-category-value').textContent = kpis.topCategory;
  qs('#kpi-category-ctx').textContent = kpis.topCategoryCount > 0
    ? fmt(kpis.topCategoryCount) + ' incidents'
    : 'No data for current filters';

  qs('#kpi-area-value').textContent = kpis.topArea;
  qs('#kpi-area-ctx').textContent = kpis.topAreaCount > 0
    ? fmt(kpis.topAreaCount) + ' incidents'
    : 'No data for current filters';

  qs('#kpi-month-value').textContent = kpis.latestMonth;
  qs('#kpi-month-ctx').textContent = (filters.year !== 'all' || filters.month !== 'all')
    ? 'within filtered range'
    : 'most recent month with data';
}

// ===== Chart Configuration =====
const CHART_COLORS = {
  primary: '#2563eb',
  primaryHover: '#1d4ed8',
  secondary: '#94a3b8'
};

const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
Chart.defaults.font.size = 11.5;
Chart.defaults.color = '#52606d';
Chart.defaults.plugins.tooltip.backgroundColor = '#0c2443';
Chart.defaults.plugins.tooltip.padding = 10;
Chart.defaults.plugins.tooltip.titleFont = { family: "'Archivo', sans-serif", weight: '700', size: 12 };
Chart.defaults.plugins.tooltip.bodyFont = { family: "'Inter', sans-serif", size: 12 };
Chart.defaults.plugins.tooltip.cornerRadius = 6;
Chart.defaults.plugins.tooltip.displayColors = false;
Chart.defaults.plugins.tooltip.callbacks = {
  label: function (context) {
    return fmt(context.raw || 0) + ' incidents';
  }
};

// ===== Chart Lifecycle =====
function destroyChart(name) {
  if (charts[name]) {
    charts[name].destroy();
    charts[name] = null;
  }
}

function showNoDataOverlay(canvas, message) {
  const container = canvas.parentElement; // .chart-container
  // Remove existing overlay
  const existing = container.querySelector('.no-data-overlay');
  if (existing) existing.remove();

  const overlay = document.createElement('div');
  overlay.className = 'no-data-overlay';
  overlay.textContent = message;
  container.appendChild(overlay);
}

function hideNoDataOverlay(canvas) {
  const container = canvas.parentElement;
  const existing = container.querySelector('.no-data-overlay');
  if (existing) existing.remove();
}

// ===== Chart Rendering =====

function renderTimeChart(agg) {
  const canvas = document.getElementById('timeChart');
  destroyChart('timeChart');
  hideNoDataOverlay(canvas);

  if (agg.labels.length === 0) {
    showNoDataOverlay(canvas, 'No incidents match the current filters.');
    return;
  }

  const ctx2d = canvas.getContext('2d');
  const gradient = ctx2d.createLinearGradient(0, 0, 0, 240);
  gradient.addColorStop(0, 'rgba(37, 99, 235, 0.25)');
  gradient.addColorStop(1, 'rgba(37, 99, 235, 0.02)');

  charts.timeChart = new Chart(canvas, {
    type: 'line',
    data: {
      labels: agg.labels,
      datasets: [{
        data: agg.values,
        borderColor: CHART_COLORS.primary,
        backgroundColor: gradient,
        fill: true,
        tension: 0.3,
        pointRadius: agg.labels.length > 40 ? 0 : 2.5,
        pointBackgroundColor: CHART_COLORS.primary,
        pointHoverRadius: 5,
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: REDUCED_MOTION ? 0 : 500 },
      interaction: { mode: 'nearest', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          title: function (ctx) { return ctx[0].label; }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          border: { display: false },
          ticks: {
            maxTicksLimit: 10,
            font: { size: 10.5 }
          }
        },
        y: {
          grid: { color: '#e2e8f0' },
          border: { display: false },
          ticks: { precision: 0 },
          beginAtZero: true
        }
      }
    }
  });
}

function renderBarChart(canvasId, chartName, agg, options) {
  const canvas = document.getElementById(canvasId);
  destroyChart(chartName);
  hideNoDataOverlay(canvas);

  if (agg.labels.length === 0) {
    showNoDataOverlay(canvas, 'No data for the selected filters.');
    return;
  }

  const displayCount = Math.min(agg.labels.length, options.maxBars || MAX_BARS);
  const labels = agg.labels.slice(0, displayCount);
  const values = agg.values.slice(0, displayCount);

  let chartLabels = labels;
  let chartValues = values;

  if (options.ranked) {
    // Reverse so highest rank appears at top in a horizontal bar chart
    chartLabels = [];
    chartValues = [];
    for (let i = labels.length - 1; i >= 0; i--) {
      chartLabels.push((labels.length - i) + '. ' + labels[i]);
      chartValues.push(values[i]);
    }
  }

  charts[chartName] = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: chartLabels,
      datasets: [{
        data: chartValues,
        backgroundColor: CHART_COLORS.primary,
        hoverBackgroundColor: CHART_COLORS.primaryHover,
        borderRadius: 5,
        barThickness: options.barThickness || 22
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: REDUCED_MOTION ? 0 : 500 },
      plugins: {
        legend: { display: false },
        tooltip: {
          title: function (ctx) { return ctx[0].label; }
        }
      },
      scales: {
        x: Object.assign({
          grid: { display: false },
          border: { display: false }
        }, options.xScale || {}),
        y: Object.assign({
          grid: { display: false },
          border: { display: false },
          ticks: { font: { size: 11.5, weight: '600' }, color: '#0c2443' }
        }, options.yScale || {})
      }
    }
  });
}

function renderCategoryChart(agg) {
  renderBarChart('categoryChart', 'categoryChart', agg, {
    maxBars: MAX_BARS,
    barThickness: 24,
    xScale: { grid: { color: '#e2e8f0' }, border: { display: false }, ticks: { precision: 0 } }
  });
}

function renderAreaChart(agg) {
  renderBarChart('areaChart', 'areaChart', agg, {
    maxBars: MAX_BARS,
    barThickness: 22,
    xScale: { grid: { color: '#e2e8f0' }, border: { display: false }, ticks: { precision: 0 } }
  });
}

function renderTopAreasChart(agg) {
  renderBarChart('topAreasChart', 'topAreasChart', agg, {
    maxBars: 10,
    barThickness: 20,
    ranked: true,
    yScale: { grid: { display: false }, border: { display: false }, ticks: { display: false } }
  });
}

// ===== Master Render =====
function renderAll() {
  // Guard against re-entrant calls that can cause stack overflow
  if (isRendering) return;
  isRendering = true;

  try {
    const dataset = getFilteredDataset();
    const kpis = computeKPIs(dataset.activeMonthIndices, dataset.activeRows);

    renderKPIs(kpis);

    const monthAgg = aggregateByMonth(dataset.activeMonthIndices, dataset.activeRows);
    renderTimeChart(monthAgg);

    const categoryAgg = aggregateByCategory(dataset.activeMonthIndices, dataset.activeRows);
    renderCategoryChart(categoryAgg);

    const areaAgg = aggregateByArea(dataset.activeMonthIndices, dataset.activeRows);
    renderAreaChart(areaAgg);
    renderTopAreasChart(areaAgg);

    renderChips();
    updateRecordRange(dataset);
  } finally {
    isRendering = false;
  }
}

function updateRecordRange(dataset) {
  let filteredTotal = 0;
  for (let r = 0; r < dataset.activeRows.length; r++) {
    const values = dataset.activeRows[r].values;
    for (let m = 0; m < dataset.activeMonthIndices.length; m++) {
      filteredTotal += values[dataset.activeMonthIndices[m]];
    }
  }

  let rangeText = '';
  if (dataset.activeMonthIndices.length > 0) {
    const firstActive = monthColumns[dataset.activeMonthIndices[0]];
    const lastActive = monthColumns[dataset.activeMonthIndices[dataset.activeMonthIndices.length - 1]];
    rangeText = firstActive.key + ' – ' + lastActive.key;
  } else {
    rangeText = 'No matching records';
  }

  els.recordRange.textContent = fmt(filteredTotal) + ' incidents shown (' + rangeText + ')';
}

// ===== Chips Rendering =====
function renderChips() {
  els.chipsRow.innerHTML = '';

  const chipDefs = [
    { key: 'year', label: 'Year', value: filters.year !== 'all' ? filters.year : null },
    { key: 'month', label: 'Month', value: filters.month !== 'all' ? MONTH_NAMES[filters.month] : null },
    { key: 'area', label: 'Area', value: filters.area !== 'all' ? filters.area : null },
    { key: 'category', label: 'Category', value: filters.category !== 'all' ? filters.category : null },
    { key: 'subcategory', label: 'Subcategory', value: filters.subcategory !== 'all' ? filters.subcategory : null }
  ];

  for (let i = 0; i < chipDefs.length; i++) {
    const def = chipDefs[i];
    if (!def.value) continue;

    const chip = document.createElement('div');
    chip.className = 'chip';
    chip.innerHTML = '<span>' + def.label + ': ' + def.value + '</span>';

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.setAttribute('aria-label', 'Clear ' + def.label + ' filter');
    btn.innerHTML = '&times;';
    btn.addEventListener('click', function () {
      filters[def.key] = 'all';
      if (def.key === 'category') updateSubcategoryOptions();
      syncSelects();
      renderAll();
    });
    chip.appendChild(btn);
    els.chipsRow.appendChild(chip);
  }

  // Show a message if no filters are active
  if (els.chipsRow.children.length === 0) {
    const msg = document.createElement('span');
    msg.style.fontSize = '11.5px';
    msg.style.color = 'var(--color-text-muted)';
    msg.textContent = 'No active filters — showing all data';
    els.chipsRow.appendChild(msg);
  }
}

// ===== Visibility Helpers =====
function showLoading(show) {
  els.loadingOverlay.style.display = show ? 'flex' : 'none';
}

function showDashboard(show) {
  els.dashboard.style.display = show ? 'block' : 'none';
}

function showError(message, hint) {
  els.errorMessage.textContent = message || 'Failed to load data.';
  els.errorHint.textContent = hint || 'Please check your internet connection and try refreshing the page.';
  els.errorBanner.style.display = 'flex';
  els.loadingOverlay.style.display = 'none';
  els.dashboard.style.display = 'none';
}

function hideError() {
  els.errorBanner.style.display = 'none';
}
