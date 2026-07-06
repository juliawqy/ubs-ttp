"""
seed_demo.py — Aequus demo data seeder.

Populates Recruitment, Performance, and Training services with realistic data
that exercises every bias-detection pathway in the system.

Runs automatically inside Docker via the `seeder` compose service.
Can also be run locally against a running stack:

    python tools/seed_demo.py                  # localhost default ports
    python tools/seed_demo.py --host myhost

Requires: httpx, reportlab
"""
from __future__ import annotations

import argparse
import io
import os
import sys
import time
from datetime import date, timedelta

import httpx
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# ---------------------------------------------------------------------------
# ANSI colours
# ---------------------------------------------------------------------------
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
CYAN   = "\033[36m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg: str)    -> None: print(f"  {GREEN}✔{RESET}  {msg}")
def warn(msg: str)  -> None: print(f"  {YELLOW}⚑{RESET}  {msg}")
def err(msg: str)   -> None: print(f"  {RED}✘{RESET}  {msg}")
def info(msg: str)  -> None: print(f"  {CYAN}→{RESET}  {msg}")
def head(msg: str)  -> None: print(f"\n{BOLD}{msg}{RESET}")


# ---------------------------------------------------------------------------
# PDF helper
# ---------------------------------------------------------------------------
def _make_cv_pdf(lines: list[str]) -> bytes:
    """Return a minimal pdfplumber-readable PDF containing the given lines."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    y = 720
    for line in lines:
        c.drawString(72, y, line)
        y -= 16
    c.save()
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Health-wait
# ---------------------------------------------------------------------------
def _wait_healthy(url: str, label: str, retries: int = 30, delay: float = 2.0) -> None:
    for attempt in range(1, retries + 1):
        try:
            r = httpx.get(url, timeout=3)
            if r.status_code == 200:
                ok(f"{label} is healthy")
                return
        except httpx.RequestError:
            pass
        if attempt == 1:
            info(f"Waiting for {label}...")
        time.sleep(delay)
    print(f"\n{RED}ERROR: {label} did not become healthy after {retries * delay:.0f}s.{RESET}")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Seeder
# ---------------------------------------------------------------------------
class DemoSeeder:
    def __init__(self, recruitment: str, performance: str, training: str) -> None:
        self.rec  = recruitment.rstrip("/")
        self.perf = performance.rstrip("/")
        self.tr   = training.rstrip("/")

    # -- convenience ---------------------------------------------------------

    def _post(self, base: str, path: str, payload: dict, *, label: str) -> dict | None:
        try:
            r = httpx.post(f"{base}{path}", json=payload, timeout=10)
        except httpx.RequestError as exc:
            err(f"{label} — request failed: {exc}")
            return None
        if r.status_code in (200, 201):
            return r.json()
        err(f"{label} — HTTP {r.status_code}: {r.text[:120]}")
        return None

    def _post_file(self, base: str, path: str, filename: str,
                   pdf_bytes: bytes, *, label: str) -> dict | None:
        try:
            r = httpx.post(
                f"{base}{path}",
                files={"file": (filename, pdf_bytes, "application/pdf")},
                timeout=10,
            )
        except httpx.RequestError as exc:
            err(f"{label} — request failed: {exc}")
            return None
        if r.status_code in (200, 201):
            return r.json()
        err(f"{label} — HTTP {r.status_code}: {r.text[:120]}")
        return None

    def _show_bias(self, result: dict) -> None:
        bc = result.get("bias_check") or {}
        if bc.get("flagged"):
            for fp in bc.get("flagged_phrases", []):
                warn(f'Bias flag -> "{fp["phrase"]}" -- {fp["reason"][:70]}...')
        else:
            ok("No bias flags detected")

    # -- job postings ---------------------------------------------------------

    def seed_job_postings(self) -> None:
        head("-- Job Postings -----------------------------------------------")

        postings = [
            # 1. Clean
            {
                "_label": "Senior Data Engineer (clean)",
                "title": "Senior Data Engineer",
                "description": (
                    "Design and maintain our data pipelines. You will build "
                    "scalable ETL processes, own data quality, and collaborate "
                    "across engineering and analytics teams."
                ),
                "requirements": ["Python", "SQL", "Spark", "dbt"],
                "department": "Data",
                "manager": {
                    "id": "mgr-001",
                    "name": "Sarah Tan",
                    "department": "Data",
                    "email": "sarah.tan@ubs.com",
                },
            },
            # 2. Jargon bias -- "rockstar", "ninja", "culture fit"
            {
                "_label": 'Rockstar Ninja role ("rockstar", "ninja", "culture fit" flagged)',
                "title": "Rockstar Frontend Ninja",
                "description": (
                    "We need a rockstar ninja who lives and breathes JavaScript. "
                    "You must be a culture fit who thrives in our fast-paced environment "
                    "and ships features at lightning speed."
                ),
                "requirements": ["React", "TypeScript", "CSS"],
                "department": "Engineering",
                "manager": {
                    "id": "mgr-002",
                    "name": "James Lim",
                    "department": "Engineering",
                    "email": "james.lim@ubs.com",
                },
            },
            # 3. Nationality discrimination -- regex: "locals only"
            {
                "_label": 'Singapore Backend role ("locals only" nationality flag)',
                "title": "Backend Engineer -- Singapore Office",
                "description": (
                    "Join our Singapore backend team. Locals only -- candidates must "
                    "be based in Singapore with no relocation required. "
                    "Strong Go or Java experience preferred."
                ),
                "requirements": ["Go", "Java", "Kubernetes", "PostgreSQL"],
                "department": "Engineering",
                "manager": {
                    "id": "mgr-001",
                    "name": "Sarah Tan",
                    "department": "Data",
                    "email": "sarah.tan@ubs.com",
                },
            },
            # 4. Age discrimination -- "digital native"
            {
                "_label": 'Product Manager role ("digital native" age-discrimination flag)',
                "title": "Digital Native Product Manager",
                "description": (
                    "We are looking for a digital native who grew up with social media "
                    "and understands Gen Z consumers instinctively. You will define "
                    "product roadmaps and own the mobile experience."
                ),
                "requirements": ["Product roadmap", "Agile", "User research"],
                "department": "Product",
                "manager": {
                    "id": "mgr-003",
                    "name": "Priya Nair",
                    "department": "Product",
                    "email": "priya.nair@ubs.com",
                },
            },
            # 5. Nationality discrimination -- regex: "only British applicants"
            {
                "_label": 'London Compliance role ("only British applicants" nationality flag)',
                "title": "Compliance Analyst -- London",
                "description": (
                    "Regulatory compliance analyst for our London desk. "
                    "Only British applicants will be considered for this role "
                    "due to client communication requirements."
                ),
                "requirements": ["FCA regulations", "Risk assessment", "Excel"],
                "department": "Compliance",
                "manager": {
                    "id": "mgr-004",
                    "name": "Oliver Brown",
                    "department": "Compliance",
                    "email": "oliver.brown@ubs.com",
                },
            },
            # 6. Clean
            {
                "_label": "UX Designer (clean)",
                "title": "UX / UI Designer",
                "description": (
                    "Create intuitive, accessible interfaces for our internal products. "
                    "You will conduct user research, prototype in Figma, and collaborate "
                    "with engineering to ship polished experiences."
                ),
                "requirements": ["Figma", "User research", "Accessibility (WCAG)"],
                "department": "Design",
                "manager": {
                    "id": "mgr-003",
                    "name": "Priya Nair",
                    "department": "Product",
                    "email": "priya.nair@ubs.com",
                },
            },
        ]

        for p in postings:
            label = p.pop("_label")
            info(label)
            result = self._post(self.rec, "/job-postings", p, label=label)
            if result:
                self._show_bias(result)

    # -- candidates -----------------------------------------------------------

    def seed_candidates(self) -> None:
        head("-- Candidates -------------------------------------------------")

        cvs = [
            # 1. Hired -- clean justification
            {
                "_label": "Alex Johnson -- hired (clean justification)",
                "_decision": "hired",
                "_justification": (
                    "Alex demonstrated strong proficiency across all required skills "
                    "in the technical screen. Structured answers, clear communication, "
                    "and directly relevant experience at scale. Recommended for hire."
                ),
                "_scores": {"Technical Skills": 9.0, "Communication & Clarity": 8.5},
                "_lines": [
                    "Alex Johnson",
                    "alex.johnson@email.com  |  github.com/alexjohnson",
                    "Senior Software Engineer -- 8 years Python, SQL, distributed systems",
                    "2016-2024  Tech Lead, DataCorp -- led team of 6, shipped ML pipeline",
                    "2014-2016  Software Engineer, FinanceHub -- built trading data APIs",
                    "Education: BSc Computer Science, NUS, 2014",
                ],
            },
            # 2. Rejected -- clean justification
            {
                "_label": "Sam Chen -- rejected (clean justification)",
                "_decision": "rejected",
                "_justification": (
                    "Sam has a solid foundation but lacked the depth in distributed "
                    "systems that this role requires. Limited hands-on experience with "
                    "stream processing and no production Spark usage. Would consider "
                    "again after two more years of relevant experience."
                ),
                "_scores": {"Technical Skills": 5.5, "Communication & Clarity": 7.0},
                "_lines": [
                    "Sam Chen",
                    "sam.chen@email.com",
                    "Software Engineer -- 3 years Python, SQL",
                    "2021-2024  Junior Engineer, StartupXYZ -- built REST APIs",
                    "2019-2021  Analyst, ConsultCo -- data reporting",
                    "Education: BSc Information Systems, SMU, 2019",
                ],
            },
            # 3. Rejected -- BIASED justification: "culture fit", "not a good fit"
            {
                "_label": 'Jordan Lee -- rejected (BIASED: "culture fit", "not a good fit" flagged)',
                "_decision": "rejected",
                "_justification": (
                    "Jordan's technical skills were acceptable but ultimately this candidate "
                    "is not a good fit for the team. The communication style doesn't match "
                    "our culture fit expectations and I don't think they would integrate "
                    "well into the existing team dynamic."
                ),
                "_scores": {"Technical Skills": 6.0, "Communication & Clarity": 6.5},
                "_lines": [
                    "Jordan Lee",
                    "jordan.lee@email.com",
                    "Full Stack Engineer -- 5 years React, Node.js, PostgreSQL",
                    "2019-2024  Software Engineer, MediaCo -- built content platform",
                    "2017-2019  Junior Developer, AgencyABC",
                    "Education: BEng Software Engineering, NTU, 2017",
                ],
            },
            # 4. Pending -- no decision yet
            {
                "_label": "Casey Morgan -- pending (interview in progress)",
                "_decision": None,
                "_justification": None,
                "_scores": {"Technical Skills": 7.5, "Communication & Clarity": 8.0},
                "_lines": [
                    "Casey Morgan",
                    "casey.morgan@email.com",
                    "Data Scientist -- 4 years Python, R, ML modelling",
                    "2020-2024  Data Scientist, AnalyticsFirm -- churn prediction models",
                    "2018-2020  Research Analyst, UniversityLab",
                    "Education: MSc Statistics, Oxford, 2018",
                ],
            },
        ]

        criteria = [
            {"name": "Technical Skills",       "weight": 0.6, "required": True},
            {"name": "Communication & Clarity", "weight": 0.4, "required": True},
        ]

        for cv in cvs:
            label         = cv["_label"]
            decision      = cv["_decision"]
            justification = cv["_justification"]
            scores        = cv["_scores"]
            pdf_bytes     = _make_cv_pdf(cv["_lines"])

            info(label)

            upload = self._post_file(
                self.rec, "/candidates/upload", "cv.pdf", pdf_bytes,
                label=f"{label} [upload]",
            )
            if not upload:
                continue

            cid = upload["candidate_id"]

            self._post(
                self.rec, "/candidates/assess",
                {"candidate_id": cid, "criteria": criteria, "scores": scores},
                label=f"{label} [assess]",
            )

            if decision and justification:
                result = self._post(
                    self.rec, f"/candidates/{cid}/decide",
                    {"decision": decision, "justification": justification},
                    label=f"{label} [decide]",
                )
                if result:
                    self._show_bias(result)
            else:
                ok("No decision yet -- candidate stays pending")

    # -- performance reviews --------------------------------------------------

    def seed_reviews(self) -> None:
        head("-- Performance Reviews ----------------------------------------")

        reviews = [
            # 1. Clean -- high scorer
            {
                "_label": "emp-001 review by mgr-001 (clean, high scorer)",
                "employee_id": "emp-001",
                "reviewer_id": "mgr-001",
                "criteria": [
                    {"criterion": "Technical Quality",       "score": 5, "comments": "Consistently delivers well-tested, maintainable code. Led the refactor of the pipeline service with measurable quality improvements."},
                    {"criterion": "Collaboration",           "score": 5, "comments": "Sought out and incorporated feedback from five different stakeholders before shipping. Excellent cross-team communicator."},
                    {"criterion": "Ownership & Reliability", "score": 4, "comments": "On-call response time consistently under ten minutes. Proactively flagged two incidents before they escalated."},
                    {"criterion": "Growth & Learning",       "score": 4, "comments": "Completed three internal certifications this quarter. Mentors two junior engineers effectively."},
                ],
            },
            # 2. Biased -- "aggressive" flagged
            {
                "_label": 'emp-002 review by mgr-001 (BIASED: "aggressive" flagged)',
                "employee_id": "emp-002",
                "reviewer_id": "mgr-001",
                "criteria": [
                    {"criterion": "Technical Quality",       "score": 4, "comments": "Good output, reliable deliveries."},
                    {"criterion": "Collaboration",           "score": 2, "comments": "Can be aggressive in meetings and tends to push their view without listening to alternatives. Others have noted this too."},
                    {"criterion": "Ownership & Reliability", "score": 3, "comments": "Meets deadlines but sometimes at the cost of team cohesion."},
                    {"criterion": "Growth & Learning",       "score": 3, "comments": "Engages with training materials when asked but rarely self-initiates."},
                ],
            },
            # 3. Biased -- "culture fit" and "doesn't fit" flagged
            {
                "_label": 'emp-003 review by mgr-002 (BIASED: "culture fit", "doesn\'t fit" flagged)',
                "employee_id": "emp-003",
                "reviewer_id": "mgr-002",
                "criteria": [
                    {"criterion": "Technical Quality",       "score": 3, "comments": "Adequate technical output, no major issues."},
                    {"criterion": "Collaboration",           "score": 2, "comments": "Doesn't fit well with the team dynamic. There's a culture fit issue that the team has noticed."},
                    {"criterion": "Ownership & Reliability", "score": 3, "comments": "Shows up and delivers tasks as assigned."},
                    {"criterion": "Growth & Learning",       "score": 2, "comments": "Has not engaged with the development plan set at the start of the year."},
                ],
            },
            # 4. Clean -- mid-range
            {
                "_label": "emp-004 review by mgr-003 (clean, mid-range scores)",
                "employee_id": "emp-004",
                "reviewer_id": "mgr-003",
                "criteria": [
                    {"criterion": "Technical Quality",       "score": 3, "comments": "Meets the baseline requirements. Code reviews show some gaps in edge-case handling worth addressing."},
                    {"criterion": "Collaboration",           "score": 4, "comments": "Actively participates in planning sessions and responds to feedback constructively."},
                    {"criterion": "Ownership & Reliability", "score": 3, "comments": "Generally reliable but two missed deadlines this quarter need attention."},
                    {"criterion": "Growth & Learning",       "score": 3, "comments": "Completed the mandatory training. Encourage more self-directed learning next quarter."},
                ],
            },
        ]

        for rv in reviews:
            label = rv.pop("_label")
            info(label)
            result = self._post(self.perf, "/reviews", rv, label=label)
            if result:
                bc = result.get("bias_check") or {}
                if bc.get("flagged"):
                    for fp in bc.get("flagged_phrases", []):
                        warn(f'Bias flag -> "{fp["phrase"]}" -- {fp["reason"][:70]}...')
                else:
                    ok("No bias flags detected")

    # -- 360 feedback ---------------------------------------------------------

    def seed_feedback(self) -> None:
        head("-- 360 Feedback -----------------------------------------------")

        entries = [
            {"_label": "emp-001 from emp-005 (clean)", "_block": False,
             "employee_id": "emp-001", "rater_id": "emp-005",
             "comments": "Exceptionally helpful during the Q3 migration. Explained complex concepts patiently and always made time for questions."},
            {"_label": "emp-001 from emp-006 (clean)", "_block": False,
             "employee_id": "emp-001", "rater_id": "emp-006",
             "comments": "Reliable partner on the data pipeline work. Raises blockers early and communicates status clearly without being prompted."},
            {"_label": "emp-002 from emp-005 (clean, constructive)", "_block": False,
             "employee_id": "emp-002", "rater_id": "emp-005",
             "comments": "Strong technical contributor. I'd encourage more active listening in design discussions -- their ideas land better when others feel heard first."},
            {"_label": "emp-003 from emp-007 (clean)", "_block": False,
             "employee_id": "emp-003", "rater_id": "emp-007",
             "comments": "Solid on individual tasks. Would benefit from more proactive communication when blockers arise mid-sprint."},
            {"_label": "emp-002 from emp-008 (BLOCKED: offensive language)", "_block": True,
             "employee_id": "emp-002", "rater_id": "emp-008",
             "comments": "This person is completely useless and a waste of space on the team."},
        ]

        for entry in entries:
            label = entry.pop("_label")
            block = entry.pop("_block")
            info(label)
            try:
                r = httpx.post(f"{self.perf}/feedback", json=entry, timeout=10)
            except httpx.RequestError as exc:
                err(f"Request failed: {exc}")
                continue

            if block:
                if r.status_code == 422:
                    ok("Correctly BLOCKED -- offensive language rejected (HTTP 422)")
                else:
                    warn(f"Expected 422 block, got HTTP {r.status_code}")
            else:
                if r.status_code in (200, 201):
                    ok("Submitted successfully")
                else:
                    err(f"HTTP {r.status_code}: {r.text[:80]}")

    # -- training modules -----------------------------------------------------

    def seed_training_modules(self) -> None:
        head("-- Training Modules -------------------------------------------")

        today = date.today()
        modules = [
            {"title": "Unconscious Bias Awareness",        "assigned_to": "mgr-001", "due_date": str(today + timedelta(days=30)),  "description": "Understand how unconscious bias affects hiring, promotion, and day-to-day team decisions. Includes research-backed case studies."},
            {"title": "Inclusive Hiring Practices",        "assigned_to": "mgr-002", "due_date": str(today + timedelta(days=14)),  "description": "Structured interview techniques, blind CV review processes, and panel diversity guidelines."},
            {"title": "Structured Interview Techniques",   "assigned_to": "emp-001", "due_date": str(today + timedelta(days=21)),  "description": "How to design and run behavioural interviews that assess skills consistently across all candidates."},
            {"title": "Allyship at Work",                  "assigned_to": "emp-002", "due_date": str(today + timedelta(days=45)),  "description": "Practical tools for becoming an effective ally -- speaking up, amplifying underrepresented voices, and addressing microaggressions."},
            {"title": "Writing Bias-Free Job Descriptions","assigned_to": "mgr-003", "due_date": str(today + timedelta(days=10)),  "description": "Hands-on workshop: rewrite real job postings to eliminate exclusionary language and widen the applicant pool."},
        ]

        for mod in modules:
            label = f'{mod["title"]} -> {mod["assigned_to"]}'
            info(label)
            result = self._post(self.tr, "/training/modules", mod, label=label)
            if result:
                ok(f'Created module #{result.get("id")} due {mod["due_date"]}')

    # -- run all --------------------------------------------------------------

    def run(self) -> None:
        self.seed_job_postings()
        self.seed_candidates()
        self.seed_reviews()
        self.seed_feedback()
        self.seed_training_modules()

        head("-- Done -------------------------------------------------------")
        print(f"""
  {BOLD}Bias scenarios seeded:{RESET}

  {YELLOW}Job Postings flagged:{RESET}
    - "Rockstar Frontend Ninja"        -> rockstar, ninja, culture fit
    - "Backend Engineer (Singapore)"   -> locals only (nationality)
    - "Digital Native Product Manager" -> digital native (age)
    - "Compliance Analyst London"      -> only British applicants (nationality)

  {YELLOW}Hire Decisions flagged:{RESET}
    - Jordan Lee rejection             -> culture fit, not a good fit

  {YELLOW}Performance Reviews flagged:{RESET}
    - emp-002 review                   -> aggressive (gendered)
    - emp-003 review                   -> culture fit, doesn't fit

  {RED}Feedback blocked (HTTP 422):{RESET}
    - emp-002 from emp-008             -> useless, waste of space (offensive)

  {GREEN}Clean (no flags):{RESET}
    - 2 job postings, 2 decisions, 2 reviews, 4 feedback, 5 training modules
""")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Aequus with demo data")
    parser.add_argument("--host",     default="localhost")
    parser.add_argument("--rec-port",  type=int, default=8001)
    parser.add_argument("--perf-port", type=int, default=8003)
    parser.add_argument("--tr-port",   type=int, default=8002)
    parser.add_argument("--no-wait",  action="store_true",
                        help="Skip health-check wait (used inside Docker where "
                             "depends_on handles readiness)")
    args = parser.parse_args()

    rec_base  = os.environ.get("REC_URL",  f"http://{args.host}:{args.rec_port}")
    perf_base = os.environ.get("PERF_URL", f"http://{args.host}:{args.perf_port}")
    tr_base   = os.environ.get("TR_URL",   f"http://{args.host}:{args.tr_port}")

    print(f"\n{BOLD}Aequus Demo Seeder{RESET}")
    print(f"  Recruitment  -> {rec_base}")
    print(f"  Performance  -> {perf_base}")
    print(f"  Training     -> {tr_base}")

    if not args.no_wait:
        head("-- Health checks ----------------------------------------------")
        _wait_healthy(f"{rec_base}/health",  "Recruitment")
        _wait_healthy(f"{perf_base}/health", "Performance")
        _wait_healthy(f"{tr_base}/health",   "Training")

    DemoSeeder(rec_base, perf_base, tr_base).run()


if __name__ == "__main__":
    main()
