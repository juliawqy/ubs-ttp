// training.js — client-side logic for the Training page

// ── Tab switching ──────────────────────────────────────────────────────────────
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => {
      b.classList.remove("btn-primary"); b.classList.add("btn-outline");
    });
    btn.classList.add("btn-primary"); btn.classList.remove("btn-outline");
    ["modules", "iat", "career"].forEach((id) => {
      document.getElementById(`tab-${id}`).style.display = "none";
    });
    document.getElementById(`tab-${btn.dataset.tab}`).style.display = "block";
    if (btn.dataset.tab === "modules") loadModules();
    if (btn.dataset.tab === "career") loadCareerPaths();
  });
});

// ─── Modules ──────────────────────────────────────────────────────────────────
let _modulesCache = [];

async function loadModules() {
  const tbody = document.getElementById("modules-tbody");
  try {
    const data = await api.get("/training/modules");
    _modulesCache = data;
    if (data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:#6b7280">No modules assigned yet. Create the first one.</td></tr>`;
      return;
    }
    tbody.innerHTML = data.map((m) => `
      <tr>
        <td>${m.title}</td>
        <td>${m.assigned_to}</td>
        <td>${m.due_date}</td>
        <td>
          <div style="display:flex;align-items:center;gap:0.5rem">
            <div style="flex:1;background:#e5e7eb;border-radius:999px;height:6px">
              <div style="width:${m.completion_pct}%;background:#e00b1c;border-radius:999px;height:6px"></div>
            </div>
            <span style="font-size:0.8rem">${m.completion_pct}%</span>
          </div>
        </td>
        <td style="white-space:nowrap">
          <button class="btn btn-outline" style="font-size:0.78rem;padding:0.25rem 0.6rem;margin-right:0.35rem" onclick="openEditModuleModal(${m.id})">Edit</button>
          <button class="btn btn-outline" style="font-size:0.78rem;padding:0.25rem 0.6rem;margin-right:0.35rem" onclick="sendReminder(${m.id})">Remind</button>
          <button class="btn btn-outline" style="font-size:0.78rem;padding:0.25rem 0.6rem;color:#ef4444" onclick="deleteModule(${m.id})">Delete</button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:#ef4444">${e.message}</td></tr>`;
  }
}

async function sendReminder(moduleId) {
  try {
    await api.post(`/training/modules/${moduleId}/remind`, {});
    alert("Reminder sent.");
    loadModules();
  } catch (e) {
    alert(`Could not send reminder: ${e.message}`);
  }
}

async function deleteModule(moduleId) {
  if (!confirm("Delete this training module?")) return;
  try {
    await api.delete(`/training/modules/${moduleId}`);
    loadModules();
  } catch (e) {
    alert(`Could not delete module: ${e.message}`);
  }
}

const moduleModal = document.getElementById("module-modal");
const moduleForm = document.getElementById("module-form");
let editingModuleId = null;

function _resetModuleModal() {
  editingModuleId = null;
  moduleForm.reset();
  document.getElementById("module-progress-row").style.display = "none";
  document.getElementById("module-form-error").style.display = "none";
  document.getElementById("module-modal-title").textContent = "New Training Module";
  const submitBtn = document.getElementById("module-modal-submit");
  submitBtn.disabled = false;
  submitBtn.textContent = "Create Module";
}

document.getElementById("new-module-btn").addEventListener("click", () => {
  _resetModuleModal();
  moduleModal.classList.add("open");
});

function openEditModuleModal(moduleId) {
  const m = _modulesCache.find((mod) => mod.id === moduleId);
  if (!m) return;
  _resetModuleModal();
  editingModuleId = m.id;
  document.getElementById("module-modal-title").textContent = "Edit Training Module";
  moduleForm.title.value = m.title;
  moduleForm.assigned_to.value = m.assigned_to;
  moduleForm.due_date.value = m.due_date;
  moduleForm.description.value = m.description || "";
  document.getElementById("module-progress-row").style.display = "block";
  moduleForm.completion_pct.value = m.completion_pct;
  document.getElementById("module-modal-submit").textContent = "Save Changes";
  moduleModal.classList.add("open");
}

document.getElementById("module-modal-cancel").addEventListener("click", () => moduleModal.classList.remove("open"));
moduleModal.addEventListener("click", (e) => { if (e.target === moduleModal) moduleModal.classList.remove("open"); });

moduleForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const submitBtn = document.getElementById("module-modal-submit");
  const errEl = document.getElementById("module-form-error");
  const isEdit = editingModuleId !== null;
  const body = {
    title: form.title.value.trim(),
    assigned_to: form.assigned_to.value.trim(),
    due_date: form.due_date.value,
    description: form.description.value.trim(),
  };

  submitBtn.disabled = true;
  submitBtn.textContent = isEdit ? "Saving..." : "Submitting...";
  errEl.style.display = "none";

  try {
    if (isEdit) {
      await api.put(`/training/modules/${editingModuleId}`, body);
      const original = _modulesCache.find((m) => m.id === editingModuleId);
      const newPct = parseFloat(form.completion_pct.value);
      if (!Number.isNaN(newPct) && original && newPct !== original.completion_pct) {
        await api.patch(`/training/modules/${editingModuleId}/progress`, { completion_pct: newPct });
      }
    } else {
      await api.post("/training/modules", body);
    }
    moduleModal.classList.remove("open");
    loadModules();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.style.display = "block";
    submitBtn.disabled = false;
    submitBtn.textContent = isEdit ? "Save Changes" : "Create Module";
  }
});

// ─── IAT ──────────────────────────────────────────────────────────────────────
// Category content (poles + stimulus words) is fetched from
// GET /training/iat/categories rather than hardcoded here, so a real
// company content source can be plugged in on the backend (swap
// IATCategoryCatalog for a real provider) without any frontend changes.
// Today that endpoint returns a stubbed, value-neutral set of categories.
let _iatCategories = [];

let _iatSessionId = null;
let _iatEmployeeId = null;
let _iatTrials = [];
let _iatTrialIndex = 0;
let _iatTrialStart = null;

function _buildIatTrials() {
  const trials = [];
  _iatCategories.forEach((cat) => {
    (cat.stimuli || []).forEach((word) => {
      trials.push({ categoryId: cat.id, label: cat.label, poleA: cat.pole_a, poleB: cat.pole_b, stimulus: word });
    });
  });
  for (let i = trials.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [trials[i], trials[j]] = [trials[j], trials[i]];
  }
  return trials;
}

function _resetIatUi() {
  document.getElementById("iat-intro").style.display = "block";
  document.getElementById("iat-trial").style.display = "none";
  document.getElementById("iat-result").style.display = "none";
  document.getElementById("iat-employee-id").value = "";
  const startBtn = document.getElementById("start-iat-btn");
  startBtn.disabled = false;
  startBtn.textContent = "Start Private Session";
}

document.getElementById("start-iat-btn").addEventListener("click", async () => {
  const startErrEl = document.getElementById("iat-start-error");
  const errEl = document.getElementById("iat-error");
  const startBtn = document.getElementById("start-iat-btn");
  const employeeId = document.getElementById("iat-employee-id").value.trim();
  startErrEl.style.display = "none";
  errEl.style.display = "none";

  if (!employeeId) {
    startErrEl.textContent = "Enter your Employee ID to start a private session.";
    startErrEl.style.display = "block";
    return;
  }

  startBtn.disabled = true;
  startBtn.textContent = "Starting...";
  try {
    _iatCategories = await api.get("/training/iat/categories");
    if (!_iatCategories.length) {
      throw new Error("No test categories are available right now.");
    }
    const session = await api.post("/training/iat/sessions", { employee_id: employeeId });
    _iatSessionId = session.id;
    _iatEmployeeId = employeeId;
    _iatTrials = _buildIatTrials();
    _iatTrialIndex = 0;
    document.getElementById("iat-intro").style.display = "none";
    document.getElementById("iat-trial").style.display = "block";
    _showIatTrial();
  } catch (err) {
    startErrEl.textContent = err.message;
    startErrEl.style.display = "block";
    startBtn.disabled = false;
    startBtn.textContent = "Start Private Session";
  }
});

function _showIatTrial() {
  const trial = _iatTrials[_iatTrialIndex];
  document.getElementById("iat-progress-label").textContent =
    `Question ${_iatTrialIndex + 1} of ${_iatTrials.length}`;
  document.getElementById("iat-category-label").textContent =
    `${trial.label} — classify this word as quickly as feels natural`;
  document.getElementById("iat-stimulus").textContent = trial.stimulus;
  const poleABtn = document.getElementById("iat-pole-a-btn");
  const poleBBtn = document.getElementById("iat-pole-b-btn");
  poleABtn.textContent = trial.poleA;
  poleBBtn.textContent = trial.poleB;
  poleABtn.disabled = false;
  poleBBtn.disabled = false;
  _iatTrialStart = performance.now();
}

document.getElementById("iat-pole-a-btn").addEventListener("click", () => _submitIatTrial("a"));
document.getElementById("iat-pole-b-btn").addEventListener("click", () => _submitIatTrial("b"));

async function _submitIatTrial(pole) {
  const trial = _iatTrials[_iatTrialIndex];
  const responseTimeMs = performance.now() - _iatTrialStart;
  const poleABtn = document.getElementById("iat-pole-a-btn");
  const poleBBtn = document.getElementById("iat-pole-b-btn");
  poleABtn.disabled = true;
  poleBBtn.disabled = true;

  try {
    await api.post(`/training/iat/sessions/${_iatSessionId}/responses`, {
      category: trial.categoryId,
      selected_pole: pole,
      response_time_ms: responseTimeMs,
    });
    _iatTrialIndex += 1;
    if (_iatTrialIndex < _iatTrials.length) {
      _showIatTrial();
    } else {
      await _finishIatSession();
    }
  } catch (err) {
    const errEl = document.getElementById("iat-error");
    errEl.textContent = `Could not record your response: ${err.message}`;
    errEl.style.display = "block";
    poleABtn.disabled = false;
    poleBBtn.disabled = false;
  }
}

async function _finishIatSession() {
  document.getElementById("iat-trial").style.display = "none";
  try {
    await api.post(`/training/iat/sessions/${_iatSessionId}/complete`, {});
    const result = await api.get(
      `/training/iat/sessions/${_iatSessionId}/result?employee_id=${encodeURIComponent(_iatEmployeeId)}`
    );
    _renderIatResult(result);
  } catch (err) {
    const errEl = document.getElementById("iat-error");
    errEl.textContent = `Could not load your results: ${err.message}`;
    errEl.style.display = "block";
    _resetIatUi();
  }
}

function _renderIatResult(result) {
  const tbody = document.getElementById("iat-result-tbody");
  tbody.innerHTML = Object.entries(result.category_scores).map(([categoryId, score]) => {
    const cat = _iatCategories.find((c) => c.id === categoryId);
    const label = cat ? cat.label : categoryId;
    const lean = cat ? (score >= 0 ? cat.pole_a : cat.pole_b) : "—";
    return `<tr><td>${label}</td><td>${Math.abs(score).toFixed(0)} ms faster toward "${lean}"</td></tr>`;
  }).join("");
  document.getElementById("iat-result").style.display = "block";
}

document.getElementById("iat-retake-btn").addEventListener("click", () => {
  _iatSessionId = null;
  _iatEmployeeId = null;
  document.getElementById("iat-error").style.display = "none";
  _resetIatUi();
});

// ─── Career Mapping ────────────────────────────────────────────────────────────
let _careerCache = [];

async function loadCareerPaths() {
  const tbody = document.getElementById("career-tbody");
  try {
    const data = await api.get("/training/career-mapping");
    _careerCache = data;
    if (data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:#6b7280">No career paths mapped yet. Create the first one.</td></tr>`;
      return;
    }
    tbody.innerHTML = data.map((entry) => {
      const skills = (entry.recommended_skills || []).map((s) => `<span class="skill-tag">${s}</span>`).join("") || "—";
      return `<tr>
        <td>${entry.employee_name}</td>
        <td>${entry.current_role}</td>
        <td>${entry.next_milestone}</td>
        <td>${entry.target_date}</td>
        <td>${skills}</td>
        <td style="white-space:nowrap">
          <button class="btn btn-outline" style="font-size:0.78rem;padding:0.25rem 0.6rem;margin-right:0.35rem" onclick="openEditCareerModal(${entry.id})">Edit</button>
          <button class="btn btn-outline" style="font-size:0.78rem;padding:0.25rem 0.6rem;color:#ef4444" onclick="deleteCareerEntry(${entry.id})">Delete</button>
        </td>
      </tr>`;
    }).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6" style="color:#ef4444">${e.message}</td></tr>`;
  }
}

async function deleteCareerEntry(entryId) {
  if (!confirm("Delete this career path entry?")) return;
  try {
    await api.delete(`/training/career-mapping/${entryId}`);
    loadCareerPaths();
  } catch (e) {
    alert(`Could not delete entry: ${e.message}`);
  }
}

const careerModal = document.getElementById("career-modal");
const careerForm = document.getElementById("career-form");
let editingCareerId = null;

function _resetCareerModal() {
  editingCareerId = null;
  careerForm.reset();
  document.getElementById("career-form-error").style.display = "none";
  document.getElementById("career-modal-title").textContent = "New Career Path Entry";
  const submitBtn = document.getElementById("career-modal-submit");
  submitBtn.disabled = false;
  submitBtn.textContent = "Create Entry";
}

document.getElementById("new-career-btn").addEventListener("click", () => {
  _resetCareerModal();
  careerModal.classList.add("open");
});

function openEditCareerModal(entryId) {
  const entry = _careerCache.find((e) => e.id === entryId);
  if (!entry) return;
  _resetCareerModal();
  editingCareerId = entry.id;
  document.getElementById("career-modal-title").textContent = "Edit Career Path Entry";
  careerForm.employee_name.value = entry.employee_name;
  careerForm.current_role.value = entry.current_role;
  careerForm.next_milestone.value = entry.next_milestone;
  careerForm.target_date.value = entry.target_date;
  document.getElementById("career-modal-submit").textContent = "Save Changes";
  careerModal.classList.add("open");
}

document.getElementById("career-modal-cancel").addEventListener("click", () => careerModal.classList.remove("open"));
careerModal.addEventListener("click", (e) => { if (e.target === careerModal) careerModal.classList.remove("open"); });

careerForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const submitBtn = document.getElementById("career-modal-submit");
  const errEl = document.getElementById("career-form-error");
  const isEdit = editingCareerId !== null;
  const body = {
    employee_name: form.employee_name.value.trim(),
    current_role: form.current_role.value.trim(),
    next_milestone: form.next_milestone.value.trim(),
    target_date: form.target_date.value,
  };

  submitBtn.disabled = true;
  submitBtn.textContent = isEdit ? "Saving..." : "Submitting...";
  errEl.style.display = "none";

  try {
    if (isEdit) {
      await api.put(`/training/career-mapping/${editingCareerId}`, body);
    } else {
      await api.post("/training/career-mapping", body);
    }
    careerModal.classList.remove("open");
    loadCareerPaths();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.style.display = "block";
    submitBtn.disabled = false;
    submitBtn.textContent = isEdit ? "Save Changes" : "Create Entry";
  }
});

// ── Initial load ───────────────────────────────────────────────────────────────
loadModules();
