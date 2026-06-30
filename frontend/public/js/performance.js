// performance.js — client-side logic for the Performance page

// ── Tab switching ──────────────────────────────────────────────────────────────
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
  });
});

function _labelizeCriterion(key) {
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

let _rubricCriteria = [];
let _scoreMin = 1;
let _scoreMax = 5;

async function loadRubric() {
  try {
    const rubric = await api.get("/performance/reviews/rubric");
    _rubricCriteria = rubric.criteria;
    _scoreMin = rubric.min_score;
    _scoreMax = rubric.max_score;
  } catch (e) {
    document.getElementById("review-rubric-rows").innerHTML =
      `<p style="color:#ef4444;font-size:0.85rem">Could not load rubric: ${e.message}</p>`;
  }
}

function renderRubricRows() {
  const container = document.getElementById("review-rubric-rows");
  container.innerHTML = _rubricCriteria.map((c) => `
    <div class="rubric-row" data-criterion="${c.key}">
      <div class="rubric-row-head">
        <label for="review-score-${c.key}">${_labelizeCriterion(c.key)}<span class="rubric-desc">${c.description}</span></label>
        <input type="number" id="review-score-${c.key}" min="${_scoreMin}" max="${_scoreMax}" step="1" required />
      </div>
      <textarea id="review-comments-${c.key}" placeholder="Optional supporting comments for ${_labelizeCriterion(c.key).toLowerCase()}..."></textarea>
    </div>`).join("");
}

// ── Reviews list ─────────────────────────────────────────────────────────────────
let _reviewsCache = [];

function _flaggedCriteriaCount(review) {
  return Object.values(review.bias_checks || {}).filter((bc) => bc.flagged).length;
}

async function loadReviews() {
  const tbody = document.getElementById("reviews-tbody");
  try {
    const data = await api.get("/performance/reviews");
    _reviewsCache = data;
    if (data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:#6b7280">No reviews submitted yet. Write the first one.</td></tr>`;
      return;
    }
    tbody.innerHTML = data.map((r, i) => {
      const flagCount = _flaggedCriteriaCount(r);
      const biasBadge = flagCount > 0
        ? `<span class="badge badge-red">&#9888; ${flagCount} flag(s)</span>`
        : `<span class="badge badge-green">Clean</span>`;
      return `<tr>
        <td>${r.employee_id}</td>
        <td>${r.reviewer_id}</td>
        <td>${r.score.average.toFixed(2)} / 5</td>
        <td>${biasBadge}</td>
        <td><button class="btn btn-outline" style="font-size:0.78rem;padding:0.25rem 0.6rem" onclick="openReviewDetail(${i})">View</button></td>
      </tr>`;
    }).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:#ef4444">${e.message}</td></tr>`;
  }
}

// ── New Review / Review Detail modal ──────────────────────────────────────────
const reviewModal = document.getElementById("review-modal");
const reviewForm = document.getElementById("review-form");
const reviewBiasModal = document.getElementById("review-bias-modal");
let _pendingReviewBody = null;

function _resetReviewModal() {
  reviewForm.reset();
  document.getElementById("review-modal-title").textContent = "Write Performance Review";
  document.getElementById("review-form-error").style.display = "none";
  document.getElementById("review-result").style.display = "none";
  reviewForm.style.display = "block";
  const submitBtn = document.getElementById("review-modal-submit");
  submitBtn.disabled = false;
  submitBtn.textContent = "Submit Review";
  renderRubricRows();
}

document.getElementById("new-review-btn").addEventListener("click", () => {
  _resetReviewModal();
  reviewModal.classList.add("open");
});

document.getElementById("review-modal-cancel").addEventListener("click", () => reviewModal.classList.remove("open"));
reviewModal.addEventListener("click", (e) => { if (e.target === reviewModal) reviewModal.classList.remove("open"); });

function _renderReviewResult(review) {
  document.getElementById("review-result-average").textContent = review.score.average.toFixed(2);
  document.getElementById("review-result-breakdown").innerHTML = Object.entries(review.score.per_criterion)
    .map(([criterion, score]) => `<tr><td>${_labelizeCriterion(criterion)}</td><td>${score}</td></tr>`).join("");

  const flagged = Object.entries(review.bias_checks || {}).filter(([, bc]) => bc.flagged);
  const biasDiv = document.getElementById("review-result-bias");
  if (flagged.length === 0) {
    biasDiv.innerHTML = `<p style="color:#22c55e;font-size:0.85rem">No biased language detected in any comment.</p>`;
  } else {
    biasDiv.innerHTML = `
      <div class="ai-banner">
        <div class="ai-label">Bias Notes - Advisory Only</div>
        <ul style="margin-top:0.5rem;padding-left:1.2rem">
          ${flagged.map(([criterion, bc]) => bc.flagged_phrases.map((fp) =>
            `<li><strong>${_labelizeCriterion(criterion)}:</strong> "${fp.phrase}" — ${fp.reason}. <em>${fp.suggestion}</em></li>`
          ).join("")).join("")}
        </ul>
      </div>`;
  }

  document.getElementById("review-result").style.display = "block";
}

function openReviewDetail(index) {
  const review = _reviewsCache[index];
  if (!review) return;
  document.getElementById("review-modal-title").textContent = "Review Details";
  document.getElementById("review-form-error").style.display = "none";
  reviewForm.style.display = "none";
  _renderReviewResult(review);
  reviewModal.classList.add("open");
}

document.getElementById("review-result-close").addEventListener("click", () => reviewModal.classList.remove("open"));

reviewForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const errEl = document.getElementById("review-form-error");
  const submitBtn = document.getElementById("review-modal-submit");
  errEl.style.display = "none";

  const employeeId = document.getElementById("review-employee-id").value.trim();
  const reviewerId = document.getElementById("review-reviewer-id").value.trim();
  if (!employeeId || !reviewerId) {
    errEl.textContent = "Employee ID and Reviewer ID are both required.";
    errEl.style.display = "block";
    return;
  }

  const criteria = [];
  for (const c of _rubricCriteria) {
    const scoreInput = document.getElementById(`review-score-${c.key}`);
    const comments = document.getElementById(`review-comments-${c.key}`).value.trim();
    const score = parseInt(scoreInput.value, 10);
    if (Number.isNaN(score) || score < _scoreMin || score > _scoreMax) {
      errEl.textContent = `Please score "${_labelizeCriterion(c.key)}" between ${_scoreMin} and ${_scoreMax}.`;
      errEl.style.display = "block";
      return;
    }
    criteria.push({ criterion: c.key, score, comments });
  }

  const body = { employee_id: employeeId, reviewer_id: reviewerId, criteria };

  submitBtn.disabled = true;
  submitBtn.textContent = "Checking...";

  try {
    const checks = await Promise.all(
      criteria
        .filter((c) => c.comments)
        .map((c) => api.post("/performance/reviews/check-bias", { text: c.comments })
          .then((result) => ({ criterion: c.criterion, result })))
    );
    submitBtn.disabled = false;
    submitBtn.textContent = "Submit Review";

    const flagged = checks.filter((c) => c.result.flagged);
    if (flagged.length > 0) {
      _pendingReviewBody = body;
      _openReviewBiasModal(flagged);
    } else {
      await _submitReview(body);
    }
  } catch (err) {
    errEl.textContent = err.message;
    errEl.style.display = "block";
    submitBtn.disabled = false;
    submitBtn.textContent = "Submit Review";
  }
});

function _openReviewBiasModal(flagged) {
  const list = document.getElementById("review-bias-modal-list");
  list.innerHTML = flagged.map(({ criterion, result }) => result.flagged_phrases.map((fp) =>
    `<li><strong>${_labelizeCriterion(criterion)}:</strong> "${fp.phrase}" — ${fp.reason}. <em>${fp.suggestion}</em></li>`
  ).join("")).join("");
  reviewBiasModal.classList.add("open");
}

document.getElementById("review-bias-edit-btn").addEventListener("click", () => {
  // Dismiss the popup only -- the review form underneath is untouched, so
  // the reviewer can revise their comments and submit again.
  reviewBiasModal.classList.remove("open");
  _pendingReviewBody = null;
});

document.getElementById("review-bias-confirm-btn").addEventListener("click", async () => {
  const confirmBtn = document.getElementById("review-bias-confirm-btn");
  confirmBtn.disabled = true;
  confirmBtn.textContent = "Submitting...";
  reviewBiasModal.classList.remove("open");
  await _submitReview(_pendingReviewBody);
  confirmBtn.disabled = false;
  confirmBtn.textContent = "Submit Anyway";
});

reviewBiasModal.addEventListener("click", (e) => { if (e.target === reviewBiasModal) reviewBiasModal.classList.remove("open"); });

async function _submitReview(body) {
  const errEl = document.getElementById("review-form-error");
  const submitBtn = document.getElementById("review-modal-submit");
  try {
    const result = await api.post("/performance/reviews", body);
    reviewForm.style.display = "none";
    document.getElementById("review-modal-title").textContent = "Review Submitted";
    _renderReviewResult(result);
    _pendingReviewBody = null;
    loadReviews();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.style.display = "block";
    submitBtn.disabled = false;
    submitBtn.textContent = "Submit Review";
  }
}

// ── 360 Feedback: submit ──────────────────────────────────────────────────────
document.getElementById("feedback-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const submitBtn = document.getElementById("feedback-submit-btn");
  const errEl = document.getElementById("feedback-form-error");
  const successEl = document.getElementById("feedback-form-success");
  errEl.style.display = "none";
  successEl.style.display = "none";

  const body = {
    employee_id: form.employee_id.value.trim(),
    rater_id: form.rater_id.value.trim(),
    comments: form.comments.value.trim(),
  };

  submitBtn.disabled = true;
  submitBtn.textContent = "Submitting...";

  try {
    await api.post("/performance/feedback", body);
    form.reset();
    successEl.style.display = "block";
  } catch (err) {
    errEl.textContent = err.message;
    errEl.style.display = "block";
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Submit Feedback";
  }
});

// ── 360 Feedback: anonymised aggregated view ──────────────────────────────────
document.getElementById("feedback-lookup-btn").addEventListener("click", async () => {
  const errEl = document.getElementById("feedback-lookup-error");
  const resultDiv = document.getElementById("feedback-lookup-result");
  const employeeId = document.getElementById("feedback-lookup-id").value.trim();
  errEl.style.display = "none";
  resultDiv.style.display = "none";

  if (!employeeId) {
    errEl.textContent = "Enter an Employee ID to look up.";
    errEl.style.display = "block";
    return;
  }

  try {
    const aggregated = await api.get(`/performance/feedback/${encodeURIComponent(employeeId)}`);
    document.getElementById("feedback-lookup-count").textContent = aggregated.count;
    const list = document.getElementById("feedback-lookup-list");
    list.innerHTML = aggregated.comments.length
      ? aggregated.comments.map((c) => `<li>${c}</li>`).join("")
      : `<li style="color:#6b7280;list-style:none;margin-left:-1.2rem">No feedback submitted yet.</li>`;
    resultDiv.style.display = "block";
  } catch (err) {
    errEl.textContent = err.message;
    errEl.style.display = "block";
  }
});

// ── Initial load ───────────────────────────────────────────────────────────────
loadReviews();
loadRubric();
