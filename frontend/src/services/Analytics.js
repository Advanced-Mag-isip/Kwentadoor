const BASE_URL = import.meta.env.PUBLIC_API_URL
  ? `${import.meta.env.PUBLIC_API_URL}/analytics`
  : "http://127.0.0.1:8000/api/analytics";
  
async function safeFetch(url) {
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  const text = await res.text();
  if (!res.ok) {
    console.error("API ERROR:", url, text);
    throw new Error(`HTTP ${res.status} at ${url}`);
  }
  try {
    return JSON.parse(text);
  } catch (err) {
    console.error("INVALID JSON RESPONSE:", url, text);
    throw err;
  }
}

export function getSummary(period = "yearly", year = 2026, month = null) {
  let qs = `period=${period}&year=${year}`;
  if (month) qs += `&month=${month}`;
  return safeFetch(`${BASE_URL}/summary/?${qs}`);
}

export function getIncomeVsExpenses(period = "yearly", year = 2026, month = null) {
  let qs = `period=${period}&year=${year}`;
  if (month) qs += `&month=${month}`;
  return safeFetch(`${BASE_URL}/charts/income-vs-expenses/?${qs}`);
}

export function getRunaway(period = "yearly", year = 2026, month = null) {
  let qs = `period=${period}&year=${year}`;
  if (month) qs += `&month=${month}`;
  return safeFetch(`${BASE_URL}/charts/funding-runaway-projection/?${qs}`);
}

export function getExpensesByCategory(period = "yearly", year = 2026, month = null) {
  let qs = `period=${period}&year=${year}`;
  if (month) qs += `&month=${month}`;
  return safeFetch(`${BASE_URL}/charts/expenses-by-category/?${qs}`);
}

export function getIncomeUtilization(period = "yearly", year = 2026, month = null) {
  let qs = `period=${period}&year=${year}`;
  if (month) qs += `&month=${month}`;
  return safeFetch(`${BASE_URL}/charts/income-utilization/?${qs}`);
}
