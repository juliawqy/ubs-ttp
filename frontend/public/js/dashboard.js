// dashboard.js — Analytics Dashboard (TTP-30)
// Fetches data from the analytics service via /api/analytics/metrics/*

async function loadDashboard() {
  try {
    const kpis = await api.get("/analytics/metrics/kpis");
    renderKPITiles(kpis);
    renderPipelineChart(kpis.pipeline_by_stage);
    renderBiasIncidentsChart(kpis.bias_incidents_trend);
    renderTrainingChart(kpis.training_completion_by_group);
  } catch (e) {
    console.error("Dashboard load failed:", e.message);
    showError(e.message);
  }
}

function renderKPITiles(kpis) {
  document.getElementById("kpi-diversity").textContent =
    kpis.sourcing_diversity_ratio.toFixed(1) + "%";
  document.getElementById("kpi-skills-hire").textContent =
    kpis.skills_hire_rate.toFixed(1) + "%";
  document.getElementById("kpi-promo-velocity").textContent =
    kpis.avg_promotion_months + " mo";
  document.getElementById("kpi-enps").textContent = kpis.enps_score;
}

function renderPipelineChart(data) {
  // Stacked bar: each stage shows total, coloured by diverse % vs majority
  const labels = data.map((d) => capitalise(d.stage));
  const diverseCounts = data.map((d) => Math.round((d.pct / 100) * d.total));
  const majorityCounts = data.map((d) => d.total - Math.round((d.pct / 100) * d.total));

  new Chart(document.getElementById("chart-pipeline"), {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Diverse candidates",
          data: diverseCounts,
          backgroundColor: "#e00b1c",
        },
        {
          label: "All others",
          data: majorityCounts,
          backgroundColor: "#d1d5db",
        },
      ],
    },
    options: {
      responsive: true,
      scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true } },
      plugins: {
        legend: { position: "bottom" },
        tooltip: {
          callbacks: {
            afterBody: (items) => {
              const total = items.reduce((s, i) => s + i.raw, 0);
              return `Total: ${total}`;
            },
          },
        },
      },
    },
  });
}

function renderBiasIncidentsChart(trend) {
  if (!trend || trend.length === 0) return;

  // Show last 12 weeks; abbreviate period label to week number
  const labels = trend.map((d) => {
    const parts = d.period.split("-W");
    return "W" + parts[1];
  });
  const counts = trend.map((d) => d.count);

  new Chart(document.getElementById("chart-bias"), {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Bias incidents",
          data: counts,
          borderColor: "#e00b1c",
          backgroundColor: "rgba(224,11,28,0.08)",
          tension: 0.35,
          fill: true,
          pointRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
      plugins: { legend: { display: false } },
    },
  });
}

function renderTrainingChart(data) {
  new Chart(document.getElementById("chart-training"), {
    type: "bar",
    data: {
      labels: data.map((d) => capitalise(d.group.replace("_", " "))),
      datasets: [
        {
          label: "Completion %",
          data: data.map((d) => d.pct),
          backgroundColor: "#1a1a2e",
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      scales: { x: { beginAtZero: true, max: 100 } },
      plugins: { legend: { display: false } },
    },
  });
}

function capitalise(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function showError(msg) {
  const container = document.querySelector(".container");
  if (!container) return;
  const banner = document.createElement("div");
  banner.style.cssText =
    "background:#fee2e2;color:#b91c1c;padding:.75rem 1rem;border-radius:.5rem;margin-bottom:1rem;font-size:.875rem;";
  banner.textContent = "Dashboard data unavailable: " + msg;
  container.prepend(banner);
}

loadDashboard();
