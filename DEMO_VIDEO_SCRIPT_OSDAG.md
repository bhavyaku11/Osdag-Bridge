# Screencast Demo Video Script — OsdagBridge Task 3 & Task 6
## FOSSEE Winter Internship 2026 — Submission Demonstration

- **Candidate:** Bhavya Kumar  
- **Topics Covered:** Task 3 (LaTeX Report Generator Refactoring) & Task 6 (Software Testing & Issue Reporting)  
- **Target Video Duration:** 3 to 5 minutes  
- **Recommended Tools:** OBS Studio / QuickTime Screen Recording + Microphone

---

## Timeline & Scene-by-Scene Script

### [00:00 - 00:45] Introduction & Objectives
- **Visual:** Terminal or IDE showing the OsdagBridge repository and commit history.
- **Narrator Speaking:**
  > "Hello! My name is Bhavya Kumar, and this is my technical demonstration for the FOSSEE Winter Internship 2026 screening assignment on OsdagBridge.
  > Today, I will be presenting my contributions across two key areas:
  > First, **Task 3: LaTeX Report Generator Refactoring**, where I established a centralized styling engine, resolved critical footer margin overlaps, embedded high-DPI chart visualizers, and standardized table headers across all chapters.
  > Second, **Task 6: Software Testing and Issue Reporting**, where I created a comprehensive 20-scenario testing matrix, an automated test suite, and identified and fixed 7 critical issues in OsdagBridge, including Issue #103 regarding Bill of Materials volume calculations."

---

### [00:45 - 02:00] Task 3: LaTeX Report Generator Demonstrations
- **Visual:** Open `src/osdagbridge/core/reports/styles.py` in the IDE, followed by a side-by-side view of the generated LaTeX report and charts.
- **Narrator Speaking:**
  > "Let's first look at Task 3. In `styles.py`, I designed a centralized single source of truth for the entire report styling system.
  > Previously, document margins were hardcoded to 1 inch, which caused text on long check tables—such as Girder 4 on Page 30—to bleed directly into the green footer rule when software default footnotes were rendered.
  > By setting the bottom margin to 2.8 cm and footskip to 38 pt in our `GeometryConfig`, we completely eliminated this content collision.
  > Next, I developed `plot_utils.py` to inject visual analytics into the report:
  > In Section 5.5, we embed a 300 DPI Utilization Ratio summary bar chart with color-coded safety tiers and a red dashed permissible limit line at UR = 1.0.
  > In Chapter 7, we generate two distinct charts: a structural steel take-off breakdown across girders, bracing, and stiffeners, and a concrete volume versus rebar weight comparison.
  > Finally, all multi-page tables now implement `\endfirsthead` and `\endhead` with shaded headers (`tableHeaderBg`), guaranteeing that table headers repeat seamlessly across every page break."

---

### [02:00 - 03:30] Task 6: Software Testing & Bug #103 Fix Demonstration
- **Visual:** Terminal running `pytest -v` and `python3 tests/run_functional_tests.py`.
- **Actions in Terminal:**
  ```bash
  pytest -v
  python3 tests/run_functional_tests.py
  osdagbridge boq resources/sample_bridge_model.json
  ```
- **Narrator Speaking:**
  > "Moving to Task 6: Software Testing. I constructed a 20-scenario test matrix covering spans from 10 meters to 30 meters, 2 to 6 girders, skew angles up to 30 degrees, and custom steel and concrete grades.
  > As you can see on screen, our automated test suite executes all 30 pytest unit/integration tests and all 25 functional test matrix scenarios with a 100% pass rate.
  > In particular, let's examine Bug #103, which I confirmed and resolved:
  > In `boq_generator.py`, the Bill of Materials volume calculation previously used Girder 1's sectional area for all girders. When exterior and interior girders had different plate dimensions, this resulted in a 20% underestimation of structural steel tonnage.
  > I refactored the volume resolution to calculate each individual girder independently, added strict numerical validation rejecting non-finite or fractional girder numbers, cross-validated mass against volume-density consistency, and added regression guards against silent fallbacks if per-girder data is incomplete.
  > Furthermore, we implemented a full CLI with `analyze`, `boq`, and `report` commands, and documented 7 formal issues in `GITHUB_ISSUES_REPORT.md` following standard open-source issue templates."

---

### [03:30 - 04:00] Conclusion & Submission Wrap-Up
- **Visual:** Display GitHub repository, `SUBMISSION_REPORT_OSDAG.md`, and collaborator settings.
- **Narrator Speaking:**
  > "All code changes have been committed cleanly to our feature branch, thoroughly tested with unit tests and integration scripts, and are ready for review.
  > `Nidhikhare12` has been noted as collaborator for repository access.
  > Thank you to the FOSSEE team and IIT Bombay for this exciting opportunity to contribute to open-source civil engineering software!"

---

## Quick Reference Commands for Recording
```bash
# 1. Show git branch and commits
cd /Users/bhavyakumar/Documents/FOSSEE/osdag/OsdagBridge
git status
git log -n 2 --oneline

# 2. Run the full functional test suite
cd /Users/bhavyakumar/Documents/FOSSEE
python3 osdag/tests/run_functional_tests.py

# 3. Run pytest unit tests
PYTHONPATH=osdag/OsdagBridge/src pytest osdag/OsdagBridge/tests/unit/test_reports.py -v

# 4. View generated report charts
ls -lh /tmp/osdag_test_charts_suite/
```
