# Slide 9 — Module 5: Execution Engine

## Running Tests at Scale, Reliably

---

## Module Overview

The Execution Engine takes validated automation scripts and **runs them against real applications** across multiple browsers, environments, and configurations — managing parallelism, retries, and CI/CD integration.

> **Architect's Focus:** This is where theory meets reality. The Execution Engine must be as reliable as the tests it runs — infrastructure failures should never be confused with application bugs.

---

## Responsibilities

| Responsibility | What It Does | Why It Matters |
|---------------|-------------|----------------|
| **Execute Tests** | Run Playwright/Selenium scripts against target applications | This is the actual testing — everything else is preparation |
| **Manage Environments** | Configure browser versions, OS targets, test data, base URLs per environment | Same test must run on dev, QA, staging, and pre-prod |
| **Integrate CI/CD** | Trigger from pipelines (Jenkins, GitHub Actions), report results back | Testing must be part of the delivery pipeline, not a separate activity |

---

## Execution Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         EXECUTION ENGINE                                  │
│                                                                          │
│  ┌────────────────────┐                                                  │
│  │   SCRIPT QUEUE     │  Incoming scripts → Priority queue               │
│  │   (Priority-based) │  P0 scripts execute first                        │
│  └────────┬───────────┘                                                  │
│           │                                                              │
│           ▼                                                              │
│  ┌────────────────────────────────────────────────────┐                  │
│  │              EXECUTION ORCHESTRATOR                 │                  │
│  │                                                    │                  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │                  │
│  │  │ Worker 1 │  │ Worker 2 │  │ Worker N │        │                  │
│  │  │ Chrome   │  │ Firefox  │  │ Edge     │        │                  │
│  │  └──────────┘  └──────────┘  └──────────┘        │                  │
│  │                                                    │                  │
│  │  Environment Config: baseURL, auth tokens, DB seed │                  │
│  └────────────────────┬───────────────────────────────┘                  │
│                       │                                                  │
│           ┌───────────┼───────────┐                                      │
│           ▼           ▼           ▼                                      │
│  ┌──────────────┐ ┌────────┐ ┌──────────┐                               │
│  │  Screenshots │ │  Logs  │ │  Videos  │  Evidence Capture              │
│  └──────────────┘ └────────┘ └──────────┘                               │
│                                                                          │
│  ┌────────────────────────────────────────────────────┐                  │
│  │              RESULT AGGREGATOR                      │                  │
│  │  Collect results from all workers → unified report  │                  │
│  └────────────────────────────────────────────────────┘                  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Testing Strategy

### 1. Parallel Execution

```
SCENARIO: 50 test scripts need to run

SEQUENTIAL (Traditional):
  50 scripts × 30 seconds each = 25 minutes total
  
PARALLEL (This Engine):
  50 scripts ÷ 10 workers = 5 batches × 30 seconds = 2.5 minutes total
  
KEY VALIDATION POINTS:
  ✓ No data leakage between parallel workers (test isolation)
  ✓ Each worker has its own browser instance (no shared state)
  ✓ Test data is isolated per worker (no conflicts on shared DB)
  ✓ Results from all workers are correctly aggregated
  ✓ Worker failure doesn't block other workers
```

**Test Cases for Parallelism:**

| TC ID | Test Case | What We Validate |
|-------|-----------|------------------|
| EX-PAR-001 | Run 10 scripts in parallel | All 10 complete, no data mixing |
| EX-PAR-002 | One worker crashes mid-execution | Other workers unaffected, crash is logged |
| EX-PAR-003 | All workers finish at different times | Results aggregated only after all complete |
| EX-PAR-004 | Shared database with parallel tests | Isolation via transactions or test-specific data |

### 2. Retry & Timeout Handling

```
RETRY POLICY:

  Failure Type          Action                  Max Retries   Backoff
  ─────────────────────────────────────────────────────────────────────
  Element not found     Retry with extended wait     2        Linear (5s, 10s)
  Network timeout       Retry with same config       3        Exponential (2s, 4s, 8s)
  Browser crash         Restart browser + retry      2        Fixed (10s)
  Assertion failure     NO retry (real failure)       0        N/A
  Auth token expired    Refresh token + retry         1        Immediate
  
TIMEOUT THRESHOLDS:

  Page load:       30 seconds (configurable per environment)
  Element wait:    10 seconds
  API response:    15 seconds
  Full test:       5 minutes (kill if exceeded)
  Full suite:      60 minutes (alert if exceeded)
```

### 3. Infrastructure Failure Simulation (Chaos Testing)

| Simulation | How We Do It | What We Validate |
|-----------|-------------|------------------|
| Browser crash | Kill browser process mid-test | Partial results saved, test marked as "Infra Failure" (not "App Bug") |
| Network disconnect | Throttle network to 0 | Timeout triggered, retry attempted, clear error logged |
| Disk full | Fill temp directory before screenshot capture | Error handled gracefully, no silent data loss |
| Memory pressure | Limit container memory | OOM detected, test stopped cleanly, results preserved |
| Grid node unavailable | Remove a Selenium Grid node mid-suite | Queue redistributes to available nodes |

---

## Test Cases for This Module

| TC ID | Test Case | Priority | Type |
|-------|-----------|----------|------|
| EX-001 | Execute single script on Chrome — passes | P0 | Positive |
| EX-002 | Execute same script on Chrome, Firefox, Edge — all pass | P0 | Cross-Browser |
| EX-003 | Execute 50 scripts in parallel — no data mixing | P0 | Parallelism |
| EX-004 | Script fails on assertion — marked as "Failed" with correct step | P0 | Negative |
| EX-005 | Script times out — retry triggered, then marked as timed out | P1 | Timeout |
| EX-006 | Browser crashes mid-test — partial results preserved | P1 | Chaos |
| EX-007 | Network failure during execution — retry with backoff | P1 | Chaos |
| EX-008 | All tests pass — report generated with correct counts | P0 | Integration |
| EX-009 | Mixed results (pass/fail/skip) — all states correctly reported | P0 | Integration |
| EX-010 | CI/CD trigger — pipeline starts execution, results reported back | P1 | CI/CD |
| EX-011 | Environment switch (QA → Staging) — same scripts, different config | P1 | Environment |
| EX-012 | 200+ step script — executes without memory issues | P2 | Scalability |

---

## Metrics

| Metric | Formula | Target | Alert Threshold |
|--------|---------|--------|-----------------|
| **Execution Success Rate** | (passed tests / total executed) × 100 | >= 90% | < 85% |
| **Flakiness %** | (tests that flip pass↔fail on retry / total tests) × 100 | < 5% | > 10% |
| **Infra Failure Rate** | (infra-caused failures / total failures) × 100 | < 10% | > 20% |
| **Retry Recovery Rate** | (tests that pass on retry / tests that were retried) × 100 | >= 60% | < 40% |
| **Parallel Efficiency** | (sequential time / actual parallel time) × 100 | >= 70% | < 50% |
| **Avg Execution Time** | Mean time per test script | < 45 seconds | > 90 seconds |
| **Suite Completion Rate** | (suites completed / suites started) × 100 | >= 98% | < 95% |

---

## CI/CD Integration Points

```
┌────────────────────────────────────────────────────────┐
│                CI/CD PIPELINE INTEGRATION               │
│                                                        │
│  Code Commit                                           │
│      │                                                 │
│      ▼                                                 │
│  Build + Unit Tests                                    │
│      │                                                 │
│      ▼                                                 │
│  Deploy to QA Environment                              │
│      │                                                 │
│      ▼                                                 │
│  ┌──────────────────────────────┐                      │
│  │  EXECUTION ENGINE TRIGGERED  │◀── Webhook / API     │
│  │  • Smoke suite (P0 tests)   │                      │
│  │  • Results → Pipeline gate  │                      │
│  └──────────────┬───────────────┘                      │
│                 │                                       │
│        Pass?    ├── Yes → Deploy to Staging             │
│                 └── No  → Block + Alert + Jira Defect   │
│                                                        │
│  Nightly:                                              │
│  ┌──────────────────────────────┐                      │
│  │  FULL REGRESSION SUITE      │◀── Scheduled          │
│  │  • All P0-P2 test cases     │                      │
│  │  • Cross-browser matrix     │                      │
│  │  • Results → Dashboard      │                      │
│  └──────────────────────────────┘                      │
└────────────────────────────────────────────────────────┘
```

---

## Architect's Notes

1. **Distinguish infra failures from app failures** — A test that fails because Chrome crashed is NOT a bug in the application. The engine must classify failure types accurately.
2. **Flakiness is a system health metric** — Rising flakiness often indicates environment instability, not test quality issues. Track trends, not just snapshots.
3. **Parallel execution requires data isolation** — Two tests modifying the same DB row in parallel will produce non-deterministic results. Use test-specific data or transaction isolation.
4. **Timeout values are environment-specific** — QA (slow infra) needs longer timeouts than pre-prod (prod-like infra). Externalize all timing configs.

---

*The Execution Engine is the proving ground. Everything upstream is preparation; everything downstream is analysis. This module must run reliably at scale, every time, in every environment.*
