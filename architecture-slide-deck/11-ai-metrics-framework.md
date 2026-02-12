# Slide 11 — Module 7: AI Metrics Framework

## Measuring AI Quality — Not Assuming It

---

## Module Overview

The AI Metrics Framework is a dedicated measurement system that **quantifies the quality of every AI-driven decision** in the platform — from requirement understanding to test case generation to root cause analysis.

> **Architect's Core Principle:** "AI quality is measured, not assumed."

Without this framework, we're operating on blind trust. With it, we have **empirical evidence** of whether the AI is helping or hallucinating.

---

## Why a Dedicated AI Metrics Layer?

Traditional software metrics (code coverage, pass/fail rates) don't capture AI quality. AI systems introduce a fundamentally different category of risk:

| Traditional Software Risk | AI-Specific Risk |
|---------------------------|------------------|
| Code has a bug (deterministic) | Model output is wrong (probabilistic) |
| Function returns wrong value | LLM hallucinates non-existent feature |
| Integration breaks on deploy | Prompt change silently degrades quality |
| Test fails consistently | Test is flaky because AI output varies |

**You can't manage what you don't measure. This framework makes AI behavior observable and accountable.**

---

## AI Metrics Tracked

### 1. Requirement Accuracy

```
WHAT IT MEASURES:
  How accurately the Requirement Understanding Agent extracts and 
  interprets acceptance criteria from Jira stories.

HOW WE MEASURE:
  Compare agent output against golden dataset (human-verified extractions)

FORMULA:
  Requirement Accuracy = (Matching Extractions / Total Expected Extractions) × 100

TARGET: >= 85%
ALERT:  < 75%

TRACKING FREQUENCY: Per story processed + daily aggregate + weekly trend
```

### 2. Test Coverage Score

```
WHAT IT MEASURES:
  How thoroughly the Test Case Design Agent covers all testable 
  scenarios for a given set of requirements.

HOW WE MEASURE:
  For each story:
    • Count total ACs
    • Count ACs with positive test cases
    • Count ACs with negative test cases
    • Count ACs with edge case coverage

FORMULA:
  Coverage Score = Weighted average of:
    (Positive coverage × 0.4) + (Negative coverage × 0.35) + (Edge coverage × 0.25)

TARGET: >= 85%
ALERT:  < 75%

DIMENSIONS:
  ┌─────────────────────────────────────────────────────┐
  │  Positive Path Coverage    ████████████████░░  90%  │
  │  Negative Path Coverage    ██████████████░░░░  80%  │
  │  Edge Case Coverage        ██████████░░░░░░░░  65%  │
  │  Business Rule Coverage    ████████████░░░░░░  75%  │
  │                                                     │
  │  Weighted Overall:         ████████████████░░  82%  │
  └─────────────────────────────────────────────────────┘
```

### 3. Hallucination Rate

```
WHAT IT MEASURES:
  The percentage of AI-generated content that has NO basis in the 
  input data — the agent invented something that doesn't exist.

EXAMPLES OF HALLUCINATION:
  ✗ Test case for "social login" when story only mentions email login
  ✗ Business rule about "admin access" when story is about user profile
  ✗ Acceptance criterion about "mobile responsive" when story is desktop-only

HOW WE DETECT:
  For each AI output item:
    1. Trace back to source (story text, AC, description)
    2. If no source mapping exists → hallucination
    3. If source mapping is a stretch (low similarity) → potential hallucination

FORMULA:
  Hallucination Rate = (Hallucinated items / Total generated items) × 100

TARGET: < 5%
ALERT:  > 8%
BLOCK:  > 15% (pipeline stops, human review required)
```

### 4. Decision Confidence

```
WHAT IT MEASURES:
  How confident each agent is in its own output — a self-reported 
  score that enables threshold-based routing.

HOW IT WORKS:
  Each agent emits a confidence score (0.0 to 1.0) with every output.
  
  Routing Rules:
    Confidence >= 0.85  →  Auto-proceed (no human review)
    Confidence 0.70-0.84 →  Flag for optional review
    Confidence < 0.70   →  BLOCK — require human approval

WHY IT MATTERS:
  Confidence calibration tells us if the agent "knows what it doesn't know."
  An overconfident agent (always reports 0.95) that frequently makes errors 
  is MORE dangerous than an underconfident one.

CALIBRATION TEST:
  Plot confidence vs actual accuracy.
  Ideal: high confidence → high accuracy, low confidence → lower accuracy.
  Problem: if high confidence often correlates with errors → miscalibrated model.
```

---

## Metrics Dashboard View

```
┌──────────────────────────────────────────────────────────────────────┐
│                    AI METRICS DASHBOARD                               │
│                    Date: 2026-02-12 | Sprint: 24                     │
│                                                                      │
│  ┌─────────────────────┐  ┌─────────────────────┐                   │
│  │ REQ ACCURACY        │  │ TEST COVERAGE       │                   │
│  │      87.3%          │  │      83.6%          │                   │
│  │  ▲ +2.1% vs last wk│  │  ▲ +1.5% vs last wk│                   │
│  │  Target: 85% ✓      │  │  Target: 85% ⚠     │                   │
│  └─────────────────────┘  └─────────────────────┘                   │
│                                                                      │
│  ┌─────────────────────┐  ┌─────────────────────┐                   │
│  │ HALLUCINATION RATE  │  │ AVG CONFIDENCE      │                   │
│  │       3.2%          │  │      0.88           │                   │
│  │  ▼ -0.8% vs last wk│  │  ▲ +0.02 vs last wk│                   │
│  │  Target: <5% ✓      │  │  Target: >0.85 ✓   │                   │
│  └─────────────────────┘  └─────────────────────┘                   │
│                                                                      │
│  TREND (Last 8 Weeks):                                              │
│                                                                      │
│  Req Accuracy:  82 → 83 → 84 → 85 → 86 → 86 → 85 → 87   ▲        │
│  Coverage:      78 → 79 → 80 → 81 → 82 → 83 → 83 → 84   ▲        │
│  Hallucination: 7  → 6  → 6  → 5  → 5  → 4  → 4  → 3    ▼ (good) │
│  Confidence:    .82→.83→.84→.85→.86→.87→.87→.88           ▲        │
│                                                                      │
│  Status: ALL METRICS WITHIN TARGET RANGE                            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Testing the Metrics Framework Itself

The metrics framework must be tested to ensure it's reporting accurately:

| TC ID | Test Case | Priority |
|-------|-----------|----------|
| MET-001 | Inject known-good AI output → accuracy metric should be 100% | P0 |
| MET-002 | Inject known-bad AI output (50% hallucinated) → hallucination rate shows 50% | P0 |
| MET-003 | Inject mixed results → coverage score calculates weighted average correctly | P0 |
| MET-004 | Confidence score of 0.60 → triggers human review routing | P1 |
| MET-005 | All metrics displayed correctly on dashboard (no stale data) | P1 |
| MET-006 | Trend calculation over 8 data points → correct moving average | P2 |
| MET-007 | Alert triggers when metric breaches threshold | P1 |
| MET-008 | Metrics survive agent restart (persisted, not in-memory only) | P1 |

---

## Architect's View

```
"The AI Metrics Framework is the CONSCIENCE of the platform.

Without it:
  • We don't know if AI quality is improving or degrading
  • We can't detect prompt regressions until users complain
  • We can't justify trust in AI-generated tests
  • We can't comply with AI governance requirements

With it:
  • Every AI decision has a measurable quality score
  • Regressions are detected within hours, not weeks
  • Trust is earned through data, not faith
  • Compliance is built in, not bolted on"
```

---

## Integration Points

| Source | Data Sent to Metrics Framework |
|--------|-------------------------------|
| Requirement Agent | Extraction results + confidence scores |
| Test Case Agent | Generated TCs + coverage reports + confidence scores |
| Script Agent | Compilation results + compliance scores |
| RCA Agent | Classification results + accuracy feedback |
| Golden Datasets | Ground truth for accuracy calculations |
| Execution Engine | Pass/fail data for correlation with AI quality |

---

*This framework transforms the platform from "AI that we hope works" to "AI that we can prove works." Every number on this dashboard is backed by a validation methodology, a golden dataset, and a trend line.*
