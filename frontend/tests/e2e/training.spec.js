// @ts-check
/**
 * E2E tests for the Training page.
 * Run: cd frontend && npx playwright test
 *
 * All API calls are stubbed.
 */
import { test, expect } from "@playwright/test";

/** @type {any[]} */
const MOCK_MODULES = [
  {
    id: 1,
    title: "Inclusive Leadership 101",
    assigned_to: "emp-1",
    due_date: "2026-07-15",
    description: "Foundations of inclusive leadership.",
    completion_pct: 40,
    status: "in_progress",
    reminder_count: 0,
  },
];

/** @type {any[]} */
const MOCK_IAT_CATEGORIES = [
  {
    id: "decision-style",
    label: "Decision-Making Style",
    pole_a: "Analytical",
    pole_b: "Intuitive",
    stimuli: ["Data", "Logic", "Evidence", "Metrics"],
  },
  {
    id: "feedback-style",
    label: "Feedback Style",
    pole_a: "Direct",
    pole_b: "Diplomatic",
    stimuli: ["Blunt", "Frank", "Candid", "Tactful"],
  },
];

/** @type {any[]} */
const MOCK_CAREER_ENTRIES = [
  {
    id: 1,
    employee_name: "Jordan Lee",
    current_role: "software engineer",
    next_milestone: "senior software engineer",
    target_date: "2026-12-01",
    recommended_skills: ["System Design", "Code Review", "Mentoring"],
  },
];

// ─── Helpers ───────────────────────────────────────────────────────────────────

/**
 * @param {import('@playwright/test').Page} page
 * @param {any[]} data
 */
async function mockGetModules(page, data = MOCK_MODULES) {
  await page.route("**/api/training/modules", (route) => {
    if (route.request().method() === "GET") {
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(data) });
    } else {
      route.continue();
    }
  });
}

/**
 * @param {import('@playwright/test').Page} page
 * @param {any[]} data
 */
async function mockGetIatCategories(page, data = MOCK_IAT_CATEGORIES) {
  await page.route("**/api/training/iat/categories", (route) => {
    if (route.request().method() === "GET") {
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(data) });
    } else {
      route.continue();
    }
  });
}

/**
 * @param {import('@playwright/test').Page} page
 * @param {any[]} data
 */
async function mockGetCareerEntries(page, data = MOCK_CAREER_ENTRIES) {
  await page.route("**/api/training/career-mapping", (route) => {
    if (route.request().method() === "GET") {
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(data) });
    } else {
      route.continue();
    }
  });
}

// ─── Modules tab ───────────────────────────────────────────────────────────────

test.describe("Modules tab", () => {
  test("shows modules table on load", async ({ page }) => {
    await mockGetModules(page);
    await page.goto("/training");
    await expect(page.getByRole("cell", { name: "Inclusive Leadership 101" })).toBeVisible();
    await expect(page.getByRole("cell", { name: "emp-1" })).toBeVisible();
    await expect(page.getByText("2026-07-15")).toBeVisible();
    await expect(page.getByText("40%")).toBeVisible();
  });

  test("shows empty state when no modules", async ({ page }) => {
    await mockGetModules(page, []);
    await page.goto("/training");
    await expect(page.getByText("No modules assigned yet")).toBeVisible();
  });

  test("each row has Edit, Remind, and Delete actions", async ({ page }) => {
    await mockGetModules(page);
    await page.goto("/training");
    await expect(page.getByRole("button", { name: "Edit" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Remind" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Delete" })).toBeVisible();
  });
});

// ─── New / Edit Module modal ───────────────────────────────────────────────────

test.describe("New / Edit Module modal", () => {
  test("modal opens on + New Module click", async ({ page }) => {
    await mockGetModules(page);
    await page.goto("/training");
    await page.getByRole("button", { name: "+ New Module" }).click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await expect(page.getByText("New Training Module")).toBeVisible();
    // Completion % only makes sense once a module exists
    await expect(page.locator("#module-progress-row")).not.toBeVisible();
  });

  test("modal closes on Cancel", async ({ page }) => {
    await mockGetModules(page);
    await page.goto("/training");
    await page.getByRole("button", { name: "+ New Module" }).click();
    await page.getByRole("button", { name: "Cancel" }).click();
    await expect(page.getByRole("dialog")).not.toBeVisible();
  });

  test("creating a module sends the correct payload", async ({ page }) => {
    await mockGetModules(page);
    let capturedBody = /** @type {any} */ (null);

    await page.route("**/api/training/modules", async (route) => {
      if (route.request().method() === "POST") {
        capturedBody = route.request().postDataJSON();
        await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify(MOCK_MODULES[0]) });
      } else {
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_MODULES) });
      }
    });

    await page.goto("/training");
    await page.getByRole("button", { name: "+ New Module" }).click();

    await page.fill("#module-title", "Bias Awareness Basics");
    await page.fill("#module-assigned-to", "emp-9");
    await page.fill("#module-due-date", "2026-08-01");
    await page.fill("#module-description", "Intro module on recognising unconscious bias.");

    await page.getByRole("button", { name: "Create Module" }).click();

    await expect(page.getByRole("dialog")).not.toBeVisible();
    expect(capturedBody).not.toBeNull();
    expect(capturedBody.title).toBe("Bias Awareness Basics");
    expect(capturedBody.assigned_to).toBe("emp-9");
    expect(capturedBody.due_date).toBe("2026-08-01");
  });

  test("create failure shows inline form error and keeps modal open", async ({ page }) => {
    await mockGetModules(page);
    await page.route("**/api/training/modules", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({ status: 422, contentType: "application/json", body: JSON.stringify({ detail: "title cannot be empty" }) });
      } else {
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_MODULES) });
      }
    });

    await page.goto("/training");
    await page.getByRole("button", { name: "+ New Module" }).click();
    await page.fill("#module-assigned-to", "emp-9");
    await page.fill("#module-due-date", "2026-08-01");
    await page.getByRole("button", { name: "Create Module" }).click();

    await expect(page.getByText("title cannot be empty")).toBeVisible();
    await expect(page.getByRole("dialog")).toBeVisible();
  });

  test("Edit prefills the form and shows the Completion % field", async ({ page }) => {
    await mockGetModules(page);
    await page.goto("/training");
    await page.getByRole("button", { name: "Edit" }).click();

    await expect(page.getByText("Edit Training Module")).toBeVisible();
    await expect(page.locator("#module-title")).toHaveValue("Inclusive Leadership 101");
    await expect(page.locator("#module-assigned-to")).toHaveValue("emp-1");
    await expect(page.locator("#module-due-date")).toHaveValue("2026-07-15");
    await expect(page.locator("#module-progress-row")).toBeVisible();
    await expect(page.locator("#module-progress")).toHaveValue("40");
  });

  test("editing a module sends PUT, and PATCH only when completion changes", async ({ page }) => {
    await mockGetModules(page);
    let putBody = /** @type {any} */ (null);
    let patchBody = /** @type {any} */ (null);

    await page.route("**/api/training/modules/*/progress", async (route) => {
      patchBody = route.request().postDataJSON();
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ...MOCK_MODULES[0], completion_pct: patchBody.completion_pct }) });
    });
    await page.route("**/api/training/modules/*", async (route) => {
      if (route.request().method() === "PUT") {
        putBody = route.request().postDataJSON();
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ...MOCK_MODULES[0], ...putBody }) });
      } else {
        await route.continue();
      }
    });

    await page.goto("/training");
    await page.getByRole("button", { name: "Edit" }).click();
    await page.fill("#module-title", "Inclusive Leadership 201");
    await page.fill("#module-progress", "75");
    await page.getByRole("button", { name: "Save Changes" }).click();

    await expect(page.getByRole("dialog")).not.toBeVisible();
    expect(putBody.title).toBe("Inclusive Leadership 201");
    expect(patchBody.completion_pct).toBe(75);
  });

  test("editing a module without changing completion does not call PATCH", async ({ page }) => {
    await mockGetModules(page);
    let patchCalled = false;

    await page.route("**/api/training/modules/*/progress", async (route) => {
      patchCalled = true;
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_MODULES[0]) });
    });
    await page.route("**/api/training/modules/*", async (route) => {
      if (route.request().method() === "PUT") {
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_MODULES[0]) });
      } else {
        await route.continue();
      }
    });

    await page.goto("/training");
    await page.getByRole("button", { name: "Edit" }).click();
    await page.fill("#module-title", "Inclusive Leadership 101 (revised)");
    await page.getByRole("button", { name: "Save Changes" }).click();

    await expect(page.getByRole("dialog")).not.toBeVisible();
    expect(patchCalled).toBe(false);
  });
});

// ─── Module row actions: Remind / Delete ───────────────────────────────────────

test.describe("Module row actions", () => {
  test("Remind shows a confirmation when a reminder is sent", async ({ page }) => {
    await mockGetModules(page);
    await page.route("**/api/training/modules/*/remind", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ...MOCK_MODULES[0], reminder_count: 1 }) });
    });

    await page.goto("/training");
    const dialogPromise = page.waitForEvent("dialog");
    await page.getByRole("button", { name: "Remind" }).click();
    const dialog = await dialogPromise;
    expect(dialog.message()).toContain("Reminder sent");
    await dialog.accept();
  });

  test("Remind shows a visible error instead of failing silently when no reminder is due (409)", async ({ page }) => {
    await mockGetModules(page);
    await page.route("**/api/training/modules/*/remind", async (route) => {
      await route.fulfill({ status: 409, contentType: "application/json", body: JSON.stringify({ detail: "No reminder is due for this module" }) });
    });

    await page.goto("/training");
    const dialogPromise = page.waitForEvent("dialog");
    await page.getByRole("button", { name: "Remind" }).click();
    const dialog = await dialogPromise;
    expect(dialog.message()).toContain("No reminder is due for this module");
    await dialog.accept();
  });

  test("Delete sends a DELETE request once confirmed", async ({ page }) => {
    await mockGetModules(page);
    let deleteCalled = false;

    await page.route("**/api/training/modules/*", async (route) => {
      if (route.request().method() === "DELETE") {
        deleteCalled = true;
        await route.fulfill({ status: 204 });
      } else {
        await route.continue();
      }
    });

    await page.goto("/training");
    page.once("dialog", (dialog) => dialog.accept());
    await page.getByRole("button", { name: "Delete" }).click();
    await expect.poll(() => deleteCalled).toBe(true);
  });

  test("Delete does nothing if the confirmation is dismissed", async ({ page }) => {
    await mockGetModules(page);
    let deleteCalled = false;

    await page.route("**/api/training/modules/*", async (route) => {
      if (route.request().method() === "DELETE") {
        deleteCalled = true;
        await route.fulfill({ status: 204 });
      } else {
        await route.continue();
      }
    });

    await page.goto("/training");
    page.once("dialog", (dialog) => dialog.dismiss());
    await page.getByRole("button", { name: "Delete" }).click();
    await page.waitForTimeout(200);
    expect(deleteCalled).toBe(false);
  });
});

// ─── Career Mapping tab ────────────────────────────────────────────────────────

test.describe("Career Mapping tab", () => {
  test("shows career paths with recommended skills on load", async ({ page }) => {
    await mockGetModules(page);
    await mockGetCareerEntries(page);
    await page.goto("/training");
    await page.getByRole("button", { name: "Career Mapping" }).click();

    await expect(page.getByRole("cell", { name: "Jordan Lee" })).toBeVisible();
    await expect(page.getByText("software engineer")).toBeVisible();
    await expect(page.getByText("System Design")).toBeVisible();
    await expect(page.getByText("Mentoring")).toBeVisible();
  });

  test("shows empty state when no career paths are mapped", async ({ page }) => {
    await mockGetModules(page);
    await mockGetCareerEntries(page, []);
    await page.goto("/training");
    await page.getByRole("button", { name: "Career Mapping" }).click();

    await expect(page.getByText("No career paths mapped yet")).toBeVisible();
  });
});

// ─── New / Edit Career Entry modal ─────────────────────────────────────────────

test.describe("New / Edit Career Entry modal", () => {
  test("modal opens on + New Entry click", async ({ page }) => {
    await mockGetModules(page);
    await mockGetCareerEntries(page);
    await page.goto("/training");
    await page.getByRole("button", { name: "Career Mapping" }).click();
    await page.getByRole("button", { name: "+ New Entry" }).click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await expect(page.getByText("New Career Path Entry")).toBeVisible();
  });

  test("creating an entry sends the correct payload", async ({ page }) => {
    await mockGetModules(page);
    await mockGetCareerEntries(page);
    let capturedBody = /** @type {any} */ (null);

    await page.route("**/api/training/career-mapping", async (route) => {
      if (route.request().method() === "POST") {
        capturedBody = route.request().postDataJSON();
        await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify(MOCK_CAREER_ENTRIES[0]) });
      } else {
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_CAREER_ENTRIES) });
      }
    });

    await page.goto("/training");
    await page.getByRole("button", { name: "Career Mapping" }).click();
    await page.getByRole("button", { name: "+ New Entry" }).click();

    await page.fill("#career-employee-name", "Priya Nair");
    await page.fill("#career-current-role", "software engineer");
    await page.fill("#career-next-milestone", "senior software engineer");
    await page.fill("#career-target-date", "2027-01-01");

    await page.getByRole("button", { name: "Create Entry" }).click();

    await expect(page.getByRole("dialog")).not.toBeVisible();
    expect(capturedBody).not.toBeNull();
    expect(capturedBody.employee_name).toBe("Priya Nair");
    expect(capturedBody.current_role).toBe("software engineer");
    expect(capturedBody.next_milestone).toBe("senior software engineer");
  });

  test("Edit prefills the form and saves via PUT", async ({ page }) => {
    await mockGetModules(page);
    await mockGetCareerEntries(page);
    let putBody = /** @type {any} */ (null);

    await page.route("**/api/training/career-mapping/*", async (route) => {
      if (route.request().method() === "PUT") {
        putBody = route.request().postDataJSON();
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ...MOCK_CAREER_ENTRIES[0], ...putBody }) });
      } else {
        await route.continue();
      }
    });

    await page.goto("/training");
    await page.getByRole("button", { name: "Career Mapping" }).click();
    await page.getByRole("button", { name: "Edit" }).click();

    await expect(page.locator("#career-employee-name")).toHaveValue("Jordan Lee");
    await expect(page.locator("#career-current-role")).toHaveValue("software engineer");

    await page.fill("#career-next-milestone", "engineering manager");
    await page.getByRole("button", { name: "Save Changes" }).click();

    await expect(page.getByRole("dialog")).not.toBeVisible();
    expect(putBody.next_milestone).toBe("engineering manager");
  });

  test("Delete sends a DELETE request once confirmed", async ({ page }) => {
    await mockGetModules(page);
    await mockGetCareerEntries(page);
    let deleteCalled = false;

    await page.route("**/api/training/career-mapping/*", async (route) => {
      if (route.request().method() === "DELETE") {
        deleteCalled = true;
        await route.fulfill({ status: 204 });
      } else {
        await route.continue();
      }
    });

    await page.goto("/training");
    await page.getByRole("button", { name: "Career Mapping" }).click();
    page.once("dialog", (dialog) => dialog.accept());
    await page.getByRole("button", { name: "Delete" }).click();
    await expect.poll(() => deleteCalled).toBe(true);
  });
});

// ─── Implicit Association Test (IAT) flow ──────────────────────────────────────

test.describe("Implicit Association Test (IAT) flow", () => {
  test("shows the employee id input and start button initially", async ({ page }) => {
    await mockGetModules(page);
    await page.goto("/training");
    await page.getByRole("button", { name: "Self-Reflection (IAT)" }).click();

    await expect(page.locator("#iat-employee-id")).toBeVisible();
    await expect(page.getByRole("button", { name: "Start Private Session" })).toBeVisible();
  });

  test("shows an inline error when starting without an employee id", async ({ page }) => {
    await mockGetModules(page);
    await page.goto("/training");
    await page.getByRole("button", { name: "Self-Reflection (IAT)" }).click();
    await page.getByRole("button", { name: "Start Private Session" }).click();

    await expect(page.getByText("Enter your Employee ID")).toBeVisible();
  });

  test("starting a session begins the trial flow", async ({ page }) => {
    await mockGetModules(page);
    await mockGetIatCategories(page);
    await page.route("**/api/training/iat/sessions", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify({ id: 1, employee_id: "emp-1", status: "in_progress", response_count: 0 }) });
      } else {
        await route.continue();
      }
    });

    await page.goto("/training");
    await page.getByRole("button", { name: "Self-Reflection (IAT)" }).click();
    await page.fill("#iat-employee-id", "emp-1");
    await page.getByRole("button", { name: "Start Private Session" }).click();

    await expect(page.getByText("Question 1 of 8")).toBeVisible();
    await expect(page.locator("#iat-stimulus")).toBeVisible();
  });

  test("completing all trials shows private results", async ({ page }) => {
    await mockGetModules(page);
    await mockGetIatCategories(page);
    await page.route("**/api/training/iat/sessions", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify({ id: 1, employee_id: "emp-1", status: "in_progress", response_count: 0 }) });
      } else {
        await route.continue();
      }
    });
    await page.route("**/api/training/iat/sessions/*/responses", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ id: 1, employee_id: "emp-1", status: "in_progress", response_count: 1 }) });
    });
    await page.route("**/api/training/iat/sessions/*/complete", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ session_id: 1, employee_id: "emp-1", category_scores: { "decision-style": 120, "feedback-style": -80 } }),
      });
    });
    await page.route(/\/api\/training\/iat\/sessions\/\d+\/result/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ session_id: 1, employee_id: "emp-1", category_scores: { "decision-style": 120, "feedback-style": -80 } }),
      });
    });

    await page.goto("/training");
    await page.getByRole("button", { name: "Self-Reflection (IAT)" }).click();
    await page.fill("#iat-employee-id", "emp-1");
    await page.getByRole("button", { name: "Start Private Session" }).click();

    for (let i = 0; i < 8; i++) {
      await page.locator("#iat-pole-a-btn").click();
    }

    await expect(page.getByText("Your results")).toBeVisible();
    await expect(page.getByText("Decision-Making Style")).toBeVisible();
    await expect(page.getByText(/Analytical/)).toBeVisible();
    await expect(page.getByText("Feedback Style")).toBeVisible();
    await expect(page.getByText(/Diplomatic/)).toBeVisible();
  });

  test("Take Again resets back to the intro screen", async ({ page }) => {
    await mockGetModules(page);
    await mockGetIatCategories(page);
    await page.route("**/api/training/iat/sessions", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify({ id: 1, employee_id: "emp-1", status: "in_progress", response_count: 0 }) });
      } else {
        await route.continue();
      }
    });
    await page.route("**/api/training/iat/sessions/*/responses", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ id: 1, employee_id: "emp-1", status: "in_progress", response_count: 1 }) });
    });
    await page.route("**/api/training/iat/sessions/*/complete", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ session_id: 1, employee_id: "emp-1", category_scores: { "decision-style": 120, "feedback-style": -80 } }),
      });
    });
    await page.route(/\/api\/training\/iat\/sessions\/\d+\/result/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ session_id: 1, employee_id: "emp-1", category_scores: { "decision-style": 120, "feedback-style": -80 } }),
      });
    });

    await page.goto("/training");
    await page.getByRole("button", { name: "Self-Reflection (IAT)" }).click();
    await page.fill("#iat-employee-id", "emp-1");
    await page.getByRole("button", { name: "Start Private Session" }).click();
    for (let i = 0; i < 8; i++) {
      await page.locator("#iat-pole-a-btn").click();
    }
    await expect(page.getByText("Your results")).toBeVisible();

    await page.getByRole("button", { name: "Take Again" }).click();
    await expect(page.getByRole("button", { name: "Start Private Session" })).toBeVisible();
    await expect(page.locator("#iat-employee-id")).toHaveValue("");
  });

  test("shows a privacy error and resets if the result fetch is denied (403)", async ({ page }) => {
    await mockGetModules(page);
    await mockGetIatCategories(page);
    await page.route("**/api/training/iat/sessions", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify({ id: 1, employee_id: "emp-1", status: "in_progress", response_count: 0 }) });
      } else {
        await route.continue();
      }
    });
    await page.route("**/api/training/iat/sessions/*/responses", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ id: 1, employee_id: "emp-1", status: "in_progress", response_count: 1 }) });
    });
    await page.route("**/api/training/iat/sessions/*/complete", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ session_id: 1, employee_id: "emp-1", category_scores: { "decision-style": 120, "feedback-style": -80 } }),
      });
    });
    await page.route(/\/api\/training\/iat\/sessions\/\d+\/result/, async (route) => {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "IAT results are private to the employee who took the test" }),
      });
    });

    await page.goto("/training");
    await page.getByRole("button", { name: "Self-Reflection (IAT)" }).click();
    await page.fill("#iat-employee-id", "emp-1");
    await page.getByRole("button", { name: "Start Private Session" }).click();
    for (let i = 0; i < 8; i++) {
      await page.locator("#iat-pole-a-btn").click();
    }

    await expect(page.getByText(/private to the employee/)).toBeVisible();
    await expect(page.getByRole("button", { name: "Start Private Session" })).toBeVisible();
  });

  test("renders whatever categories the backend returns, not hardcoded content", async ({ page }) => {
    // Deliberately different from the stub data (MOCK_IAT_CATEGORIES) to prove
    // the frontend has no hardcoded fallback left -- it renders exactly what
    // GET /training/iat/categories returns. This is the concrete check behind
    // the "company can plug in its own modules later" claim: swapping the
    // backend's IATCategoryCatalog changes what shows up here, with zero
    // frontend changes.
    const CUSTOM_CATEGORIES = [
      {
        id: "custom-category",
        label: "Custom Company Category",
        pole_a: "FooPole",
        pole_b: "BarPole",
        stimuli: ["Widget"],
      },
    ];

    await mockGetModules(page);
    await mockGetIatCategories(page, CUSTOM_CATEGORIES);
    await page.route("**/api/training/iat/sessions", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify({ id: 1, employee_id: "emp-1", status: "in_progress", response_count: 0 }) });
      } else {
        await route.continue();
      }
    });

    await page.goto("/training");
    await page.getByRole("button", { name: "Self-Reflection (IAT)" }).click();
    await page.fill("#iat-employee-id", "emp-1");
    await page.getByRole("button", { name: "Start Private Session" }).click();

    await expect(page.getByText("Question 1 of 1")).toBeVisible();
    await expect(page.getByText("Custom Company Category")).toBeVisible();
    await expect(page.locator("#iat-stimulus")).toHaveText("Widget");
    await expect(page.locator("#iat-pole-a-btn")).toHaveText("FooPole");
    await expect(page.locator("#iat-pole-b-btn")).toHaveText("BarPole");
  });
});
