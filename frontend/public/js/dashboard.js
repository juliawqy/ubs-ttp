// dashboard.js — Analytics Dashboard (TTP-30)
// Fetches data from the analytics service via /api/analytics/metrics/*

async function loadDashboard() {
  try {
    const kpis = await api.get("/analytics/metrics/kpis");
    renderKPITiles(kpis);
    renderPipelineChart(kpis.pipeline_by_stage);
    renderBiasIncidentsChart(kpis.bias_incidents_trend);
    renderTrainingChart(kpis.training_completion_by_group);
  renderFeedbackInsights(kpis.feedback_insights);
  } catch (e) {
    console.error("Dashboard load failed:", e.message);
    showError(e.message);
  }
}

function renderKPITiles(kpis) {
  document.getElementById("kpi-diversity").textContent =
    kpis.sourcing_diversity_ratio.toFixed(1) + "%";
  document.getElementById("kpi-skills-hire").textContent =
    kpis.offer_acceptance_rate.toFixed(1) + "%";
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
    "background:#fee2e2;color:#b91c1c;padding:.75rem 1rem;border-radius:.5rem;margin-bottom:1rem";
  banner.textContent = "Dashboard error: " + msg;
  container.prepend(banner);
}

function renderFeedbackInsights(insights) {
  const container = document.getElementById("feedback-insights-list");
  if (!insights || insights.length === 0) {
    container.innerHTML = '<p style="color:#6b7280;font-size:0.85rem">No feedback themes available yet.</p>';
    return;
  }
  container.innerHTML = insights.map((item) => `
    <div style="display:flex;gap:1rem;align-items:flex-start;padding:0.75rem 0;border-bottom:1px solid #f3f4f6">
      <div style="flex-shrink:0;background:#fee2e2;color:#b91c1c;border-radius:999px;padding:0.2rem 0.6rem;font-size:0.75rem;font-weight:700;white-space:nowrap">
        ${item.mentions}x
      </div>
      <div>
        <div style="font-weight:600;font-size:0.88rem;color:#1f2937;margin-bottom:0.2rem">${item.theme}</div>
        <div style="font-size:0.82rem;color:#6b7280">${item.suggestion}</div>
      </div>
    </div>`).join("");
}

document.addEventListener("DOMContentLoaded", loadDashboard);
