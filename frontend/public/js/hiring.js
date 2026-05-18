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
  });
});

// ─── Job Postings ──────────────────────────────────────────────────────────────
async function loadPostings() {
  const tbody = document.getElementById("postings-tbody");
  try {
    const data = await api.get("/job-postings");
    if (data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:#6b7280">No postings yet. Create the first one.</td></tr>`;
      return;
    }
    tbody.innerHTML = data.map((p) => {
      const biasBadge = p.bias_check.flagged
        ? `<span class="badge badge-red">⚠ ${p.bias_check.flagged_phrases.length} flag(s)</span>`
        : `<span class="badge badge-green">Clean</span>`;
      const statusBadge = `<span class="badge badge-yellow">${p.status}</span>`;
      return `<tr>
        <td>${p.title}</td>
        <td>${p.department}</td>
        <td>${p.manager.name}</td>
        <td>${statusBadge}</td>
        <td>${biasBadge}</td>
      </tr>`;
    }).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:#ef4444">${e.message}</td></tr>`;
  }
}

// ─── New Posting Modal ─────────────────────────────────────────────────────────
const modal = document.getElementById("new-posting-modal");
const modalForm = document.getElementById("new-posting-form");

document.getElementById("new-posting-btn").addEventListener("click", () => {
  modalForm.reset();
  document.getElementById("bias-result").style.display = "none";
  document.getElementById("bias-result").innerHTML = "";
  document.getElementById("form-error").style.display = "none";
  document.getElementById("modal-submit").textContent = "Submit Posting";
  document.getElementById("modal-submit").disabled = false;
  modal.classList.add("open");
});

document.getElementById("modal-cancel").addEventListener("click", closeModal);

modal.addEventListener("click", (e) => {
  if (e.target === modal) closeModal();
});

function closeModal() {
  modal.classList.remove("open");
}

modalForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const submitBtn = document.getElementById("modal-submit");

  const requirements = form.requirements.value
    .split(",")
    .map((r) => r.trim())
    .filter(Boolean);

  const body = {
    title: form.title.value.trim(),
    description: form.description.value.trim(),
    requirements,
    department: form.department.value.trim(),
    manager: {
      id: form.manager_id.value.trim(),
      name: form.manager_name.value.trim(),
      department: form.manager_dept.value.trim(),
      email: form.manager_email.value.trim(),
    },
  };

  submitBtn.disabled = true;
  submitBtn.textContent = "Submitting…";
  document.getElementById("form-error").style.display = "none";

  try {
    const result = await api.post("/job-postings", body);

    if (result.bias_check.flagged) {
      const biasDiv = document.getElementById("bias-result");
      biasDiv.innerHTML = `
        <div class="ai-banner">
          <div class="ai-label">Bias Detected — Advisory Only</div>
          The following phrases may introduce bias. You can revise before the hiring department reviews your request.
          <ul style="margin-top:0.5rem;padding-left:1.2rem">
            ${result.bias_check.flagged_phrases.map((fp) =>
              `<li><strong>"${fp.phrase}"</strong> — ${fp.reason}. <em>Suggestion: ${fp.suggestion}</em></li>`
            ).join("")}
          </ul>
        </div>`;
      biasDiv.style.display = "block";
      submitBtn.textContent = "Close";
      submitBtn.disabled = false;
      submitBtn.type = "button";
      submitBtn.addEventListener("click", closeModal, { once: true });
    } else {
      closeModal();
    }

    loadPostings();
  } catch (err) {
    const errEl = document.getElementById("form-error");
    errEl.textContent = err.message;
    errEl.style.display = "block";
    submitBtn.disabled = false;
    submitBtn.textContent = "Submit Posting";
  }
});

// ─── Candidates ────────────────────────────────────────────────────────────────
async function loadCandidates() {
  const tbody = document.getElementById("candidates-tbody");
  try {
    const data = await api.get("/candidates");
    if (data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="2" style="text-align:center;color:#6b7280">No candidates uploaded yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = data.map((c) => {
      const preview = c.redacted_text.length > 120
        ? c.redacted_text.slice(0, 120) + "…"
        : c.redacted_text;
      return `<tr>
        <td>Candidate #${c.candidate_id}</td>
        <td style="max-width:420px">${preview}</td>
      </tr>`;
    }).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="2" style="color:#ef4444">${e.message}</td></tr>`;
  }
}

document.getElementById("upload-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fileInput = document.getElementById("cv-file");
  const statusEl = document.getElementById("upload-status");
  const file = fileInput.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  statusEl.textContent = "Uploading…";
  statusEl.style.color = "#6b7280";

  try {
    const response = await fetch("/api/candidates/upload", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `Upload failed (${response.status})`);
    }
    const result = await response.json();
    statusEl.textContent = `Uploaded — Candidate ID: ${result.candidate_id}`;
    statusEl.style.color = "#22c55e";
    fileInput.value = "";
    loadCandidates();
  } catch (err) {
    statusEl.textContent = err.message;
    statusEl.style.color = "#ef4444";
  }
});

// ─── Panel Assignment ──────────────────────────────────────────────────────────
document.getElementById("assign-panel-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const errorEl = document.getElementById("panel-error");
  const resultDiv = document.getElementById("panel-result");

  errorEl.style.display = "none";
  resultDiv.style.display = "none";

  let pool;
  try {
    pool = JSON.parse(form.pool_json.value);
  } catch {
    errorEl.textContent = "Invalid JSON — check the interviewer pool format.";
    errorEl.style.display = "block";
    return;
  }

  const body = {
    interviewer_pool: pool,
    panel_size: parseInt(form.panel_size.value, 10) || 3,
    mandatory_ids: form.mandatory_ids.value
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean),
  };

  try {
    const result = await api.post("/interviews/assign-panel", body);
    const approvedBadge = result.approved
      ? `<span class="badge badge-green">Approved</span>`
      : `<span class="badge badge-red">Needs Review</span>`;

    resultDiv.innerHTML = `
      <div class="card" style="margin-top:1.25rem">
        <div class="card-title">Suggested Panel — ${approvedBadge}</div>
        ${!result.approved ? `<p style="color:#ef4444;margin-bottom:0.75rem">${result.rejection_reason}</p>` : ""}
        <table>
          <thead>
            <tr><th>Name</th><th>Department</th><th>Gender</th><th>Seniority</th></tr>
          </thead>
          <tbody>
            ${result.interviewers.map((iv) => `
              <tr>
                <td>${iv.name}</td>
                <td>${iv.department}</td>
                <td>${iv.gender}</td>
                <td>${iv.seniority}</td>
              </tr>`).join("")}
          </tbody>
        </table>
        <p style="margin-top:0.75rem;font-size:0.82rem;color:#6b7280">
          This is a suggestion only. The final decision rests with the hiring manager.
        </p>
      </div>`;
    resultDiv.style.display = "block";
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.style.display = "block";
  }
});

// ─── Initial load ──────────────────────────────────────────────────────────────
loadPostings();
