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

_loadDashMetrics();
document.addEventListener("astro:page-load", _loadDashMetrics);
