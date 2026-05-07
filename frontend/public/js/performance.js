// performance.js — client-side logic for the Performance Reviews page

document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => {
      b.classList.remove("btn-primary"); b.classList.add("btn-outline");
    });
    btn.classList.add("btn-primary"); btn.classList.remove("btn-outline");
    ["reviews", "feedback"].forEach((id) => {
      document.getElementById(`tab-${id}`).style.display = "none";
    });
    document.getElementById(`tab-${btn.dataset.tab}`).style.display = "block";
    if (btn.dataset.tab === "reviews") loadReviews();
    if (btn.dataset.tab === "feedback") loadFeedback();
  });
});

let activeEmployeeId = null;

// ─── Reviews ──────────────────────────────────────────────────────────────────
async function loadReviews() {
  const tbody = document.getElementById("reviews-tbody");
  try {
    const data = await api.get("/performance/reviews");
    tbody.innerHTML = data.map((r) => `
      <tr>
        <td>${r.employee_name}</td>
        <td>${r.role}</td>
        <td><span class="badge ${r.status === "Submitted" ? "badge-green" : "badge-yellow"}">${r.status}</span></td>
        <td>${r.bias_score != null ? r.bias_score + "/10" : "—"}</td>
        <td>
          <button class="btn btn-primary" style="font-size:0.8rem;padding:0.3rem 0.7rem"
            onclick="openEditor(${r.employee_id})">
            ${r.status === "Pending" ? "Write Review" : "Edit"}
          </button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:#ef4444">${e.message}</td></tr>`;
  }
}

function openEditor(employeeId) {
  activeEmployeeId = employeeId;
  document.getElementById("review-editor").style.display = "block";
  document.getElementById("ai-feedback").style.display = "none";
  document.getElementById("review-score").value = "";
  document.getElementById("review-text").value = "";
}

document.getElementById("cancel-review-btn").addEventListener("click", () => {
  document.getElementById("review-editor").style.display = "none";
});

// AI bias check
document.getElementById("check-bias-btn").addEventListener("click", async () => {
  const text = document.getElementById("review-text").value.trim();
  if (!text) { alert("Write your review first."); return; }
  try {
    const result = await api.post("/ai-assistant/assistant/check-bias", { text });
    const banner = document.getElementById("ai-feedback");
    document.getElementById("ai-feedback-text").innerHTML =
      result.flagged
        ? `<strong>Flagged phrases:</strong> ${result.flagged_phrases.join(", ")}<br><em>Suggestion: ${result.suggestion}</em>`
        : "No bias detected. Your review looks good to submit.";
    banner.style.display = "block";
  } catch (e) {
    alert("Bias check failed: " + e.message);
  }
});

document.getElementById("submit-review-btn").addEventListener("click", async () => {
  const score = document.getElementById("review-score").value;
  const text = document.getElementById("review-text").value.trim();
  if (!score || !text) { alert("Please fill in both score and justification."); return; }
  await api.post("/performance/reviews", { employee_id: activeEmployeeId, score: +score, text });
  document.getElementById("review-editor").style.display = "none";
  loadReviews();
});

// ─── Feedback ─────────────────────────────────────────────────────────────────
async function loadFeedback() {
  const tbody = document.getElementById("feedback-tbody");
  try {
    const data = await api.get("/performance/feedback");
    tbody.innerHTML = data.map((f) => `
      <tr>
        <td>Anonymous</td>
        <td>${f.submitted_date}</td>
        <td>${f.theme}</td>
        <td><span class="badge ${f.sentiment === "Positive" ? "badge-green" : f.sentiment === "Negative" ? "badge-red" : "badge-yellow"}">${f.sentiment}</span></td>
        <td><button class="btn btn-outline" style="font-size:0.8rem;padding:0.3rem 0.7rem">View</button></td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:#ef4444">${e.message}</td></tr>`;
  }
}

loadReviews();
