// @ts-check
/**
 * E2E tests for the Hiring page.
 * Run: cd frontend && npx playwright test
 *
 * All API calls are stubbed.
 */
import { test, expect } from "@playwright/test";

const MOCK_POSTINGS = [
  {
    id: 1,
    title: "Senior Python Engineer",
    department: "Engineering",
    manager: { id: "mgr-001", name: "Amy Baker", department: "Engineering", email: "amy.baker@ubs.com" },
    status: "pending",
    bias_check: { flagged: false, flagged_phrases: [] },
  },
];

const MOCK_BIASED_RESULT = {
  id: 2,
  title: "Rockstar Python Ninja",
  department: "Engineering",
  manager: { id: "mgr-001", name: "Amy Baker", department: "Engineering", email: "amy.baker@ubs.com" },
  status: "pending",
  bias_check: {
    flagged: true,
    flagged_phrases: [
      { phrase: "rockstar", reason: "Gendered language", suggestion: "Try 'skilled engineer'" },
      { phrase: "ninja", reason: "Exclusionary jargon", suggestion: "Try 'expert'" },
    ],
  },
};

const MOCK_CANDIDATES = [
  { candidate_id: "cand-001", redacted_text: "Experienced software developer with 8 years in Python and distributed systems." },
  { candidate_id: "cand-002", redacted_text: "Data analyst with strong SQL and visualisation background." },
];

const MOCK_PANEL = {
  approved: true,
  rejection_reason: null,
  interviewers: [
    { id: "iv-001", name: "Alice Smith", gender: "Female", department: "Engineering", seniority: "Senior" },
    { id: "iv-002", name: "Bob Jones",  gender: "Male",   department: "HR",          seniority: "Mid"    },
    { id: "iv-003", name: "Carol Lee",  gender: "Female", department: "Finance",     seniority: "Senior" },
  ],
};

// ─── Helpers ───────────────────────────────────────────────────────────────────

async function mockGetPostings(page, data = MOCK_POSTINGS) {
  await page.route("**/api/job-postings", (route) => {
    if (route.request().method() === "GET") {
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(data) });
    } else {
      route.continue();
    }
  });
}

async function mockGetCandidates(page, data = MOCK_CANDIDATES) {
  await page.route("**/api/candidates", (route) => {
    if (route.request().method() === "GET") {
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(data) });
    } else {
      route.continue();
    }
  });
}

// ─── Job Postings tab ─────────────────────────────────────────────────────────

test.describe("Job Postings tab", () => {
  test("shows postings table on load", async ({ page }) => {
    await mockGetPostings(page);
    await page.goto("/hiring");
    await expect(page.getByRole("cell", { name: "Senior Python Engineer" })).toBeVisible();
    await expect(page.getByRole("cell", { name: "Engineering" }).first()).toBeVisible();
    await expect(page.getByRole("cell", { name: "Amy Baker" })).toBeVisible();
  });

  test("shows empty state when no postings", async ({ page }) => {
    await mockGetPostings(page, []);
    await page.goto("/hiring");
    await expect(page.getByText("No postings yet")).toBeVisible();
  });

  test("clean posting shows green Clean badge", async ({ page }) => {
    await mockGetPostings(page);
    await page.goto("/hiring");
    await expect(page.getByText("Clean")).toBeVisible();
  });

  test("biased posting in list shows red flag badge", async ({ page }) => {
    await mockGetPostings(page, [{ ...MOCK_BIASED_RESULT, id: 1 }]);
    await page.goto("/hiring");
    await expect(page.getByText(/flag/)).toBeVisible();
  });
});

// ─── New Posting modal ────────────────────────────────────────────────────────

test.describe("New Posting modal", () => {
  test("modal opens on button click", async ({ page }) => {
    await mockGetPostings(page);
    await page.goto("/hiring");
    await page.getByRole("button", { name: "+ New Posting" }).click();
    await expect(page.getByRole("dialog")).toBeVisible();
  });

  test("modal closes on Cancel", async ({ page }) => {
    await mockGetPostings(page);
    await page.goto("/hiring");
    await page.getByRole("button", { name: "+ New Posting" }).click();
    await page.getByRole("button", { name: "Cancel" }).click();
    await expect(page.getByRole("dialog")).not.toBeVisible();
  });

  test("submitting clean posting closes modal", async ({ page }) => {
    await mockGetPostings(page);
    await page.route("**/api/job-postings", (route) => {
      if (route.request().method() === "POST") {
        route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify(MOCK_POSTINGS[0]) });
      } else {
        route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_POSTINGS) });
      }
    });

    await page.goto("/hiring");
    await page.getByRole("button", { name: "+ New Posting" }).click();

    await page.fill("#post-title", "Senior Python Engineer");
    await page.fill("#post-description", "Build scalable APIs for our trading platform.");
    await page.fill("#post-requirements", "Python, SQL, REST APIs");
    await page.fill("#post-department", "Engineering");
    await page.fill("#manager-name", "Amy Baker");
    await page.fill("#manager-id", "mgr-001");
    await page.fill("#manager-dept", "Engineering");
    await page.fill("#manager-email", "amy.baker@ubs.com");

    await page.getByRole("button", { name: "Submit Posting" }).click();
    await expect(page.getByRole("dialog")).not.toBeVisible();
  });

  test("biased posting shows advisory warnings inside modal", async ({ page }) => {
    await mockGetPostings(page);
    await page.route("**/api/job-postings", (route) => {
      if (route.request().method() === "POST") {
        route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify(MOCK_BIASED_RESULT) });
      } else {
        route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([]) });
      }
    });

    await page.goto("/hiring");
    await page.getByRole("button", { name: "+ New Posting" }).click();

    await page.fill("#post-title", "Rockstar Python Ninja");
    await page.fill("#post-description", "We need a rockstar ninja.");
    await page.fill("#post-requirements", "Python");
    await page.fill("#post-department", "Engineering");
    await page.fill("#manager-name", "Amy Baker");
    await page.fill("#manager-id", "mgr-001");
    await page.fill("#manager-dept", "Engineering");
    await page.fill("#manager-email", "amy.baker@ubs.com");

    await page.getByRole("button", { name: "Submit Posting" }).click();

    await expect(page.getByText("Bias Detected")).toBeVisible();
    await expect(page.getByText(/rockstar/)).toBeVisible();
    await expect(page.getByText(/ninja/)).toBeVisible();
    // modal stays open so manager can act on the feedback
    await expect(page.getByRole("dialog")).toBeVisible();
  });

  test("sends correct payload to API", async ({ page }) => {
    await mockGetPostings(page);
    let capturedBody = null;

    await page.route("**/api/job-postings", async (route) => {
      if (route.request().method() === "POST") {
        capturedBody = route.request().postDataJSON();
        await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify(MOCK_POSTINGS[0]) });
      } else {
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_POSTINGS) });
      }
    });

    await page.goto("/hiring");
    await page.getByRole("button", { name: "+ New Posting" }).click();

    await page.fill("#post-title", "Senior Python Engineer");
    await page.fill("#post-description", "Build scalable APIs.");
    await page.fill("#post-requirements", "Python, SQL");
    await page.fill("#post-department", "Engineering");
    await page.fill("#manager-name", "Amy Baker");
    await page.fill("#manager-id", "mgr-001");
    await page.fill("#manager-dept", "Engineering");
    await page.fill("#manager-email", "amy.baker@ubs.com");

    await page.getByRole("button", { name: "Submit Posting" }).click();

    expect(capturedBody.title).toBe("Senior Python Engineer");
    expect(capturedBody.requirements).toEqual(["Python", "SQL"]);
    expect(capturedBody.manager.id).toBe("mgr-001");
    expect(capturedBody.manager.email).toBe("amy.baker@ubs.com");
  });
});

// ─── Candidates tab ───────────────────────────────────────────────────────────

test.describe("Candidates tab", () => {
  test("shows blind profiles on load", async ({ page }) => {
    await mockGetPostings(page);
    await mockGetCandidates(page);
    await page.goto("/hiring");
    await page.getByRole("button", { name: "Candidates" }).click();

    await expect(page.getByText("Candidate #cand-001")).toBeVisible();
    await expect(page.getByText("Candidate #cand-002")).toBeVisible();
  });

  test("shows empty state when no candidates", async ({ page }) => {
    await mockGetPostings(page);
    await mockGetCandidates(page, []);
    await page.goto("/hiring");
    await page.getByRole("button", { name: "Candidates" }).click();

    await expect(page.getByText("No candidates uploaded yet")).toBeVisible();
  });

  test("shows CV upload form", async ({ page }) => {
    await mockGetPostings(page);
    await mockGetCandidates(page);
    await page.goto("/hiring");
    await page.getByRole("button", { name: "Candidates" }).click();

    await expect(page.locator("#cv-file")).toBeVisible();
    await expect(page.getByRole("button", { name: "Upload" })).toBeVisible();
  });
});

// ─── Panel Assignment tab ─────────────────────────────────────────────────────

test.describe("Panel Assignment tab", () => {
  test("shows assignment form", async ({ page }) => {
    await mockGetPostings(page);
    await page.goto("/hiring");
    await page.getByRole("button", { name: "Panel Assignment" }).click();

    await expect(page.locator("#pool_json")).toBeVisible();
    await expect(page.locator("#panel_size")).toBeVisible();
    await expect(page.getByRole("button", { name: "Suggest Panel" })).toBeVisible();
  });

  test("shows suggested panel after submit", async ({ page }) => {
    await mockGetPostings(page);
    await page.route("**/api/interviews/assign-panel", (route) => {
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_PANEL) });
    });

    await page.goto("/hiring");
    await page.getByRole("button", { name: "Panel Assignment" }).click();

    const pool = [
      { id: "iv-001", name: "Alice Smith", gender: "Female", department: "Engineering", seniority: "Senior" },
      { id: "iv-002", name: "Bob Jones",   gender: "Male",   department: "HR",          seniority: "Mid"    },
      { id: "iv-003", name: "Carol Lee",   gender: "Female", department: "Finance",     seniority: "Senior" },
    ];
    await page.fill("#pool_json", JSON.stringify(pool));
    await page.getByRole("button", { name: "Suggest Panel" }).click();

    await expect(page.getByText("Alice Smith")).toBeVisible();
    await expect(page.getByText("Bob Jones")).toBeVisible();
    await expect(page.getByText("Carol Lee")).toBeVisible();
    await expect(page.getByText("Approved")).toBeVisible();
    await expect(page.getByText(/final decision rests with the hiring manager/).first()).toBeVisible();
  });

  test("shows error for invalid JSON", async ({ page }) => {
    await mockGetPostings(page);
    await page.goto("/hiring");
    await page.getByRole("button", { name: "Panel Assignment" }).click();

    await page.fill("#pool_json", "not valid json");
    await page.getByRole("button", { name: "Suggest Panel" }).click();

    await expect(page.getByText("Invalid JSON")).toBeVisible();
  });

  test("shows rejection reason when panel not approved", async ({ page }) => {
    await mockGetPostings(page);
    const rejected = {
      approved: false,
      rejection_reason: "Panel lacks gender diversity.",
      interviewers: [
        { id: "iv-001", name: "Alice Smith", gender: "Female", department: "Engineering", seniority: "Senior" },
      ],
    };
    await page.route("**/api/interviews/assign-panel", (route) => {
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(rejected) });
    });

    await page.goto("/hiring");
    await page.getByRole("button", { name: "Panel Assignment" }).click();

    await page.fill("#pool_json", JSON.stringify([{ id: "iv-001", name: "Alice Smith", gender: "Female", department: "Engineering", seniority: "Senior" }]));
    await page.getByRole("button", { name: "Suggest Panel" }).click();

    await expect(page.getByText("Needs Review")).toBeVisible();
    await expect(page.getByText("Panel lacks gender diversity.")).toBeVisible();
  });
});
