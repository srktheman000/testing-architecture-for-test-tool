# 04 — Test Case Generation Validation

> **Purpose:** Define how to validate the completeness, accuracy, and quality of AI-generated test cases, including coverage analysis, duplicate detection, and a quality scoring formula.

---

## 4.1 Validation Framework Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              TEST CASE GENERATION VALIDATION PIPELINE            │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Schema   │─▶│ Coverage │─▶│ Quality  │─▶│ Duplicate│       │
│  │ Check    │  │ Analysis │  │ Scoring  │  │ Detection│       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│       │             │             │              │              │
│       ▼             ▼             ▼              ▼              │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              VALIDATION REPORT                       │      │
│  │  • Schema compliance: PASS/FAIL                      │      │
│  │  • Coverage score: 0-100%                            │      │
│  │  • Quality score: 0-100                              │      │
│  │  • Duplicates found: N                               │      │
│  │  • Missing AC coverage: [list]                       │      │
│  │  • Recommendation: APPROVE / REVIEW / REJECT         │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4.2 Completeness Validation

### 4.2.1 Test Case Structural Completeness

Every generated test case must contain all required fields:

| Field | Required | Validation Rule |
|-------|----------|----------------|
| `id` | Yes | Non-empty, unique within suite, format `TC-NNN` |
| `title` | Yes | 10-200 characters, descriptive, no generic titles |
| `type` | Yes | One of: positive, negative, edge_case, boundary, security, performance |
| `priority` | Yes | One of: critical, high, medium, low |
| `preconditions` | Yes | At least one precondition listed |
| `steps` | Yes | At least 2 steps, each with action + expected result |
| `expectedResult` | Yes | Clear, verifiable outcome statement |
| `testData` | Conditional | Required if steps reference specific data values |
| `traceability` | Yes | Links to source acceptance criteria index |
| `tags` | Optional | Relevant categorization tags |

**Completeness Score:**

```
Completeness_Score = (Fields_Present / Required_Fields_Total) × 100

Penalty: -5 points for each field that exists but has low quality
  (e.g., title = "Test 1", expectedResult = "It works")
```

### 4.2.2 Acceptance Criteria Traceability

Every acceptance criterion must be covered by at least one test case.

**Traceability Matrix Example:**

| Acceptance Criteria | Test Cases Covering | Coverage Status |
|--------------------|--------------------|--------------| 
| AC-1: Valid login redirects to dashboard | TC-001, TC-002 | Covered |
| AC-2: Invalid password shows error | TC-003, TC-004 | Covered |
| AC-3: Account lockout after 5 attempts | TC-005 | Covered |
| AC-4: Remember me checkbox works | — | **NOT COVERED** |
| AC-5: Password field masks input | TC-006 | Covered |

**Traceability Score:**

```
Traceability_Score = (ACs_Covered / Total_ACs) × 100
```

---

## 4.3 Coverage Analysis

### 4.3.1 Scenario Type Coverage

For each Jira ticket, the AI should generate test cases across multiple categories:

| Scenario Type | Description | Expected Minimum | Weight |
|--------------|-------------|------------------|--------|
| **Positive** | Happy path, expected behavior | At least 1 per AC | 0.30 |
| **Negative** | Invalid inputs, error conditions | At least 1 per AC | 0.25 |
| **Edge Cases** | Boundary values, empty states, max lengths | At least 2 total | 0.20 |
| **Boundary Cases** | Min/max values, limits, overflow | At least 1 total | 0.15 |
| **Security** | Injection, unauthorized access, XSS | At least 1 if applicable | 0.05 |
| **Performance** | Response time, load handling | At least 1 if applicable | 0.05 |

**Coverage Score Calculation:**

```
Coverage_Score = Σ (Category_Weight × min(1, Actual_Count / Expected_Minimum))
```

**Example:**

```
Positive scenarios:   3 generated (min 3 expected) → 0.30 × min(1, 3/3) = 0.30
Negative scenarios:   2 generated (min 3 expected) → 0.25 × min(1, 2/3) = 0.167
Edge cases:           1 generated (min 2 expected) → 0.20 × min(1, 1/2) = 0.10
Boundary cases:       1 generated (min 1 expected) → 0.15 × min(1, 1/1) = 0.15
Security:             0 generated (min 1 expected) → 0.05 × min(1, 0/1) = 0.00
Performance:          0 generated (min 1 expected) → 0.05 × min(1, 0/1) = 0.00
                                                                    Total: 0.717 (71.7%)
```

### 4.3.2 Missing Coverage Detection

The validator automatically identifies gaps:

```javascript
function detectMissingCoverage(testCases, acceptanceCriteria) {
  const gaps = {
    uncoveredACs: [],
    missingTypes: [],
    missingEdgeCases: [],
    suggestions: []
  };

  // Check AC coverage
  for (const [index, ac] of acceptanceCriteria.entries()) {
    const coveringTests = testCases.filter(tc =>
      tc.traceability?.acceptanceCriteriaIndex === index
    );
    if (coveringTests.length === 0) {
      gaps.uncoveredACs.push({
        acIndex: index,
        acText: ac,
        suggestion: `Generate at least one test case for: "${ac}"`
      });
    }
  }

  // Check type coverage
  const typesPresent = new Set(testCases.map(tc => tc.type));
  const requiredTypes = ['positive', 'negative'];
  for (const type of requiredTypes) {
    if (!typesPresent.has(type)) {
      gaps.missingTypes.push(type);
      gaps.suggestions.push(`No ${type} test cases found. Add at least one.`);
    }
  }

  // Check edge case coverage
  if (!typesPresent.has('edge_case') && !typesPresent.has('boundary')) {
    gaps.missingEdgeCases.push('No edge case or boundary tests found');
    gaps.suggestions.push('Add tests for empty inputs, max lengths, special characters');
  }

  return gaps;
}
```

---

## 4.4 Duplicate Detection

### 4.4.1 Duplicate Detection Strategy

Duplicates waste execution time and inflate metrics. Three levels of duplicate detection are applied:

| Level | Method | Threshold | Action |
|-------|--------|-----------|--------|
| **Exact** | String equality of title + steps | 100% match | Remove duplicate |
| **Near** | Cosine similarity of title + steps | > 90% similarity | Flag for review |
| **Semantic** | Embedding-based comparison | > 85% similarity | Flag if same AC |

**Detection Algorithm:**

```python
def detect_duplicates(test_cases):
    duplicates = []
    embeddings = embed_test_cases(test_cases)

    for i in range(len(test_cases)):
        for j in range(i + 1, len(test_cases)):
            # Exact match
            if normalize(test_cases[i].title) == normalize(test_cases[j].title):
                duplicates.append({
                    'type': 'exact',
                    'pair': (i, j),
                    'action': 'remove'
                })
                continue

            # Semantic similarity
            similarity = cosine_similarity(embeddings[i], embeddings[j])
            if similarity > 0.90:
                duplicates.append({
                    'type': 'near_duplicate',
                    'pair': (i, j),
                    'similarity': similarity,
                    'action': 'review'
                })
            elif similarity > 0.85 and test_cases[i].traceability == test_cases[j].traceability:
                duplicates.append({
                    'type': 'semantic_duplicate',
                    'pair': (i, j),
                    'similarity': similarity,
                    'action': 'review'
                })

    return duplicates
```

---

## 4.5 Missing Acceptance Criteria Detection

The platform should detect when a Jira ticket has incomplete or missing ACs:

| Detection Rule | Trigger | Action |
|---------------|---------|--------|
| No AC found in ticket | Description lacks structured criteria | Alert user, generate from description best-effort |
| AC too vague | Testability score < 0.4 | Flag specific ACs, suggest improvements |
| AC contradicts other ACs | Semantic analysis detects conflict | Flag contradiction to user |
| AC references unknown system | Entity extraction finds unknown references | Flag with clarification request |
| Missing non-functional AC | No performance/security criteria | Suggest additions based on ticket type |

---

## 4.6 Sample Validation Checklist

### Per-Test-Case Checklist

| # | Check | Pass Criteria | Weight |
|---|-------|--------------|--------|
| 1 | Title is descriptive and unique | Not generic ("Test 1"), not duplicate | 5% |
| 2 | Type is appropriate for content | Positive test doesn't describe error scenario | 10% |
| 3 | Priority aligns with AC criticality | Critical AC → High/Critical priority test | 5% |
| 4 | Preconditions are complete | All setup requirements listed | 10% |
| 5 | Steps are atomic and ordered | Each step is one action, logical sequence | 15% |
| 6 | Each step has expected result | No step without verification | 10% |
| 7 | Final expected result is verifiable | Specific, measurable outcome | 15% |
| 8 | Test data is specified | No ambiguous "enter valid data" | 10% |
| 9 | Traces to acceptance criteria | AC index present and correct | 10% |
| 10 | No hallucinated elements | All references exist in source ticket | 10% |

### Per-Suite Checklist

| # | Check | Pass Criteria |
|---|-------|--------------|
| 1 | All ACs are covered | Traceability score = 100% |
| 2 | Positive scenarios present | At least 1 per AC |
| 3 | Negative scenarios present | At least 1 per AC |
| 4 | Edge cases present | At least 2 per suite |
| 5 | No duplicates | Duplicate count = 0 |
| 6 | Test count is reasonable | Between (AC count × 1.5) and (AC count × 4) |
| 7 | All test IDs unique | No ID collisions |
| 8 | Schema fully compliant | 100% schema compliance |

---

## 4.7 AI Output Quality Score Formula

### Composite Quality Score

The **AI Output Quality Score (AOQS)** is a weighted composite metric:

```
AOQS = (
    W_completeness  × Completeness_Score  +
    W_coverage      × Coverage_Score      +
    W_accuracy      × Accuracy_Score      +
    W_hallucination × Hallucination_Free  +
    W_duplicate     × Duplicate_Free      +
    W_traceability  × Traceability_Score
) × 100

Where:
    W_completeness  = 0.15    Completeness_Score  = fields_present / fields_required
    W_coverage      = 0.25    Coverage_Score      = weighted scenario type coverage
    W_accuracy      = 0.25    Accuracy_Score      = semantic match with expected (golden dataset)
    W_hallucination = 0.15    Hallucination_Free  = 1 - (hallucinated_elements / total_elements)
    W_duplicate     = 0.05    Duplicate_Free      = 1 - (duplicate_count / total_count)
    W_traceability  = 0.15    Traceability_Score  = ACs_covered / ACs_total
```

### Score Interpretation

| AOQS Range | Grade | Interpretation | Action |
|-----------|-------|----------------|--------|
| 90 - 100 | A | Excellent — production ready | Auto-approve |
| 80 - 89 | B | Good — minor gaps | Quick review |
| 70 - 79 | C | Acceptable — notable gaps | Full review required |
| 60 - 69 | D | Below standard — significant issues | Regenerate with feedback |
| 0 - 59 | F | Unacceptable — major failures | Reject, investigate root cause |

### Quality Score Dashboard

```
┌──────────────────────────────────────────────────────────┐
│                 AI OUTPUT QUALITY DASHBOARD               │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Overall AOQS: ████████████████████░░░░░ 82/100 (B)     │
│                                                          │
│  Completeness:  █████████████████████████ 95%            │
│  Coverage:      ████████████████░░░░░░░░ 72%            │
│  Accuracy:      █████████████████████░░░ 85%            │
│  Hallucination: █████████████████████████ 98% (clean)   │
│  Duplicates:    █████████████████████████ 100% (none)   │
│  Traceability:  ██████████████████░░░░░░ 80%            │
│                                                          │
│  Recommendation: FULL REVIEW REQUIRED                    │
│  Gaps: Missing negative scenarios for AC-3, AC-5         │
│  Suggestion: Regenerate with emphasis on error scenarios  │
└──────────────────────────────────────────────────────────┘
```

---

## 4.8 Validation Test Cases

| Test ID | Scenario | Input | Expected Validation Result |
|---------|----------|-------|---------------------------|
| VAL-001 | Perfect output | Golden dataset entry with all fields | AOQS >= 90, auto-approve |
| VAL-002 | Missing negative tests | Suite with only positive tests | Coverage score drops, suggestion generated |
| VAL-003 | Duplicate test cases | Suite with 2 identical tests | Duplicate detected, flagged |
| VAL-004 | Hallucinated URL | Test step references non-existent URL | Hallucination detected, flagged |
| VAL-005 | Uncovered AC | One AC has no corresponding test | Traceability gap reported |
| VAL-006 | Invalid schema | Output missing `steps` field | Schema validation fails |
| VAL-007 | Generic titles | All tests titled "Test N" | Quality penalty applied |
| VAL-008 | Ambiguous expected results | "It should work correctly" | Quality penalty, suggestion generated |
| VAL-009 | Over-generation | 50 tests for 3 simple ACs | Warning: excessive test count |
| VAL-010 | Under-generation | 1 test for 10 complex ACs | Warning: insufficient coverage |

---

*Previous: [03 — AI-Specific Testing](./03-ai-specific-testing-strategy.md) | Next: [05 — Automation Engine Testing](./05-automation-engine-testing.md)*
