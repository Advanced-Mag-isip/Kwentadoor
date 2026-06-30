var API_BASE = "http://127.0.0.1:8000/api/expenses";

function _loadDashMetrics() {
  const now = new Date();
  const y = now.getFullYear();
  const m = now.getMonth() + 1;
  fetch("http://127.0.0.1:8000/api/analytics/charts/monthly-metrics/?year=" + y + "&month=" + m, { headers: { Accept: "application/json" } })
    .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
    .then(function (d) {
      var fmt = function (n) { return "\u20B1" + Number(n).toLocaleString("en-US", { minimumFractionDigits: 2 }); };
      var el = document.getElementById("dash-incoming-value"); if (el) el.textContent = fmt(d.incoming);
      el = document.getElementById("dash-outgoing-value"); if (el) el.textContent = fmt(d.outgoing);
      el = document.getElementById("dash-profit-value"); if (el) el.textContent = fmt(d.profit);
      el = document.getElementById("dash-transactions-value"); if (el) el.textContent = d.transaction_count;
    })
    .catch(function () {
      ["dash-incoming-value","dash-outgoing-value","dash-profit-value","dash-transactions-value"].forEach(function(id) { var el = document.getElementById(id); if (el) el.textContent = "Error"; });
    });
}

function apiFetch(path, options) {
  return fetch(API_BASE + path, {
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    ...options,
  }).then(function (r) {
    if (!r.ok) return r.json().then(function (e) { throw new Error(JSON.stringify(e)); });
    return r.json();
  });
}

window.__addFunds = function (data) {
  return apiFetch("/transactions/", {
    method: "POST",
    body: JSON.stringify({
      transaction_type: "add funds",
      wallet: parseInt(data.wallet),
      amount: parseFloat(data.amount),
      note: data.note || "",
      category: "add_funds",
      transaction_date: data.transaction_date || new Date().toISOString().split("T")[0],
      counterparty: data.counterparty || "",
    }),
  });
};

window.__spendFunds = function (data) {
  return apiFetch("/spends/", {
    method: "POST",
    body: JSON.stringify({
      wallet: parseInt(data.wallet),
      amount: parseFloat(data.amount),
      category: data.category || "office_supplies",
      note: data.note || "",
      counterparty: data.counterparty || "",
      transaction_date: data.transaction_date || "",
    }),
  });
};

window.__moveFunds = function (data) {
  return apiFetch("/transfers/", {
    method: "POST",
    body: JSON.stringify({
      from_wallet: parseInt(data.from_wallet),
      to_wallet: parseInt(data.to_wallet),
      amount: parseFloat(data.amount),
    }),
  });
};

window.__loadWalletBalance = function () {
  apiFetch("/wallets/").then(function (data) {
    var list = data.results || data;
    var total = list.reduce(function (s, w) { return s + parseFloat(w.balance || 0); }, 0);
    var el = document.getElementById("balance-amount");
    if (el) {
      el.textContent = "\u20B1" + total.toLocaleString("en-PH", { minimumFractionDigits: 2 });
      el.dataset.balance = el.textContent;
    }
  }).catch(function () {});
};

window.__loadRecentTransactions = function (filter) {
  var url = "/transactions/?limit=20";
  if (filter && filter !== "all") {
    url += "&transaction_type=" + (filter === "added" ? "add funds" : "spend funds");
  }
  apiFetch(url).then(function (data) {
    var list = data.results || data;
    var container = document.querySelector(".transaction-history-slots");
    if (!container) return;
    if (list.length === 0) {
      container.innerHTML = '<div class="transactionrow"><p colspan="6" style="text-align:center;opacity:0.5">No transactions yet</p></div>';
      return;
    }
    container.innerHTML = list.map(function (t) {
      var amt = Number(t.amount).toLocaleString("en-PH", { minimumFractionDigits: 2 });
      var date = new Date(t.transaction_date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
      var note = t.note || "--";
      var uname = t.user_name || "User 1";
      var wname = t.wallet_name || "";
      var cat = t.BIR_label || t.category || "";
      var isAdd = t.transaction_type === "add funds";
      var isSpend = t.transaction_type === "spend funds";
      var color = isAdd ? "#2ecc71" : (isSpend ? "#e74c3c" : "#f39c12");
      var sign = isAdd ? "+" : (isSpend ? "-" : "~");
      return '<div class="transactionrow">'
        + '<p style="color:' + color + ';font-weight:600">' + sign + '\u20B1' + amt + '</p>'
        + '<p>' + wname + '</p>'
        + '<p>' + cat + '</p>'
        + '<p>' + note + '</p>'
        + '<p>' + uname + '</p>'
        + '<p>' + date + '</p>'
        + '</div>';
    }).join("");
  }).catch(function () {});
};

window._loadDashMetrics = _loadDashMetrics;

_loadDashMetrics();
document.addEventListener("astro:page-load", _loadDashMetrics);
window.__loadDashboardMetrics = loadDashboardMetrics;
