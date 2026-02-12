# Slide 7 — Module 3: Test Case Design Agent

## From Requirements to Comprehensive, Auditable Test Cases

---

## Module Overview

The Test Case Design Agent receives structured requirements from the Requirement Understanding Agent and generates **complete, categorized, traceable test cases** — covering positive, negative, and edge scenarios.

> **Architect's Principle:** A generated test case must be indistinguishable in quality from one written by a senior QA engineer.

---

## Responsibilities

| Responsibility | What It Does | Why It Matters |
|---------------|-------------|----------------|
| **Generate Functional Test Cases** | Create detailed TCs with steps, expected results, and test data | These become the blueprint for automation scripts |
| **Cover Positive, Negative, Edge Cases** | Ensure every AC has positive path + failure paths + boundary conditions | Single-path testing misses 60%+ of real-world bugs |
| **Maintain Jira Traceability** | Link every TC back to its source story and AC | Audit trail: "Why does this test exist?" always has an answer |

---

## Test Case Generation Flow

```
┌──────────────────────┐
│  Structured           │
│  Requirements         │
│  (from Module 2)      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    TEST CASE DESIGN AGENT                         │
│                                                                  │
│  Phase 1: Scenario Identification                                │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ For each AC → identify positive, negative, edge paths   │     │
│  │ For each business rule → identify violation scenarios    │     │
│  │ Cross-reference ACs for combined scenarios              │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  Phase 2: Test Case Construction                                 │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ For each scenario:                                      │     │
│  │   • Generate TC ID (traceable to story + AC)            │     │
│  │   • Write clear title                                   │     │
│  │   • Define preconditions                                │     │
│  │   • Write numbered steps                                │     │
│  │   • Define expected result per step                     │     │
│  │   • Assign priority (P0-P3)                             │     │
│  │   • Categorize (Functional/Negative/Edge/Security)      │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  Phase 3: Quality Scoring                                        │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ Coverage completeness score                             │     │
│  │ Duplicate detection (semantic similarity check)         │     │
│  │ Risk-based priority assignment                          │     │
│  │ Overall confidence score                                │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────┐
│  Structured Test      │
│  Cases (JSON)         │
│  + Coverage Report    │
└──────────────────────┘
```

---

## Testing Strategy

### 1. Coverage Completeness

For every story, we validate that the generated TCs cover:

| Coverage Dimension | What We Check | Target |
|-------------------|---------------|--------|
| AC Coverage | Every acceptance criterion has at least 1 test case | 100% |
| Positive Path Coverage | Each AC has a happy-path TC | 100% |
| Negative Path Coverage | Each AC has at least 1 failure-mode TC | >= 90% |
| Edge Case Coverage | Boundary values, empty inputs, max lengths tested | >= 80% |
| Business Rule Coverage | Each identified rule has violation scenarios | >= 85% |

**How we validate:**
```
For a story with 5 ACs:
  Expected minimum TCs = 5 positive + 5 negative + 3 edge = 13 TCs
  
  Agent generates 15 TCs:
    ✓ 5 positive (1 per AC)         → AC Coverage: 100%
    ✓ 5 negative (1 per AC)         → Negative Coverage: 100%
    ✓ 3 edge cases                  → Edge Coverage: OK
    ✓ 2 business rule violations    → Rule Coverage: OK
    
  Coverage Score: 100% (all dimensions met)
```

### 2. Duplicate Detection

The agent must not generate redundant test cases:

| Scenario | Example | Detection Method |
|----------|---------|------------------|
| Exact duplicate | Two TCs with identical steps | String comparison |
| Semantic duplicate | "Login with wrong password" and "Enter incorrect password and click login" | Cosine similarity > 0.85 → flag as duplicate |
| Subset duplicate | TC-A tests steps 1-5, TC-B tests steps 1-3 (subset) | Step overlap analysis |

### 3. Risk-Based Prioritization Accuracy

| Story Context | Expected Priority | Rationale |
|--------------|-------------------|-----------|
| Login/Authentication | P0 | Security-critical, user-facing |
| Payment processing | P0 | Revenue-impacting, compliance-required |
| Profile picture upload | P2 | Non-blocking, cosmetic |
| Admin dashboard filter | P2-P3 | Internal tool, low-frequency usage |
| Data export functionality | P1 | Data integrity, user trust |

**We validate that the agent assigns priorities aligned with risk assessment.**

---

## Test Cases for This Module

| TC ID | Test Case | Priority | Type |
|-------|-----------|----------|------|
| TD-001 | Story with 5 ACs → at least 10 TCs generated (positive + negative) | P0 | Coverage |
| TD-002 | All generated TCs have required fields (ID, title, steps, expected result) | P0 | Format |
| TD-003 | Every TC links back to source story ID and AC ID | P0 | Traceability |
| TD-004 | No semantic duplicates in generated TC set | P1 | Quality |
| TD-005 | Priority assignment matches risk assessment | P1 | Quality |
| TD-006 | Edge cases generated for numeric/string/date fields | P1 | Coverage |
| TD-007 | Negative TCs include invalid input, unauthorized access, timeout scenarios | P1 | Coverage |
| TD-008 | Golden dataset: generated TCs vs expert-written TCs → coverage >= 85% | P0 | Regression |
| TD-009 | Same input run 5 times → TC count and coverage remain consistent | P1 | Determinism |
| TD-010 | TC with hallucinated features (not in AC) → flagged and rejected | P0 | AI Quality |
| TD-011 | Complex story with 15 ACs → all ACs covered, no timeout | P2 | Scalability |
| TD-012 | TCs generated for ambiguous story (low confidence) → marked for human review | P1 | Safety |

---

## Output: Structured, Auditable Test Cases

**Sample Generated Test Case:**

```json
{
  "testCaseId": "TC-PROJ123-AC1-001",
  "storyId": "PROJ-123",
  "acceptanceCriteriaId": "AC-1",
  "title": "Verify user can login with valid email and password",
  "category": "Positive",
  "priority": "P0",
  "preconditions": [
    "User has a registered account with email: test@example.com",
    "User is on the login page"
  ],
  "steps": [
    { "step": 1, "action": "Enter valid email in the email field", "testData": "test@example.com" },
    { "step": 2, "action": "Enter valid password in the password field", "testData": "ValidPass@123" },
    { "step": 3, "action": "Click the Login button", "testData": null }
  ],
  "expectedResult": "User is redirected to the dashboard. Welcome message displays user's name.",
  "traceability": {
    "story": "PROJ-123",
    "ac": "AC-1",
    "businessRule": "BR-AUTH-001"
  },
  "confidence": 0.94,
  "automatable": true
}
```

---

## Coverage Report Output

```
┌──────────────────────────────────────────────────────┐
│           TEST CASE COVERAGE REPORT                   │
│           Story: PROJ-123                             │
│                                                      │
│  Total ACs: 5                                        │
│  Total TCs Generated: 16                             │
│                                                      │
│  Positive TCs:  5  (100% AC coverage)               │
│  Negative TCs:  6  (100% AC coverage)               │
│  Edge Cases:    3  (60% AC coverage)                 │
│  Security TCs:  2  (40% AC coverage)                │
│                                                      │
│  Duplicates Found: 0                                 │
│  Hallucination Flags: 0                              │
│  Confidence Score: 0.91                              │
│                                                      │
│  Status: READY FOR AUTOMATION                        │
└──────────────────────────────────────────────────────┘
```

---

## Architect's Notes

1. **The coverage report is as important as the test cases** — Without coverage metrics, we can't tell if the generation was thorough
2. **Traceability is non-negotiable** — Every TC must trace back to its source. If a TC can't justify its existence, it should be removed
3. **Confidence thresholds control flow** — TCs with confidence < 0.70 are routed to human review, not auto-executed
4. **Version the golden datasets** — As the product evolves, golden datasets must be updated; stale baselines produce false metrics

---

*This agent transforms unstructured human requirements into structured, measured, traceable test specifications — the foundation upon which reliable automation is built.*
