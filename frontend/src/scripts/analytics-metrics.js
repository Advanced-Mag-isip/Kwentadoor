import { getSummary } from "../services/Analytics.js";

function fmt(n) {
  if (n == null || isNaN(n)) return "---";
  return Number(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

async function _loadMetrics() {
  const f = window.__chartFilters;
  const period = f?.period || "yearly";
  const year = f?.year || new Date().getFullYear();
  const month = f?.month || null;

  try {
    let data = await getSummary(period, year, month);
    if (Array.isArray(data)) {
      data = data.find(d => d.year === year) || data[0] || {};
    }

    document.getElementById("metric-incoming-value").textContent = "\u20B1" + fmt(data.total_incoming_funds);
    document.getElementById("metric-outgoing-value").textContent = "\u20B1" + fmt(data.total_outgoing_funds);
    document.getElementById("metric-avg-incoming-value").textContent = "\u20B1" + fmt(data.average_incoming_funds);
    document.getElementById("metric-avg-outgoing-value").textContent = "\u20B1" + fmt(data.average_outgoing_funds);
    document.getElementById("metric-payroll-value").textContent = "\u20B1" + fmt(data.total_payroll_cost);
    document.getElementById("metric-missing-value").textContent = data.total_missing_receipts != null ? String(data.total_missing_receipts) : "---";
    document.getElementById("metric-undocumented-value").textContent = data.undocumented_expenses_pct != null ? data.undocumented_expenses_pct + "%" : "---";
    document.getElementById("metric-growth-value").textContent = data.expense_growth != null ? data.expense_growth + "%" : "---";
  } catch (err) {
    document.querySelectorAll(".metric-value").forEach(el => { el.textContent = "Error"; });
  }
}

document.addEventListener("chart-update", _loadMetrics);
