# Slide 3 — High-Level Architecture

## System Topology & Layer Breakdown

---

## Architecture Overview

The platform is organized into **five distinct layers**, each independently testable, deployable, and observable:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   LAYER 5: CONTROL PLANE (Supervisor / Orchestrator Agent)                 │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │  Coordinates all agents • Decides next action • Triggers retries │     │
│   │  Manages human-in-loop escalation • Monitors system health       │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│   LAYER 4: ANALYSIS & METRICS LAYER                                        │
│   ┌─────────────────────┐  ┌─────────────────────┐                         │
│   │  AI Metrics          │  │  Execution Metrics   │                        │
│   │  • Accuracy          │  │  • Pass/Fail rate    │                        │
│   │  • Hallucination     │  │  • Flakiness         │                        │
│   │  • Coverage score    │  │  • Auto-heal %       │                        │
│   └─────────────────────┘  └─────────────────────┘                         │
│                                                                             │
│   LAYER 3: AUTOMATION & EXECUTION LAYER                                    │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                    │
│   │  Script       │  │  Execution   │  │  Results &   │                    │
│   │  Agent        │  │  Engine      │  │  RCA Agent   │                    │
│   └──────────────┘  └──────────────┘  └──────────────┘                    │
│                                                                             │
│   LAYER 2: AGENTIC AI LAYER                                                │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                    │
│   │  Requirement  │  │  Test Case   │  │  Feedback &  │                    │
│   │  Agent        │  │  Design Agent│  │  Learning    │                    │
│   └──────────────┘  └──────────────┘  └──────────────┘                    │
│                                                                             │
│   LAYER 1: INPUT LAYER                                                     │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │  Jira Connector → Story Parser → Validation → Normalization      │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Layer-by-Layer Breakdown

### Layer 1: Input Layer (Jira Ingestion)

**Purpose:** Accept, validate, and normalize input from external systems.

| Component | Responsibility |
|-----------|---------------|
| Jira Connector | OAuth/token-based connection to Jira Cloud/Server |
| Story Parser | Extract summary, description, acceptance criteria, attachments |
| Validator | Check for completeness, supported formats, required fields |
| Normalizer | Standardize content into a canonical internal format for downstream agents |

**Testing Architect's Note:** This layer is the **entry point** — if input is corrupted here, every downstream agent produces garbage. Testing must be exhaustive, covering malformed input, permission failures, rate limits, and edge cases.

---

### Layer 2: Agentic AI Layer

**Purpose:** Intelligent interpretation of requirements and autonomous test case generation.

| Component | Responsibility |
|-----------|---------------|
| Requirement Understanding Agent | Extract acceptance criteria, detect ambiguity, identify business rules |
| Test Case Design Agent | Generate functional test cases covering positive, negative, and edge scenarios |
| Feedback & Learning Module | Consume execution metrics to tune prompts and improve output quality |

**Testing Architect's Note:** This is the **brain** of the platform. Testing here requires a fundamentally different approach — golden datasets, hallucination detection, prompt regression testing, and similarity scoring. Traditional assertion-based testing is insufficient.

---

### Layer 3: Automation & Execution Layer

**Purpose:** Transform test designs into executable code and run them against real applications.

| Component | Responsibility |
|-----------|---------------|
| Automation Script Agent | Convert test cases to Playwright/Selenium scripts, maintain POM structure |
| Execution Engine | Run scripts across browsers/environments, manage parallel execution, integrate CI/CD |
| Results & RCA Agent | Capture evidence (logs, screenshots, video), determine root cause, create Jira defects |

**Testing Architect's Note:** This layer faces the **real world** — browsers crash, networks fail, environments drift. Testing must include chaos engineering principles: kill browsers mid-execution, throttle networks, inject infra failures.

---

### Layer 4: Analysis & Metrics Layer

**Purpose:** Measure everything — both AI quality and execution quality.

| Metric Category | What It Tracks |
|-----------------|----------------|
| AI Metrics | Requirement accuracy, test coverage score, hallucination rate, decision confidence |
| Execution Metrics | Pass/fail rate, retry recovery, execution time, parallel efficiency, flakiness |

**Testing Architect's Note:** This layer is the **conscience** of the platform. Without it, we're running blind. Every metric must be validated for accuracy — a wrong metric is worse than no metric.

---

### Layer 5: Control Plane (Supervisor Agent)

**Purpose:** Orchestrate all agents, make system-level decisions, ensure autonomous operation.

| Responsibility | Example |
|----------------|---------|
| Agent coordination | "Requirement Agent is done → trigger Test Case Agent" |
| Decision making | "Script failed to compile → regenerate with different strategy" |
| Retry logic | "Execution failed due to infra → retry 3 times with backoff" |
| Escalation | "Confidence below threshold → flag for human review" |

**Testing Architect's Note:** This is the **nervous system**. Testing the Supervisor requires simulating agent failures, timeouts, conflicting signals, and boundary conditions. Decision accuracy is the primary metric.

---

## Data Flow — End to End

```
Jira Story
    │
    ▼
┌──────────────┐     ┌───────────────────┐     ┌───────────────────┐
│  INGESTION   │────▶│  REQUIREMENT      │────▶│  TEST CASE        │
│  Validate &  │     │  UNDERSTANDING    │     │  DESIGN           │
│  Normalize   │     │  Extract & Analyze│     │  Generate & Score │
└──────────────┘     └───────────────────┘     └─────────┬─────────┘
                                                          │
                          ┌───────────────────────────────┘
                          ▼
                 ┌───────────────────┐     ┌───────────────────┐
                 │  AUTOMATION       │────▶│  EXECUTION        │
                 │  SCRIPT GEN      │     │  ENGINE           │
                 │  Code & Validate │     │  Run & Capture    │
                 └───────────────────┘     └─────────┬─────────┘
                                                      │
                          ┌───────────────────────────┘
                          ▼
                 ┌───────────────────┐     ┌───────────────────┐
                 │  RESULTS & RCA   │────▶│  METRICS &        │
                 │  Analyze & Report│     │  FEEDBACK LOOP    │
                 │  Create Defects  │     │  Learn & Improve  │
                 └───────────────────┘     └───────────────────┘
                                                      │
                                                      ▼
                                               ┌──────────────┐
                                               │  SUPERVISOR  │
                                               │  Orchestrate │
                                               └──────────────┘
```

---

## Testing Architect's View: Independent Testability

Each layer is designed to be testable in isolation:

| Layer | How to Test Independently |
|-------|--------------------------|
| Input Layer | Mock Jira API, send known payloads, verify normalization output |
| AI Layer | Use golden datasets, mock input, compare output to expected baselines |
| Automation Layer | Provide fixed test cases, verify generated scripts compile and follow patterns |
| Execution Layer | Run known scripts against controlled test apps, verify evidence capture |
| Metrics Layer | Inject known results, verify metric calculations are mathematically correct |
| Control Plane | Simulate agent events, verify orchestration decisions match expected behavior |

**This layered independence is the architectural foundation that makes the system testable, debuggable, and trustworthy.**

---

## Integration Boundaries — Where Things Break

```
Layer 1 → Layer 2:  Data format mismatch, incomplete parsing, encoding issues
Layer 2 → Layer 3:  AI output format violations, missing fields, hallucinated steps
Layer 3 → Layer 4:  Mismatched result counts, missing timestamps, partial execution data
Layer 4 → Layer 5:  Metric calculation errors feeding wrong decisions to Supervisor
Layer 5 → All:      Incorrect orchestration cascading through the entire pipeline
```

Each boundary is an explicit **integration test point** with contract tests and schema validation.

---

*This architecture ensures that complexity is managed through separation, each layer earns its own trust, and the full system is more than the sum of its parts.*
