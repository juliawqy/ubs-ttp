// hiring.js

// ── Tab switching ──────────────────────────────────────────────────────────────
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

// ── Job Postings ───────────────────────────────────────────────────────────────
async function loadPostings() {
  const tbody = document.getElementById("postings-tbody");
  try {
    const data = await api.get("/job-postings");
    if (data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:#6b7280">No postings yet. Create the first one.</td></tr>`;
      return;
    }
    _postingsCache = data;
    tbody.innerHTML = data.map((p, i) => {
      const biasBadge = p.bias_check.flagged
        ? `<span class="badge badge-red">&#9888; ${p.bias_check.flagged_phrases.length} flag(s)</span>`
        : `<span class="badge badge-green">Clean</span>`;
      return `<tr style="cursor:pointer" onclick="openPostingDetail(${i})">
        <td>${p.title}</td>
        <td>${p.department}</td>
        <td>${p.manager.name}</td>
        <td><span class="badge badge-yellow">${p.status}</span></td>
        <td>${biasBadge}</td>
      </tr>`;
    }).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:#ef4444">${e.message}</td></tr>`;
  }
}

let _postingsCache = [];
let _currentDetailIndex = null;

function openPostingDetail(index) {
  const p = _postingsCache[index];
  if (!p) return;
  _currentDetailIndex = index;
  const biasHtml = p.bias_check.flagged
    ? `<div class="ai-banner" style="margin-top:1rem">
        <div class="ai-label">Bias Detected - Advisory Only</div>
        <ul style="margin-top:0.5rem;padding-left:1.2rem">
          ${p.bias_check.flagged_phrases.map((fp) =>
            `<li><strong>"${fp.phrase}"</strong> — ${fp.reason}. <em>Suggestion: ${fp.suggestion}</em></li>`
          ).join("")}
        </ul>
      </div>`
    : `<p style="color:#22c55e;margin-top:0.75rem;font-size:0.85rem">No biased language detected.</p>`;

  const reqList = (p.requirements || []).map((r) => `<li>${r}</li>`).join("") || "<li>—</li>";

  const detailModal = document.getElementById("posting-detail-modal");
  detailModal.querySelector("#detail-title").textContent = p.title;
  detailModal.querySelector("#detail-body").innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;margin-bottom:1rem">
      <div><span style="font-size:0.75rem;color:#6b7280;text-transform:uppercase">Department</span><p style="margin:0.2rem 0 0;font-weight:600">${p.department}</p></div>
      <div><span style="font-size:0.75rem;color:#6b7280;text-transform:uppercase">Status</span><p style="margin:0.2rem 0 0"><span class="badge badge-yellow">${p.status}</span></p></div>
      <div><span style="font-size:0.75rem;color:#6b7280;text-transform:uppercase">Manager</span><p style="margin:0.2rem 0 0;font-weight:600">${p.manager.name}</p></div>
      <div><span style="font-size:0.75rem;color:#6b7280;text-transform:uppercase">Manager Email</span><p style="margin:0.2rem 0 0">${p.manager.email}</p></div>
    </div>
    <p style="font-size:0.75rem;color:#6b7280;text-transform:uppercase;margin-bottom:0.3rem">Description</p>
    <p style="margin:0 0 1rem;line-height:1.5">${p.description}</p>
    <p style="font-size:0.75rem;color:#6b7280;text-transform:uppercase;margin-bottom:0.3rem">Requirements</p>
    <ul style="margin:0 0 0 1.2rem;padding:0;line-height:1.6">${reqList}</ul>
    <p style="font-size:0.75rem;color:#6b7280;text-transform:uppercase;margin-top:1rem;margin-bottom:0.3rem">Bias Check</p>
    ${biasHtml}`;
  detailModal.classList.add("open");
}

const modal = document.getElementById("new-posting-modal");
const modalForm = document.getElementById("new-posting-form");
let editingPostingId = null;

function _resetPostingModal() {
  editingPostingId = null;
  modalForm.reset();
  document.getElementById("bias-result").style.display = "none";
  document.getElementById("bias-result").innerHTML = "";
  document.getElementById("form-error").style.display = "none";
  document.getElementById("modal-title").textContent = "Request New Job Posting";
  const submitBtn = document.getElementById("modal-submit");
  submitBtn.type = "submit";
  submitBtn.textContent = "Submit Posting";
  submitBtn.disabled = false;
}

document.getElementById("new-posting-btn").addEventListener("click", () => {
  _resetPostingModal();
  modal.classList.add("open");
});

function openEditPostingModal(index) {
  const p = _postingsCache[index];
  if (!p) return;
  document.getElementById("posting-detail-modal").classList.remove("open");
  _resetPostingModal();
  editingPostingId = p.id;
  document.getElementById("modal-title").textContent = "Edit Job Posting";
  modalForm.title.value = p.title;
  modalForm.description.value = p.description;
  modalForm.requirements.value = (p.requirements || []).join(", ");
  modalForm.department.value = p.department;
  modalForm.manager_id.value = p.manager.id;
  modalForm.manager_name.value = p.manager.name;
  modalForm.manager_dept.value = p.manager.department;
  modalForm.manager_email.value = p.manager.email;
  document.getElementById("modal-submit").textContent = "Save Changes";
  modal.classList.add("open");
}

document.getElementById("detail-edit-btn").addEventListener("click", () => {
  if (_currentDetailIndex !== null) openEditPostingModal(_currentDetailIndex);
});

document.getElementById("posting-detail-modal").addEventListener("click", (e) => {
  if (e.target === document.getElementById("posting-detail-modal"))
    document.getElementById("posting-detail-modal").classList.remove("open");
});
document.getElementById("modal-cancel").addEventListener("click", () => modal.classList.remove("open"));
modal.addEventListener("click", (e) => { if (e.target === modal) modal.classList.remove("open"); });

modalForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const submitBtn = document.getElementById("modal-submit");
  const requirements = form.requirements.value.split(",").map((r) => r.trim()).filter(Boolean);
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
  const isEdit = editingPostingId !== null;
  submitBtn.disabled = true;
  submitBtn.textContent = isEdit ? "Saving..." : "Submitting...";
  document.getElementById("form-error").style.display = "none";
  try {
    const result = isEdit
      ? await api.put(`/job-postings/${editingPostingId}`, body)
      : await api.post("/job-postings", body);
    if (result.bias_check.flagged) {
      const biasDiv = document.getElementById("bias-result");
      biasDiv.innerHTML = `
        <div class="ai-banner">
          <div class="ai-label">Bias Detected - Advisory Only</div>
          The following phrases may introduce bias. The posting has already been ${isEdit ? "saved" : "submitted"} — review the notes below and edit again if you'd like to revise.
          <ul style="margin-top:0.5rem;padding-left:1.2rem">
            ${result.bias_check.flagged_phrases.map((fp) =>
              `<li><strong>"${fp.phrase}"</strong> - ${fp.reason}. <em>Suggestion: ${fp.suggestion}</em></li>`
            ).join("")}
          </ul>
        </div>`;
      biasDiv.style.display = "block";
      submitBtn.disabled = true;
      submitBtn.textContent = isEdit ? "Saved" : "Submitted";
      document.getElementById("modal-cancel").textContent = "Close";
    } else {
      modal.classList.remove("open");
    }
    loadPostings();
  } catch (err) {
    const errEl = document.getElementById("form-error");
    errEl.textContent = err.message;
    errEl.style.display = "block";
    submitBtn.disabled = false;
    submitBtn.textContent = isEdit ? "Save Changes" : "Submit Posting";
  }
});

// ── Candidates ─────────────────────────────────────────────────────────────────
async function loadCandidates() {
  const tbody = document.getElementById("candidates-tbody");
  try {
    const data = await api.get("/candidates");
    if (data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:#6b7280">No candidates uploaded yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = data.map((c) => {
      const preview = c.redacted_text.length > 100 ? c.redacted_text.slice(0, 100) + "..." : c.redacted_text;
      const statusBadge = c.status === "hired"
        ? `<span class="badge badge-green">Hired</span>`
        : c.status === "rejected"
        ? `<span class="badge badge-red">Rejected</span>`
        : `<span class="badge badge-yellow">Pending</span>`;
      const scoreCell = c.latest_assessment
        ? `${c.latest_assessment.total_score.toFixed(2)} / 10`
        : `<span style="color:#9ca3af">—</span>`;
      const decisionCell = c.decision
        ? `<span style="font-size:0.82rem">${c.decision.justification}${c.decision.bias_flagged ? ' <span class="badge badge-red" style="font-size:0.68rem">bias noted</span>' : ''}</span>`
        : `<span style="color:#9ca3af">—</span>`;
      const isDecided = c.status !== "pending";
      return `<tr>
        <td>Candidate #${c.candidate_id}</td>
        <td style="max-width:280px">${preview}</td>
        <td>${statusBadge}</td>
        <td style="white-space:nowrap">${scoreCell}</td>
        <td style="max-width:220px">${decisionCell}</td>
        <td style="white-space:nowrap">
          <button class="btn btn-outline" style="font-size:0.78rem;padding:0.25rem 0.6rem;margin-right:0.35rem"
            onclick="openAssessModal(${c.candidate_id})" ${isDecided ? "disabled" : ""}>Assess</button>
          <button class="btn btn-primary" style="font-size:0.78rem;padding:0.25rem 0.6rem"
            onclick="openDecideModal(${c.candidate_id})" ${isDecided ? "disabled" : ""}>Decide</button>
        </td>
      </tr>`;
    }).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6" style="color:#ef4444">${e.message}</td></tr>`;
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
  statusEl.textContent = "Uploading...";
  statusEl.style.color = "#6b7280";
  try {
    const response = await fetch("/api/candidates/upload", { method: "POST", body: formData });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `Upload failed (${response.status})`);
    }
    const result = await response.json();
    statusEl.textContent = `Uploaded - Candidate ID: ${result.candidate_id}`;
    statusEl.style.color = "#22c55e";
    fileInput.value = "";
    loadCandidates();
  } catch (err) {
    statusEl.textContent = err.message;
    statusEl.style.color = "#ef4444";
  }
});

// ── Skills Assessment Modal ────────────────────────────────────────────────────
const assessModal = document.getElementById("assess-modal");
let assessCandidateId = null;

function openAssessModal(candidateId) {
  assessCandidateId = candidateId;
  document.getElementById("assess-candidate-id").textContent = candidateId;
  document.getElementById("assess-result").style.display = "none";
  document.getElementById("assess-error").style.display = "none";
  document.getElementById("assess-form").style.display = "block";
  renderCriteriaRows();
  assessModal.classList.add("open");
}

document.getElementById("assess-cancel").addEventListener("click", () => assessModal.classList.remove("open"));
assessModal.addEventListener("click", (e) => { if (e.target === assessModal) assessModal.classList.remove("open"); });

let criteria = [
  { name: "python", weight: "0.6", required: true },
  { name: "sql",    weight: "0.4", required: true },
];

function renderCriteriaRows() {
  const container = document.getElementById("criteria-rows");
  container.innerHTML = criteria.map((c, i) => `
    <div class="criteria-row">
      <input type="text" value="${c.name}" placeholder="Skill name"
        onchange="criteria[${i}].name = this.value; renderScoreRows()" />
      <input type="number" value="${c.weight}" step="0.1" min="0" max="1" placeholder="0.0"
        onchange="criteria[${i}].weight = this.value" />
      <select onchange="criteria[${i}].required = this.value === 'true'">
        <option value="true" ${c.required ? "selected" : ""}>Yes</option>
        <option value="false" ${!c.required ? "selected" : ""}>No</option>
      </select>
      <button type="button" class="btn-icon" onclick="removeCriterion(${i})">x</button>
    </div>`).join("");
  renderScoreRows();
}

function renderScoreRows() {
  const container = document.getElementById("score-rows");
  container.innerHTML = criteria.map((c, i) => `
    <div class="score-row">
      <label>${c.name || "Skill " + (i + 1)}</label>
      <input type="number" id="score-${i}" min="0" max="10" step="0.1" value="0" />
    </div>`).join("");
}

document.getElementById("add-criterion").addEventListener("click", () => {
  criteria.push({ name: "", weight: "0.1", required: false });
  renderCriteriaRows();
});

function removeCriterion(i) {
  criteria.splice(i, 1);
  renderCriteriaRows();
}

document.getElementById("assess-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errEl = document.getElementById("assess-error");
  errEl.style.display = "none";

  const scores = {};
  criteria.forEach((c, i) => {
    if (c.name) scores[c.name] = parseFloat(document.getElementById(`score-${i}`).value) || 0;
  });

  const body = {
    candidate_id: assessCandidateId,
    criteria: criteria.map((c) => ({
      name: c.name,
      weight: parseFloat(c.weight),
      required: c.required,
    })),
    scores,
  };

  try {
    const result = await api.post("/candidates/assess", body);
    document.getElementById("assess-form").style.display = "none";
    const resultDiv = document.getElementById("assess-result");
    document.getElementById("assess-total").textContent = result.total_score.toFixed(2);
    document.getElementById("assess-breakdown").innerHTML = Object.entries(result.breakdown)
      .map(([skill, score]) => `<tr><td>${skill}</td><td>${score}</td></tr>`).join("");
    resultDiv.style.display = "block";
    criteria = [
      { name: "python", weight: "0.6", required: true },
      { name: "sql",    weight: "0.4", required: true },
    ];
    loadCandidates();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.style.display = "block";
  }
});

// ── Hire Decision Modal ────────────────────────────────────────────────────────
const decideModal = document.getElementById("decide-modal");
const decideBiasModal = document.getElementById("decide-bias-modal");
let decideCandidateId = null;
let _pendingDecision = null;
let _pendingJustification = null;

function openDecideModal(candidateId) {
  decideCandidateId = candidateId;
  document.getElementById("decide-candidate-id").textContent = candidateId;
  document.getElementById("decide-form").reset();
  document.getElementById("decide-result").style.display = "none";
  document.getElementById("decide-error").style.display = "none";
  document.getElementById("decide-form").style.display = "block";
  const submitBtn = document.getElementById("decide-submit");
  submitBtn.disabled = false;
  submitBtn.textContent = "Submit Decision";
  decideModal.classList.add("open");
}

document.getElementById("decide-cancel").addEventListener("click", () => decideModal.classList.remove("open"));
decideModal.addEventListener("click", (e) => { if (e.target === decideModal) decideModal.classList.remove("open"); });

document.getElementById("decide-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const errEl = document.getElementById("decide-error");
  const submitBtn = document.getElementById("decide-submit");
  errEl.style.display = "none";

  const justification = form.justification.value.trim();
  const decision = form.decision.value;

  if (!decision) {
    errEl.textContent = "Please select a decision (Hired or Rejected).";
    errEl.style.display = "block";
    return;
  }
  if (!justification) {
    errEl.textContent = "A written justification is required before submitting.";
    errEl.style.display = "block";
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "Checking...";

  try {
    const biasResult = await api.post("/candidates/check-justification-bias", { text: justification });
    submitBtn.disabled = false;
    submitBtn.textContent = "Submit Decision";
    if (biasResult.flagged) {
      _pendingDecision = decision;
      _pendingJustification = justification;
      _openDecideBiasModal(biasResult.flagged_phrases);
    } else {
      await _recordDecision(decideCandidateId, decision, justification);
    }
  } catch (err) {
    errEl.textContent = err.message;
    errEl.style.display = "block";
    submitBtn.disabled = false;
    submitBtn.textContent = "Submit Decision";
  }
});

function _openDecideBiasModal(flaggedPhrases) {
  const list = document.getElementById("decide-bias-modal-list");
  list.innerHTML = flaggedPhrases.map((fp) =>
    `<li><strong>"${fp.phrase}"</strong> — ${fp.reason}. <em>${fp.suggestion}</em></li>`
  ).join("");
  decideBiasModal.classList.add("open");
}

document.getElementById("decide-bias-edit-btn").addEventListener("click", () => {
  // Just dismiss the popup — the Hire Decision form underneath is untouched,
  // so the user can revise the justification text and submit again.
  decideBiasModal.classList.remove("open");
  _pendingDecision = null;
  _pendingJustification = null;
});

document.getElementById("decide-bias-confirm-btn").addEventListener("click", async () => {
  const confirmBtn = document.getElementById("decide-bias-confirm-btn");
  confirmBtn.disabled = true;
  confirmBtn.textContent = "Submitting...";
  decideBiasModal.classList.remove("open");
  await _recordDecision(decideCandidateId, _pendingDecision, _pendingJustification);
  confirmBtn.disabled = false;
  confirmBtn.textContent = "Submit Anyway";
});

decideBiasModal.addEventListener("click", (e) => { if (e.target === decideBiasModal) decideBiasModal.classList.remove("open"); });

async function _recordDecision(candidateId, decision, justification) {
  const errEl = document.getElementById("decide-error");
  try {
    const result = await api.post(`/candidates/${candidateId}/decide`, { decision, justification });
    document.getElementById("decide-form").style.display = "none";
    const resultDiv = document.getElementById("decide-result");
    const decisionLabel = result.decision === "hired"
      ? `<span class="badge badge-green">Hired</span>`
      : `<span class="badge badge-red">Rejected</span>`;

    let biasHtml = "";
    if (result.bias_check.flagged) {
      biasHtml = `
        <div class="ai-banner" style="margin-top:1rem">
          <div class="ai-label">Bias Noted in Final Justification</div>
          The following phrases were flagged and recorded for audit purposes.
          <ul style="margin-top:0.5rem;padding-left:1.2rem">
            ${result.bias_check.flagged_phrases.map((fp) =>
              `<li><strong>"${fp.phrase}"</strong> — ${fp.reason}. <em>${fp.suggestion}</em></li>`
            ).join("")}
          </ul>
        </div>`;
    } else {
      biasHtml = `<p style="color:#22c55e;margin-top:0.75rem;font-size:0.85rem">No biased language detected in justification.</p>`;
    }

    resultDiv.innerHTML = `
      <p>Decision recorded: ${decisionLabel}</p>
      ${biasHtml}
      <div class="modal-actions" style="margin-top:1rem">
        <button class="btn btn-outline" onclick="decideModal.classList.remove('open');loadCandidates()">Close</button>
      </div>`;
    resultDiv.style.display = "block";
    _pendingDecision = null;
    _pendingJustification = null;
    loadCandidates();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.style.display = "block";
    const submitBtn = document.getElementById("decide-submit");
    if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = "Submit Decision"; }
  }
}

// ── Panel Assignment ───────────────────────────────────────────────────────────
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
  } catch (e) {
    errorEl.textContent = `Invalid JSON — ${e.message}. Common causes: trailing commas before ] or }, single quotes instead of double quotes.`;
    errorEl.style.display = "block";
    return;
  }
  const body = {
    interviewer_pool: pool,
    panel_size: parseInt(form.panel_size.value, 10) || 3,
    mandatory_ids: form.mandatory_ids.value.split(",").map((s) => s.trim()).filter(Boolean),
  };
  try {
    const result = await api.post("/interviews/assign-panel", body);
    const approvedBadge = result.approved
      ? `<span class="badge badge-green">Approved</span>`
      : `<span class="badge badge-red">Needs Review</span>`;
    resultDiv.innerHTML = `
      <div class="card" style="margin-top:1.25rem">
        <div class="card-title">Suggested Panel - ${approvedBadge}</div>
        ${!result.approved ? `<p style="color:#ef4444;margin-bottom:0.75rem">${result.rejection_reason}</p>` : ""}
        <table>
          <thead><tr><th>Name</th><th>Department</th><th>Gender</th><th>Seniority</th></tr></thead>
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

// ── Initial load ───────────────────────────────────────────────────────────────
loadPostings();
