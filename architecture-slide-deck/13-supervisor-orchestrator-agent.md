# Slide 13 — Supervisor / Orchestrator Agent

## The Brain That Makes the System Truly Autonomous

---

## Module Overview

The Supervisor Agent is the **central nervous system** of the platform. It coordinates all specialized agents, makes system-level decisions, manages retries and escalations, and ensures the pipeline operates autonomously end to end.

> **Key Line:** "This agent makes the system truly autonomous."

Without the Supervisor, we have a collection of independent tools. With it, we have an **intelligent, self-governing testing system**.

---

## Responsibilities

| Responsibility | What It Does | Why It Matters |
|---------------|-------------|----------------|
| **Coordinate Agents** | Determine execution order, pass outputs between agents, manage dependencies | Agents don't know about each other — the Supervisor connects them |
| **Decide Next Action** | Based on agent outputs + confidence scores + metrics, decide what to do next | Intelligence at the system level, not just individual agent level |
| **Trigger Retries or Escalation** | When an agent fails or produces low-confidence output, decide: retry, skip, or escalate to human | Prevents pipeline from stalling on recoverable errors |

---

## Orchestration Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                      SUPERVISOR AGENT                                 │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │                    DECISION ENGINE                          │      │
│  │                                                            │      │
│  │  INPUT: Agent outputs + Confidence scores + System state   │      │
│  │                                                            │      │
│  │  RULES:                                                    │      │
│  │  ┌──────────────────────────────────────────────────────┐  │      │
│  │  │ IF agent.confidence >= 0.85 → PROCEED to next agent  │  │      │
│  │  │ IF agent.confidence 0.70-0.84 → PROCEED with flag    │  │      │
│  │  │ IF agent.confidence < 0.70 → ESCALATE to human       │  │      │
│  │  │ IF agent.error = timeout → RETRY (max 3)             │  │      │
│  │  │ IF agent.error = fatal → SKIP + ALERT                │  │      │
│  │  │ IF all agents complete → TRIGGER metrics + report     │  │      │
│  │  └──────────────────────────────────────────────────────┘  │      │
│  └────────────────────────────────────────────────────────────┘      │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │                 ORCHESTRATION MAP                           │      │
│  │                                                            │      │
│  │  Jira Ingestion ──▶ Requirement Agent ──▶ Test Case Agent  │      │
│  │       │                    │                     │          │      │
│  │       │              [confidence?]          [confidence?]   │      │
│  │       │                    │                     │          │      │
│  │       ▼                    ▼                     ▼          │      │
│  │  Script Agent ────▶ Execution Engine ───▶ RCA Agent        │      │
│  │       │                    │                     │          │      │
│  │  [compiles?]          [passes?]           [classified?]    │      │
│  │       │                    │                     │          │      │
│  │       ▼                    ▼                     ▼          │      │
│  │  Metrics Framework ◀───── Feedback Loop ◀─── Jira Update  │      │
│  └────────────────────────────────────────────────────────────┘      │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │                ESCALATION MANAGER                           │      │
│  │                                                            │      │
│  │  Human-in-Loop Triggers:                                   │      │
│  │    • Low confidence on critical story (P0)                 │      │
│  │    • Multiple agent failures in sequence                   │      │
│  │    • Hallucination detected in generated tests             │      │
│  │    • Auto-created defect has severity "Blocker"            │      │
│  │    • System health metric breaches alert threshold         │      │
│  │                                                            │      │
│  │  Escalation Channels:                                      │      │
│  │    • Slack notification to QA lead                         │      │
│  │    • Email for P0 defects                                  │      │
│  │    • Jira ticket for agent failures                        │      │
│  │    • PagerDuty for system outages                          │      │
│  └────────────────────────────────────────────────────────────┘      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Testing Strategy

### 1. Decision Accuracy

The Supervisor makes decisions constantly. Each decision must be validated:

```
DECISION TESTING APPROACH:

  Create a "decision golden dataset":
  
  Scenario 1: Agent returns confidence 0.92 
    → Expected decision: PROCEED
    → Verify: Supervisor sends output to next agent
  
  Scenario 2: Agent returns confidence 0.65
    → Expected decision: ESCALATE to human
    → Verify: Human review queue receives the item
  
  Scenario 3: Agent returns timeout error
    → Expected decision: RETRY (attempt 1 of 3)
    → Verify: Agent re-invoked with same input
  
  Scenario 4: Agent returns timeout error (3rd time)
    → Expected decision: SKIP + ALERT
    → Verify: Pipeline continues, alert sent to Slack
  
  Scenario 5: All agents complete successfully
    → Expected decision: TRIGGER metrics calculation + report
    → Verify: Metrics updated, report generated
```

**Scoring:**
```
Decision Accuracy = (Correct decisions / Total decisions) × 100
Target: >= 95%
Alert:  < 90%
```

### 2. Retry Threshold Validation

```
RETRY RULES TO VALIDATE:

  ┌────────────────────────────────────────────────────────────┐
  │  Error Type          Max Retries   Backoff        Timeout  │
  │  ──────────────────────────────────────────────────────── │
  │  Agent timeout            3        Exponential     30s ea  │
  │  Network error            3        Exponential     15s ea  │
  │  Rate limit (429)         5        Retry-After     var     │
  │  Auth failure             1        Immediate       N/A     │
  │  Data validation error    0        N/A             N/A     │
  │  Compilation error        2        Fixed (10s)     N/A     │
  └────────────────────────────────────────────────────────────┘

  TEST CASES:
  • Verify retry count never exceeds max for each error type
  • Verify backoff timing is correct (exponential: 2s, 4s, 8s)
  • Verify retry-after header is respected for 429 errors
  • Verify no retry for validation errors (retrying won't help)
```

### 3. Human-in-Loop Triggers

```
SCENARIO → EXPECTED TRIGGER → CHANNEL

P0 story with confidence 0.65
  → Human review required → Slack + Email to QA Lead

3 consecutive agent failures
  → System health alert → PagerDuty

Hallucination detected (>10% rate)
  → Pipeline pause + review → Slack + Jira ticket

Auto-created Blocker defect
  → Confirmation required → Email to QA Lead + Dev Lead

Metrics breach alert threshold
  → Dashboard alert + notification → Slack + Grafana

TESTING APPROACH:
  Simulate each scenario → Verify correct channel receives alert
  with correct content within expected latency (<30 seconds)
```

---

## Test Cases

| TC ID | Test Case | Priority | Type |
|-------|-----------|----------|------|
| SUP-001 | High confidence agent output → Supervisor proceeds to next agent | P0 | Decision |
| SUP-002 | Low confidence output → Supervisor escalates to human review | P0 | Decision |
| SUP-003 | Agent timeout → Supervisor retries (up to max) | P0 | Retry |
| SUP-004 | Max retries exceeded → Supervisor skips and alerts | P0 | Retry |
| SUP-005 | All agents complete → Supervisor triggers metrics + report | P0 | Orchestration |
| SUP-006 | Agent outputs passed correctly between agents (no data loss) | P0 | Data Flow |
| SUP-007 | Concurrent stories → each orchestrated independently | P1 | Isolation |
| SUP-008 | Hallucination alert → pipeline paused, human notified | P1 | Safety |
| SUP-009 | P0 blocker defect → immediate notification to leads | P1 | Escalation |
| SUP-010 | Decision accuracy across 100 scenarios → >= 95% | P0 | Regression |
| SUP-011 | Supervisor handles 20 concurrent pipelines without resource exhaustion | P2 | Scalability |
| SUP-012 | Supervisor state survives restart (in-flight pipelines resume) | P1 | Resilience |

---

## Supervisor State Machine

```
┌─────────────────────────────────────────────────────────────────────┐
│                  PIPELINE STATE MACHINE                              │
│                                                                     │
│  ┌──────────┐    ┌───────────┐    ┌──────────┐    ┌────────────┐  │
│  │ INGESTING│───▶│INTERPRETING│───▶│DESIGNING │───▶│SCRIPTING   │  │
│  │          │    │           │    │          │    │            │  │
│  └──────────┘    └───────────┘    └──────────┘    └────────────┘  │
│       │               │               │               │            │
│       │          ┌─────────┐     ┌─────────┐     ┌─────────┐     │
│       │          │ HUMAN   │     │ HUMAN   │     │ RETRY   │     │
│       │          │ REVIEW  │     │ REVIEW  │     │         │     │
│       │          └─────────┘     └─────────┘     └─────────┘     │
│       ▼                                                            │
│  ┌──────────┐    ┌───────────┐    ┌──────────┐    ┌────────────┐  │
│  │EXECUTING │───▶│ ANALYZING │───▶│REPORTING │───▶│ COMPLETE   │  │
│  │          │    │  (RCA)    │    │          │    │            │  │
│  └──────────┘    └───────────┘    └──────────┘    └────────────┘  │
│       │               │                                            │
│  ┌─────────┐     ┌─────────┐                                      │
│  │ RETRY   │     │ ESCALATE│                                      │
│  └─────────┘     └─────────┘                                      │
│                                                                     │
│  Terminal States: COMPLETE, FAILED, CANCELLED                       │
└─────────────────────────────────────────────────────────────────────┘
```

Every state transition is logged, every decision has an audit trail, and the state can be inspected at any time for any pipeline.

---

## Metrics for the Supervisor

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Decision Accuracy | >= 95% | < 90% |
| Avg Pipeline Completion Time | < 15 minutes per story | > 30 minutes |
| Escalation Rate | < 15% of stories | > 25% |
| Retry Success Rate | >= 60% | < 40% |
| Pipeline Completion Rate | >= 95% | < 90% |
| Human Response Time (after escalation) | < 2 hours | > 4 hours |
| Concurrent Pipeline Capacity | >= 20 | < 10 |

---

## Architect's Notes

1. **The Supervisor is a single point of coordination, NOT a single point of failure** — If the Supervisor goes down, in-flight pipelines should be recoverable from persisted state.
2. **Decision logging is non-negotiable** — Every decision ("proceed", "retry", "escalate") must be logged with timestamp, input state, confidence scores, and rationale.
3. **Test the Supervisor with chaos** — Kill it mid-pipeline, restart it, verify it resumes correctly. Feed it conflicting signals and verify it makes the conservative choice.
4. **Escalation fatigue is real** — If the Supervisor escalates too often, humans ignore it. Monitor escalation rate and tune thresholds to keep it meaningful.

---

*The Supervisor Agent transforms a collection of independent tools into a coordinated, autonomous system. Its decision accuracy directly determines whether the platform is trustworthy or chaotic.*
