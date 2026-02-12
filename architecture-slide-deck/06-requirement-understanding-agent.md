# Slide 6 — Module 2: Requirement Understanding Agent

## Turning Stories Into Testable Knowledge

---

## Module Overview

The Requirement Understanding Agent receives normalized Jira story data and performs **intelligent interpretation** — extracting acceptance criteria, identifying business rules, and detecting ambiguity before anything gets tested.

> **Architect's Insight:** This is the most intellectually complex agent. It's the difference between "testing what was written" and "testing what was *meant*."

---

## Responsibilities

| Responsibility | What It Does | Why It Matters |
|---------------|-------------|----------------|
| **Extract Acceptance Criteria** | Parse AC from story body, recognize formats (Given/When/Then, bullet points, tables) | Downstream agents need structured AC to generate meaningful tests |
| **Identify Business Rules** | Detect implicit rules (e.g., "user must be logged in" implies authentication is required) | Missing business rules = missing test scenarios |
| **Detect Ambiguity** | Flag vague phrases like "should work correctly", "as expected", "handle gracefully" | Ambiguous requirements produce unreliable tests |

---

## How the Agent Works

```
┌──────────────────┐
│  Normalized       │
│  Story Input      │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                REQUIREMENT UNDERSTANDING AGENT                    │
│                                                                  │
│  Step 1: AC Extraction                                           │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ Identify AC format (Gherkin, bullets, prose)            │     │
│  │ Extract each criterion as a discrete testable statement │     │
│  │ Map each AC to story fields (summary, description)      │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  Step 2: Business Rule Identification                            │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ Detect implicit preconditions (auth, roles, state)      │     │
│  │ Identify data constraints (min/max, format, required)   │     │
│  │ Flag cross-story dependencies                           │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  Step 3: Ambiguity Detection                                     │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ Score each AC on clarity (0-100)                        │     │
│  │ Flag phrases below clarity threshold                    │     │
│  │ Suggest clarification questions for flagged items       │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  Output: Structured Requirements + Confidence Score              │
└──────────────────────────────────────────────────────────────────┘
```

---

## Testing Strategy

### 1. Golden Story Comparison

This is the **primary validation method** for this agent.

```
APPROACH:
  1. Create a "golden dataset" of 50-100 stories with:
     • Known acceptance criteria (human-verified)
     • Known business rules (architect-approved)
     • Known ambiguity flags (labeled by senior QA)
  
  2. Feed each story through the Requirement Agent
  
  3. Compare agent output against golden baseline:
     • Did it extract ALL acceptance criteria? (Recall)
     • Did it extract ONLY real criteria, no hallucinated ones? (Precision)
     • Did it identify the correct business rules?
     • Did it flag the right ambiguities?

SCORING:
  AC Extraction Accuracy  = (Correctly extracted ACs / Total known ACs) × 100
  Business Rule Recall     = (Detected rules / Total known rules) × 100
  Ambiguity Detection F1   = 2 × (Precision × Recall) / (Precision + Recall)
```

### 2. Hallucination Detection

| What to Check | Example | How to Detect |
|---------------|---------|---------------|
| Invented acceptance criteria | Story says "Login with email" → Agent adds "Login with social auth" | Compare against source; no AC in output should lack a source mapping |
| Invented business rules | Story doesn't mention roles → Agent adds "Admin-only access" | Verify every rule has evidence in the story text |
| Over-interpretation | "User fills form" → Agent interprets specific field names not in story | Output should only reference entities mentioned in the input |

### 3. Ambiguity Flag Accuracy

| Story Text | Should Be Flagged? | Why |
|-----------|-------------------|-----|
| "The page should load correctly" | Yes | "correctly" is subjective — no measurable criteria |
| "User can login with email and password" | No | Clear, specific, testable |
| "Handle errors appropriately" | Yes | "appropriately" is undefined |
| "Response time should be acceptable" | Yes | "acceptable" has no defined threshold |
| "Display user's name on the dashboard after login" | No | Specific, verifiable |

---

## Test Cases

| TC ID | Test Case | Priority | Type |
|-------|-----------|----------|------|
| RU-001 | Story with 5 clear ACs → all 5 extracted correctly | P0 | Positive |
| RU-002 | Story with Gherkin format → parsed into structured AC | P0 | Positive |
| RU-003 | Story with bullet-point ACs → each bullet becomes one AC | P1 | Positive |
| RU-004 | Story with no AC → agent flags as "incomplete" | P0 | Negative |
| RU-005 | Story with vague AC → ambiguity flags raised | P0 | Positive |
| RU-006 | Story with implicit business rules → agent detects them | P1 | Positive |
| RU-007 | Hallucination test: agent should NOT add criteria not in story | P0 | AI Quality |
| RU-008 | Story with conflicting ACs → agent flags conflict | P1 | Edge Case |
| RU-009 | Story with 20+ ACs → no truncation, all extracted | P2 | Scalability |
| RU-010 | Same story run 5 times → consistent output (determinism) | P1 | Reliability |
| RU-011 | Golden dataset: 50 stories → accuracy >= 85% | P0 | Regression |
| RU-012 | Prompt injection in story text → agent ignores malicious input | P0 | Security |

---

## Key Metric

### Requirement Interpretation Accuracy %

```
                    ┌─────────────────────────────────────────┐
                    │    REQUIREMENT INTERPRETATION ACCURACY   │
                    │                                         │
                    │    Formula:                             │
                    │    (Correct Extractions + Correct Flags)│
                    │    ─────────────────────────────────── │
                    │    (Total Expected Extractions + Flags) │
                    │                                         │
                    │    Target: >= 85%                       │
                    │    Alert:  < 75%                        │
                    │    Block:  < 65%                        │
                    └─────────────────────────────────────────┘
```

### Supporting Metrics

| Metric | Target |
|--------|--------|
| AC Extraction Recall | >= 90% |
| AC Extraction Precision | >= 85% |
| Ambiguity Detection F1 Score | >= 80% |
| Business Rule Detection Rate | >= 75% |
| Hallucination Rate | < 5% |
| Average Confidence Score | >= 0.80 |

---

## Integration Contract

**Input Schema (from Jira Ingestion):**
```json
{
  "storyId": "PROJ-123",
  "summary": "User login feature",
  "description": "As a user, I want to login with email...",
  "acceptanceCriteria": "Given I am on login page...",
  "labels": ["login", "auth"],
  "storyType": "Story",
  "priority": "High"
}
```

**Output Schema (to Test Case Design Agent):**
```json
{
  "storyId": "PROJ-123",
  "extractedACs": [
    {
      "id": "AC-1",
      "text": "User can login with valid email and password",
      "type": "positive",
      "clarity_score": 92,
      "source_mapping": "acceptanceCriteria:line1"
    }
  ],
  "businessRules": [
    {
      "rule": "User must have a registered account",
      "confidence": 0.88,
      "evidence": "Implied by 'login with email and password'"
    }
  ],
  "ambiguityFlags": [],
  "overallConfidence": 0.91
}
```

---

## Architect's Testing Notes

1. **Run golden dataset tests on every prompt change** — A single word change in the LLM prompt can dramatically shift extraction behavior
2. **Track confidence score distribution** — If the average drops over time, the model or data is drifting
3. **Human review loop** — Stories flagged with ambiguity should actually be ambiguous; audit the flags monthly
4. **Cross-language testing** — If the system supports multi-language Jira instances, test extraction in each supported language

---

*This agent is the "translator" between human intent and machine-testable requirements. Its accuracy directly determines the quality of everything that follows.*
