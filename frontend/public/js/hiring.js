// hiring.js — client-side logic for the Hiring page

// ─── Tab switching ─────────────────────────────────────────────────────────────
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => {
      b.classList.remove("btn-primary");
      b.classList.add("btn-outline");
    });
    btn.classList.add("btn-primary");
    btn.classList.remove("btn-outline");

    ["job-postings", "candidates", "interviews"].forEach((id) => {
      document.getElementById(`tab-${id}`).style.display = "none";
    });
    document.getElementById(`tab-${btn.dataset.tab}`).style.display = "block";

    if (btn.dataset.tab === "job-postings") loadPostings();
    if (btn.dataset.tab === "candidates") loadCandidates();
    if (btn.dataset.tab === "interviews") loadInterviews();
  });
});

// ─── Job Postings ──────────────────────────────────────────────────────────────
async function loadPostings() {
  const tbody = document.getElementById("postings-tbody");
  try {
    const data = await api.get("/recruitment/job-postings");
    tbody.innerHTML = data.map((p) => `
      <tr>
        <td>${p.title}</td>
        <td>${p.department}</td>
        <td>${p.posted_date}</td>
        <td>${p.applicant_count}</td>
        <td><span class="badge badge-green">${p.status}</span></td>
        <td><a href="/hiring/posting/${p.id}" class="btn btn-outline" style="padding:0.3rem 0.7rem;font-size:0.8rem">View</a></td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6" style="color:#ef4444">${e.message}</td></tr>`;
  }
}

// ─── Candidates ────────────────────────────────────────────────────────────────
async function loadCandidates() {
  const tbody = document.getElementById("candidates-tbody");
  try {
    const data = await api.get("/recruitment/candidates");
    tbody.innerHTML = data.map((c) => `
      <tr>
        <td>Candidate #${c.id}</td>
        <td>${c.skills_score}/100</td>
        <td>${c.years_experience} yrs</td>
        <td><span class="badge ${c.assessment_passed ? "badge-green" : "badge-red"}">${c.assessment_passed ? "Passed" : "Failed"}</span></td>
        <td>
          <button class="btn btn-primary" style="padding:0.3rem 0.7rem;font-size:0.8rem" onclick="shortlist(${c.id})">Shortlist</button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:#ef4444">${e.message}</td></tr>`;
  }
}

async function shortlist(candidateId) {
  await api.post(`/recruitment/candidates/${candidateId}/shortlist`, {});
  loadCandidates();
}

// ─── Interviews ────────────────────────────────────────────────────────────────
async function loadInterviews() {
  const tbody = document.getElementById("interviews-tbody");
  try {
    const data = await api.get("/recruitment/interviews");
    tbody.innerHTML = data.map((i) => `
      <tr>
        <td>Candidate #${i.candidate_id}</td>
        <td>${i.role}</td>
        <td>${i.scheduled_date}</td>
        <td>${i.panel_members.join(", ")}</td>
        <td><span class="badge badge-yellow">${i.status}</span></td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:#ef4444">${e.message}</td></tr>`;
  }
}

// Load initial tab
loadPostings();
