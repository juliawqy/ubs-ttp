// training.js — client-side logic for the Training page

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
async function loadModules() {
  const tbody = document.getElementById("modules-tbody");
  try {
    const data = await api.get("/training/modules");
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
        <td><button class="btn btn-outline" style="font-size:0.8rem;padding:0.3rem 0.7rem" onclick="sendReminder(${m.id})">Remind</button></td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:#ef4444">${e.message}</td></tr>`;
  }
}

async function sendReminder(moduleId) {
  await api.post(`/training/modules/${moduleId}/remind`, {});
  alert("Reminder sent.");
}

// ─── IAT ──────────────────────────────────────────────────────────────────────
document.getElementById("start-iat-btn").addEventListener("click", async () => {
  // Opens a sandboxed IAT session — results are private
  alert("Launching private IAT session... (sandbox opens here)");
  // TODO: open IAT iframe or navigate to sandboxed route
});

// ─── Career Mapping ────────────────────────────────────────────────────────────
async function loadCareerPaths() {
  const tbody = document.getElementById("career-tbody");
  try {
    const data = await api.get("/training/career-mapping");
    tbody.innerHTML = data.map((e) => `
      <tr>
        <td>${e.employee_name}</td>
        <td>${e.current_role}</td>
        <td>${e.next_milestone}</td>
        <td>${e.target_date}</td>
        <td><button class="btn btn-outline" style="font-size:0.8rem;padding:0.3rem 0.7rem">Edit</button></td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:#ef4444">${e.message}</td></tr>`;
  }
}

loadModules();
