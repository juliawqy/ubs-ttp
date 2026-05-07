// dashboard.js — client-side logic for the Dashboard page

async function loadDashboard() {
  try {
    const kpis = await api.get("/analytics/metrics/kpis");

    document.getElementById("kpi-diversity").textContent = kpis.sourcing_diversity_ratio + "%";
    document.getElementById("kpi-skills-hire").textContent = kpis.skills_hire_rate + "%";
    document.getElementById("kpi-promo-velocity").textContent = kpis.avg_promotion_months + " mo";
    document.getElementById("kpi-enps").textContent = kpis.enps_score;

    renderPipelineChart(kpis.pipeline_by_stage);
    renderPromotionChart(kpis.promotion_velocity_by_group);
    renderTrainingChart(kpis.training_utilisation_by_group);
  } catch (e) {
    console.error("Dashboard load failed:", e.message);
  }
}

function renderPipelineChart(data) {
  new Chart(document.getElementById("chart-pipeline"), {
    type: "bar",
    data: {
      labels: data.map((d) => d.stage),
      datasets: [{
        label: "Underrepresented %",
        data: data.map((d) => d.pct),
        backgroundColor: "#e00b1c",
      }],
    },
    options: { responsive: true, plugins: { legend: { display: false } } },
  });
}

function renderPromotionChart(data) {
  new Chart(document.getElementById("chart-promotion"), {
    type: "bar",
    data: {
      labels: data.map((d) => d.group),
      datasets: [{
        label: "Months to Promotion",
        data: data.map((d) => d.months),
        backgroundColor: "#1a1a2e",
      }],
    },
    options: { responsive: true, plugins: { legend: { display: false } } },
  });
}

function renderTrainingChart(data) {
  new Chart(document.getElementById("chart-training"), {
    type: "bar",
    data: {
      labels: data.map((d) => d.group),
      datasets: [{
        label: "Utilisation %",
        data: data.map((d) => d.pct),
        backgroundColor: "#e00b1c",
      }],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      plugins: { legend: { display: false } },
    },
  });
}

loadDashboard();
