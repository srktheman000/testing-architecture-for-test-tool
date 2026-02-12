# Slide 10 — Module 6: Results & RCA Agent

## From Test Failures to Root Causes to Jira Defects

---

## Module Overview

The Results & RCA (Root Cause Analysis) Agent collects all execution artifacts, **analyzes failures to determine root cause**, and automatically creates or updates Jira defects with complete evidence.

> **Architect's Insight:** A test failure without root cause analysis is just noise. This agent transforms raw failure data into actionable intelligence.

---

## Responsibilities

| Responsibility | What It Does | Why It Matters |
|---------------|-------------|----------------|
| **Capture Logs, Screenshots, Videos** | Collect all execution evidence — console logs, network logs, failure screenshots, execution videos | Evidence is essential for debugging and compliance |
| **Identify Root Cause** | Classify failures into categories: app bug, infra issue, test script issue, data issue, environment issue | Wrong classification wastes developer time |
| **Auto-Create Jira Defects** | Generate structured bug reports with title, steps, evidence, severity — and push to Jira | Closes the loop: test runs → bugs filed → developers fix |

---

## RCA Classification Engine

```
┌──────────────────────┐
│  Execution Results    │
│  • Pass/Fail per TC   │
│  • Logs               │
│  • Screenshots        │
│  • Videos             │
│  • Network traces     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│                      RCA AGENT                                    │
│                                                                  │
│  Step 1: Evidence Collection                                     │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ Aggregate all artifacts for each failed test            │     │
│  │ • Console logs (browser + server)                       │     │
│  │ • Screenshot at failure point                           │     │
│  │ • Video recording of full test                          │     │
│  │ • Network HAR trace                                     │     │
│  │ • DOM snapshot at failure                               │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  Step 2: Root Cause Classification                               │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ Analyze evidence using pattern matching + AI:           │     │
│  │                                                         │     │
│  │  PATTERN              → CLASSIFICATION                  │     │
│  │  ────────────────────────────────────────────           │     │
│  │  Assertion mismatch    → Application Bug                │     │
│  │  Element not found     → UI Change / Locator Issue      │     │
│  │  HTTP 500 in logs      → Backend Bug                    │     │
│  │  Timeout + no response → Infrastructure Issue           │     │
│  │  Browser crash         → Environment Issue              │     │
│  │  Test data not found   → Data Setup Issue               │     │
│  │  Auth token expired    → Configuration Issue            │     │
│  │  Script syntax error   → Automation Script Bug          │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  Step 3: Defect Creation                                         │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ For "Application Bug" classifications:                  │     │
│  │   • Generate Jira bug title (concise, descriptive)      │     │
│  │   • Include steps to reproduce (from TC steps)          │     │
│  │   • Attach evidence (screenshot, video, logs)           │     │
│  │   • Assign severity based on test priority              │     │
│  │   • Link to original story                              │     │
│  │   • Set appropriate Jira labels and components          │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  Output: RCA Report + Jira Defects Created                       │
└──────────────────────────────────────────────────────────────────┘
```

---

## Testing Strategy

### 1. RCA Accuracy %

This is the **primary metric** for this agent — did it correctly identify why a test failed?

```
VALIDATION APPROACH:

  1. Create a "failure golden dataset":
     • 50 intentionally failed tests with KNOWN root causes
     • 10 app bugs, 10 locator issues, 10 infra failures, 
       10 data issues, 10 script bugs
  
  2. Run the RCA Agent against all 50 failures
  
  3. Compare agent classification against known truth

  SCORING:
    RCA Accuracy = (Correctly classified failures / Total failures) × 100
    
    Target: >= 80%
    Alert:  < 70%
    Block:  < 60%
```

### 2. False Positive Reduction

A "false positive" in this context means: **the test failed, but there's no actual bug in the application.**

| False Positive Type | Example | Impact | How Agent Should Handle |
|--------------------|---------|--------|------------------------|
| Infra classified as app bug | Timeout due to slow network → filed as "feature broken" | Dev wastes time investigating | Classify as "Infra Issue", don't create Jira bug |
| Flaky test classified as bug | Test passes on retry → initial failure filed as bug | Noise in defect tracker | Check retry results before filing |
| Test data issue as app bug | Test expected user "John" but seed data changed | Misleading defect | Cross-reference test data setup |
| Environment config issue | Wrong base URL → 404 errors → filed as "missing feature" | False alarm | Validate environment config first |

**Target:** False positive rate < 10% of all auto-created defects

### 3. Correct Defect Classification

| Test Priority | Defect Severity | Defect Priority |
|--------------|----------------|-----------------|
| P0 (Blocker) | Critical / Blocker | P0 — Fix immediately |
| P1 (Critical) | Major | P1 — Fix in current sprint |
| P2 (Major) | Normal | P2 — Fix in next sprint |
| P3 (Minor) | Minor | P3 — Fix when capacity allows |

**Validation:** Every auto-created defect must have severity/priority aligned with the test case priority. A P3 test should never create a "Blocker" defect.

---

## Test Cases for This Module

| TC ID | Test Case | Priority | Type |
|-------|-----------|----------|------|
| RCA-001 | Assertion failure → classified as "Application Bug" | P0 | Positive |
| RCA-002 | Element not found → classified as "Locator Issue" | P0 | Positive |
| RCA-003 | HTTP 500 in logs → classified as "Backend Bug" | P0 | Positive |
| RCA-004 | Timeout → classified as "Infrastructure Issue" | P1 | Positive |
| RCA-005 | Browser crash → classified as "Environment Issue" | P1 | Positive |
| RCA-006 | Golden dataset: 50 failures → RCA accuracy >= 80% | P0 | Regression |
| RCA-007 | App bug → Jira defect created with all required fields | P0 | Integration |
| RCA-008 | Infra failure → NO Jira defect created (filtered out) | P0 | Negative |
| RCA-009 | Flaky test (passes on retry) → NOT filed as defect | P1 | False Positive |
| RCA-010 | Evidence captured: screenshot, log, video for each failure | P1 | Completeness |
| RCA-011 | Defect severity matches test priority | P1 | Quality |
| RCA-012 | Duplicate defect detection — same failure doesn't create duplicate Jira ticket | P1 | Deduplication |

---

## Auto-Created Jira Defect — Sample

```
┌────────────────────────────────────────────────────────────────┐
│  JIRA DEFECT (Auto-Created)                                    │
│                                                                │
│  Title: [AUTO] Login fails with valid credentials on Chrome    │
│  Type: Bug                                                     │
│  Priority: P0                                                  │
│  Severity: Critical                                            │
│  Labels: auto-generated, regression, login                     │
│  Component: Authentication                                     │
│  Linked Story: PROJ-123                                        │
│                                                                │
│  Description:                                                  │
│  Automated test TC-PROJ123-AC1-001 failed during execution.    │
│                                                                │
│  Steps to Reproduce:                                           │
│  1. Navigate to /login                                         │
│  2. Enter email: test@example.com                              │
│  3. Enter password: ValidPass@123                              │
│  4. Click Login button                                         │
│                                                                │
│  Expected: Redirect to dashboard with welcome message          │
│  Actual: Error message "Internal Server Error" displayed       │
│                                                                │
│  Root Cause Analysis:                                          │
│  Classification: Backend Bug                                   │
│  Evidence: HTTP 500 response from /api/auth/login              │
│  Server log: NullPointerException in AuthService.java:142      │
│                                                                │
│  Attachments:                                                  │
│  • failure-screenshot.png                                      │
│  • execution-video.mp4                                         │
│  • console-log.txt                                             │
│  • network-trace.har                                           │
│                                                                │
│  Environment: Chrome 120 / Windows 11 / QA Environment         │
│  Execution Date: 2026-02-12 14:30:00 UTC                      │
└────────────────────────────────────────────────────────────────┘
```

---

## Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| RCA Accuracy % | >= 80% | < 70% |
| False Positive Rate | < 10% | > 15% |
| Defect Auto-Creation Success | >= 95% | < 90% |
| Evidence Capture Completeness | >= 98% | < 95% |
| Duplicate Defect Rate | < 5% | > 10% |
| Mean Time to RCA | < 30 seconds per failure | > 60 seconds |
| Correct Severity Assignment | >= 90% | < 80% |

---

## Architect's Notes

1. **RCA is only as good as the evidence** — If logs aren't captured or screenshots fail, the agent is guessing. Evidence capture must be rock-solid.
2. **Deduplication is critical** — Running the same suite daily can create 50 identical defects if dedup logic isn't in place. Use fingerprinting (failure point + error message + test ID) to detect duplicates.
3. **Human review for high-severity defects** — Auto-created P0 defects should trigger a notification to the QA lead for confirmation before being assigned to developers.
4. **Track RCA drift** — If the accuracy drops over time, it likely means new failure patterns have emerged that the classification model hasn't learned yet. Retrain regularly.

---

*This agent closes the testing loop — from execution to analysis to action. Without accurate RCA, test automation is just generating noise. With it, every failure becomes a precisely targeted improvement.*
