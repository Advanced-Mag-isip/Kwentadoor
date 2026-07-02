var API_BASE = "http://127.0.0.1:8000/api/expenses";

function _authHeaders() {
  var token = localStorage.getItem("auth_token");
  return token ? { Authorization: "Token " + token } : {};
}

function _loadDashMetrics() {
  const now = new Date();
  const y = now.getFullYear();
  const m = now.getMonth() + 1;
  fetch("http://127.0.0.1:8000/api/analytics/charts/monthly-metrics/?year=" + y + "&month=" + m, { headers: Object.assign({ Accept: "application/json" }, _authHeaders()) })
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
  options = options || {};
  return fetch(API_BASE + path, {
    ...options,
    headers: Object.assign(
      { "Content-Type": "application/json", Accept: "application/json" },
      _authHeaders(),
      options.headers || {}
    ),
  }).then(function (r) {
    if (!r.ok) {
      return r.text().then(function (text) {
        try {
          var json = JSON.parse(text);
          throw new Error(JSON.stringify(json));
        } catch (e) {
          throw new Error(text || r.statusText || "Request failed");
        }
      });
    }
    return r.json();
  });
}

window.__spendFunds = function (data) {
  return apiFetch("/spends/", {
    method: "POST",
    body: JSON.stringify({
      wallet: parseInt(data.wallet),
      amount: parseFloat(data.amount),
      category: data.category || "office_supplies",
      note: data.note || "",
      counterparty: data.counterparty || "",
      transaction_date: data.transaction_date || new Date().toISOString().split("T")[0],
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

function _parseApiDate(value) {
  if (!value) return new Date(NaN);
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    var parts = value.split("-");
    return new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
  }
  return new Date(value);
}

function _formatTransactionDate(value) {
  var date = _parseApiDate(value);
  return isNaN(date.getTime())
    ? ""
    : date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function _sortByRecency(list) {
  return list.slice().sort(function (a, b) {
    var dateA = _parseApiDate(a.transaction_date).getTime();
    var dateB = _parseApiDate(b.transaction_date).getTime();
    if (dateB !== dateA) return dateB - dateA;
    // Same-day tiebreaker: higher id = created more recently
    return (b.id || 0) - (a.id || 0);
  });
}

window.__loadRecentTransactions = function (filter) {
  var url = "/transactions/?limit=100";
  var container = document.querySelector(".transaction-history-slots");
  apiFetch(url).then(function (data) {
    var list = data.results || data;
    if (filter === "added") {
      list = list.filter(function (t) { return t.transaction_type === "add funds"; });
    } else if (filter === "spent") {
      list = list.filter(function (t) { return t.transaction_type === "spend funds"; });
    }
    list = _sortByRecency(list).slice(0, 20);
    if (!container) return;
    if (list.length === 0) {
      container.innerHTML = '<div class="transactionrow"><p style="text-align:center;opacity:0.5">No transactions yet</p></div>';
      return;
    }
    container.innerHTML = list.map(function (t) {
      var amt = Number(t.amount).toLocaleString("en-PH", { minimumFractionDigits: 2 });
      var date = _formatTransactionDate(t.transaction_date);
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
  }).catch(function (err) {
    console.error("Failed to load transactions for filter '" + filter + "':", err);
    if (container) {
      container.innerHTML = '<div class="transactionrow"><p style="text-align:center;color:#e74c3c">Failed to load transactions. Check console for details.</p></div>';
    }
  });
};

window._loadDashMetrics = _loadDashMetrics;

function _loadInitialTransactions() {
  window.__loadRecentTransactions?.();
  window.__loadWalletBalance?.();
}

_loadDashMetrics();
_loadInitialTransactions();
document.addEventListener("astro:page-load", _loadDashMetrics);
document.addEventListener("astro:page-load", _loadInitialTransactions);