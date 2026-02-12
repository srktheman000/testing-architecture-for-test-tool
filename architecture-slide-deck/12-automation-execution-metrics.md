# Slide 12 — Automation Execution Metrics

## Measuring Runtime Performance & Stability

---

## Module Overview

While Slide 11 covered **AI quality metrics**, this slide focuses on **execution quality metrics** — the operational health of the automation pipeline once tests are actually running.

> **Architect's Distinction:** AI metrics tell us "Are we generating the right tests?" Execution metrics tell us "Are those tests running reliably?"

Both are required. A perfectly generated test case that fails due to flaky infrastructure still produces zero value.

---

## Execution Metrics

### 1. Pass / Fail Rate

```
WHAT IT MEASURES:
  The fundamental outcome metric — how many tests pass vs fail.

FORMULA:
  Pass Rate = (Passed Tests / Total Executed Tests) × 100
  Fail Rate = (Failed Tests / Total Executed Tests) × 100

BREAKDOWN:
  Total Executed:  500
  ├── Passed:      420  (84%)
  ├── Failed:       65  (13%)  ← FURTHER CLASSIFY:
  │   ├── App Bug:       40  (61.5% of failures)
  │   ├── Infra Issue:   12  (18.5% of failures)
  │   ├── Script Bug:     8  (12.3% of failures)
  │   └── Data Issue:     5  (7.7% of failures)
  └── Skipped:      15  (3%)

TARGET: Pass Rate >= 90%
ALERT:  Pass Rate < 85%

CRITICAL INSIGHT:
  Raw pass/fail is meaningless without failure classification.
  A 70% pass rate caused by infra issues is NOT the same as 
  a 70% pass rate caused by app bugs.
```

### 2. Retry Recovery Rate

```
WHAT IT MEASURES:
  Of tests that failed on first attempt, how many recovered (passed) on retry.

WHY IT MATTERS:
  High retry recovery = failures were transient (infra, timing)
  Low retry recovery = failures are real (app bugs, data issues)

FORMULA:
  Retry Recovery Rate = (Tests Passed on Retry / Tests Retried) × 100

EXAMPLE:
  65 tests failed initially
  40 tests were retried (retry policy criteria met)
  28 tests passed on retry
  
  Recovery Rate = (28 / 40) × 100 = 70%

TARGET: >= 60%
ALERT:  < 40%

INTERPRETATION:
  If Recovery > 80% → Too many flaky tests. Investigate root causes.
  If Recovery < 30% → Retries aren't helping. Review retry policy.
  If Recovery 40-70% → Healthy balance. Monitor trend.
```

### 3. Execution Time

```
WHAT IT MEASURES:
  How long tests take to run — individually and as suites.

METRICS:
  ┌─────────────────────────────────────────────────────────────┐
  │  EXECUTION TIME BREAKDOWN                                    │
  │                                                             │
  │  Individual Test:                                           │
  │    P50 (median):    18 seconds                              │
  │    P90:             42 seconds                              │
  │    P99:             95 seconds                              │
  │    Max:            180 seconds                              │
  │                                                             │
  │  Full Suite (500 tests):                                    │
  │    Sequential:   2.5 hours (baseline)                       │
  │    Parallel (10x): 18 minutes (actual)                      │
  │    Parallel efficiency: 83%                                 │
  │                                                             │
  │  Pipeline Impact:                                           │
  │    Smoke suite (P0):     4 minutes                          │
  │    Regression suite:     18 minutes                         │
  │    Full cross-browser:   45 minutes                         │
  └─────────────────────────────────────────────────────────────┘

TARGETS:
  Individual test P95: < 60 seconds
  Smoke suite: < 5 minutes (pipeline gate)
  Full regression: < 30 minutes
```

### 4. Parallel Efficiency

```
WHAT IT MEASURES:
  How effectively the engine utilizes parallel workers.

FORMULA:
  Parallel Efficiency = (Sequential Duration / (Parallel Duration × Worker Count)) × 100

EXAMPLE:
  Sequential: 2.5 hours = 150 minutes
  Parallel (10 workers): 18 minutes
  
  Ideal parallel: 150 / 10 = 15 minutes
  Actual parallel: 18 minutes
  
  Efficiency = (15 / 18) × 100 = 83%

WHY NOT 100%?
  • Startup/teardown overhead per worker
  • Uneven test distribution (some tests take longer)
  • Shared resource contention (DB, API rate limits)
  • Worker initialization time

TARGET: >= 70%
ALERT:  < 50%
```

---

## Stability Metrics

### 5. Flaky Test Reduction

```
WHAT IS A FLAKY TEST?
  A test that produces different results (pass/fail) on the same code,
  same environment, without any application change.

HOW WE DETECT:
  Run the same suite 3 times. If a test produces different results 
  across runs → it's flaky.

  OR: Track historical results. If a test alternates pass↔fail over 
  the last 10 runs without code changes → flaky.

METRICS:
  ┌────────────────────────────────────────────────┐
  │  FLAKINESS DASHBOARD                            │
  │                                                │
  │  Total Tests:         500                      │
  │  Flaky Tests:          23  (4.6%)              │
  │                                                │
  │  Top Flaky Tests:                              │
  │  1. checkout-flow.spec.ts    (7/10 flips)      │
  │  2. search-filter.spec.ts   (5/10 flips)       │
  │  3. notification.spec.ts    (4/10 flips)        │
  │                                                │
  │  Flaky Root Causes:                            │
  │  • Timing/Race conditions:     45%             │
  │  • Test data dependency:       25%             │
  │  • Environment instability:    20%             │
  │  • Non-deterministic ordering: 10%             │
  │                                                │
  │  Trend: 8% → 6% → 5% → 4.6%  ▼ (improving)   │
  └────────────────────────────────────────────────┘

TARGET: < 5% flaky tests
ALERT:  > 8%
GOAL:   Reduce by 20% each month until < 2%
```

### 6. Auto-Heal Success %

```
WHAT IT MEASURES:
  When the Script Agent detects a broken locator or changed flow 
  and attempts to auto-heal, how often does the heal succeed?

HEAL SCENARIOS:
  ┌──────────────────────────────────────────────────────────────┐
  │  SCENARIO                    HEAL ACTION        SUCCESS?     │
  │  ──────────────────────────────────────────────────────────  │
  │  Button ID changed           Find by text         ✓         │
  │  Form field renamed          Find by label        ✓         │
  │  Dropdown became autocomplete Detect new pattern   ✓         │
  │  Entire page restructured    Cannot find element   ✗         │
  │  New modal overlay           Detect and dismiss     ✓         │
  │  Login flow changed          Regenerate script     ✓         │
  │  URL structure changed       Update navigation     ✓         │
  │  Component library swapped   Too many changes      ✗         │
  └──────────────────────────────────────────────────────────────┘

FORMULA:
  Auto-Heal Success % = (Successful heals / Total heal attempts) × 100

TARGET: >= 70%
ALERT:  < 50%
```

---

## Metrics Correlation Analysis

The real power of metrics comes from **correlating** AI quality with execution quality:

```
CORRELATION INSIGHTS:

  High AI Accuracy + Low Pass Rate = Environment/Infra problem
    → Tests are well-designed but failing due to external issues
    → Action: Fix environment, not tests

  Low AI Accuracy + High Pass Rate = Coverage Gap
    → Tests pass but aren't testing the right things
    → Action: Improve AI prompts, expand golden datasets

  High Hallucination + High Pass Rate = False Confidence  
    → AI-invented scenarios happen to pass (coincidence)
    → Action: Audit test cases against actual requirements

  Low Confidence + Low Pass Rate = Expected
    → Agent flagged low confidence and tests indeed failed
    → Action: Route low-confidence items to human review
```

---

## Test Cases for Metrics Accuracy

| TC ID | Test Case | Priority |
|-------|-----------|----------|
| EM-001 | 100 passed, 0 failed → pass rate shows 100% | P0 |
| EM-002 | 50 passed, 50 failed → pass rate shows 50% | P0 |
| EM-003 | 10 retried, 7 passed on retry → recovery rate shows 70% | P1 |
| EM-004 | Parallel 10 workers, 100 tests → efficiency calculated correctly | P1 |
| EM-005 | Same test flips 5 times in 10 runs → flagged as flaky | P1 |
| EM-006 | 20 heal attempts, 15 successful → auto-heal shows 75% | P1 |
| EM-007 | Dashboard displays all metrics with correct values | P1 |
| EM-008 | Alert fires when pass rate drops below 85% | P1 |
| EM-009 | Historical trend shows 8-week progression correctly | P2 |
| EM-010 | Metrics persist across system restart | P1 |

---

## Combined Metrics Dashboard

```
┌──────────────────────────────────────────────────────────────────────┐
│              EXECUTION METRICS DASHBOARD                             │
│              Sprint 24 | Week 6                                     │
│                                                                      │
│  EXECUTION                          STABILITY                       │
│  ┌─────────────────────────┐       ┌─────────────────────────┐     │
│  │ Pass Rate:    88.4%     │       │ Flaky Tests:   4.6%     │     │
│  │ Fail Rate:    8.6%      │       │ Flaky Trend:   ▼ -1.4%  │     │
│  │ Skip Rate:    3.0%      │       │ Auto-Heal:     73%      │     │
│  └─────────────────────────┘       └─────────────────────────┘     │
│                                                                      │
│  PERFORMANCE                        RECOVERY                        │
│  ┌─────────────────────────┐       ┌─────────────────────────┐     │
│  │ Avg Time/Test: 22s      │       │ Retry Recovery:  68%    │     │
│  │ Suite Time:    18min     │       │ Script Regen:    82%    │     │
│  │ Parallel Eff:  83%      │       │ Heal Attempts:   45     │     │
│  └─────────────────────────┘       └─────────────────────────┘     │
│                                                                      │
│  HEALTH STATUS: ████████████████████████░░░░  88% HEALTHY           │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Architect's Notes

1. **Metrics must be actionable** — A metric nobody acts on is a vanity metric. Every metric above has an associated action when it breaches threshold.
2. **Trend matters more than snapshot** — A pass rate of 85% that's been climbing for 4 weeks is better than 90% that's been declining.
3. **Flakiness is a team health indicator** — Rising flakiness usually means environment issues or rushed test development, not bad tooling.
4. **Auto-heal is a feature, not a fix** — Self-healing buys time but doesn't replace proper locator strategies. If heal rate is too high, root-cause the locator fragility.

---

*Execution metrics are the operational heartbeat of the platform. Combined with AI metrics (Slide 11), they provide a complete picture of testing system health — from intelligence to reliability.*
