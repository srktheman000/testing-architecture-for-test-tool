# 03 — AI-Specific Testing Strategy

> **Purpose:** Define a rigorous testing approach for all AI/LLM components, including prompt engineering, model output validation, hallucination detection, and golden dataset management.

---

## 3.1 AI Testing Landscape

AI components in this platform are **non-deterministic by nature**, which demands a fundamentally different testing philosophy compared to traditional software.

```
┌──────────────────────────────────────────────────────────────────┐
│                    AI TESTING LAYERS                              │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  LAYER 4: BEHAVIORAL TESTING                               │  │
│  │  Does the AI produce useful, accurate, complete outputs?   │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  LAYER 3: GOLDEN DATASET TESTING                           │  │
│  │  Does the AI maintain quality against known benchmarks?    │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  LAYER 2: OUTPUT VALIDATION                                │  │
│  │  Is the AI output structurally correct and safe?           │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  LAYER 1: PROMPT TESTING                                   │  │
│  │  Are we asking the right questions the right way?          │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3.2 Prompt Testing

### 3.2.1 Prompt Versioning System

Every prompt used in production must be versioned, stored, and traceable.

**Prompt Registry Structure:**

```
prompts/
├── test-case-generation/
│   ├── v1.0.0/
│   │   ├── system.txt          # System instructions
│   │   ├── user-template.txt   # User message template
│   │   ├── examples.json       # Few-shot examples
│   │   └── metadata.json       # Version info, author, date
│   ├── v1.1.0/
│   │   └── ...
│   └── changelog.md
├── script-generation/
│   ├── v1.0.0/
│   │   └── ...
│   └── changelog.md
└── root-cause-analysis/
    └── v1.0.0/
        └── ...
```

**Metadata Schema:**

```json
{
  "version": "1.1.0",
  "author": "qa-team",
  "createdAt": "2026-02-01",
  "model": "gpt-4-turbo",
  "temperature": 0.3,
  "maxTokens": 4096,
  "description": "Added edge case generation instructions",
  "parentVersion": "1.0.0",
  "goldenDatasetVersion": "GD-2026-02",
  "approvedBy": "qa-lead",
  "status": "production"
}
```

### 3.2.2 Prompt Regression Testing

Every prompt change triggers a regression suite against the golden dataset.

**Regression Test Flow:**

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Prompt      │────▶│  Run Against │────▶│  Compare     │────▶│  Pass/Fail   │
│  Change      │     │  Golden      │     │  Results vs  │     │  Decision    │
│  Detected    │     │  Dataset     │     │  Baseline    │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                       │
                                          ┌──────────────┐             │
                                          │  Generate    │◀────────────┘
                                          │  Diff Report │   (if regression)
                                          └──────────────┘
```

**Regression Criteria:**

| Metric | Threshold | Action if Breached |
|--------|----------|-------------------|
| Overall accuracy | < 85% of baseline | Block deployment |
| Any category drops > 10% | Relative decline | Require review |
| New hallucination patterns | Any new pattern | Block + investigate |
| Schema compliance | < 95% | Block deployment |
| Response latency | > 120% of baseline | Warning, review |

### 3.2.3 Prompt Regression Test Cases

| Test ID | Prompt Aspect | Input | Expected Behavior |
|---------|--------------|-------|-------------------|
| PRT-001 | System instructions present | Any ticket | Output follows system format |
| PRT-002 | Few-shot examples effective | Edge case ticket | Output matches example pattern |
| PRT-003 | Token budget respected | Very large ticket | Prompt truncated gracefully, no crash |
| PRT-004 | PII sanitization | Ticket with emails/names | No PII in prompt sent to LLM |
| PRT-005 | Template variables filled | Standard ticket | No `{{placeholder}}` in final prompt |
| PRT-006 | Model parameter consistency | Same ticket, 3 runs | Output variance within acceptable range |

### 3.2.4 Guardrails for Hallucinations

**Hallucination Detection Pipeline:**

```
LLM Output
    │
    ▼
┌────────────────┐   NO    ┌──────────────┐
│ Schema Valid?  │────────▶│ REJECT +     │
│                │         │ Log + Alert  │
└───────┬────────┘         └──────────────┘
        │ YES
        ▼
┌────────────────┐   NO    ┌──────────────┐
│ References     │────────▶│ FLAG for     │
│ exist in       │         │ human review │
│ source ticket? │         └──────────────┘
└───────┬────────┘
        │ YES
        ▼
┌────────────────┐   NO    ┌──────────────┐
│ Confidence     │────────▶│ FLAG for     │
│ above          │         │ human review │
│ threshold?     │         └──────────────┘
└───────┬────────┘
        │ YES
        ▼
┌────────────────┐
│ ACCEPT         │
│ (Auto-approve  │
│  or queue)     │
└────────────────┘
```

**Hallucination Categories to Detect:**

| Category | Description | Detection Method |
|----------|------------|-----------------|
| **Fabricated URLs** | Test steps reference URLs not in the ticket | URL extraction + cross-reference with ticket |
| **Invented selectors** | CSS/XPath selectors for non-existent elements | DOM validation against target app |
| **Ghost test data** | Test data values not derivable from ticket | Entity extraction comparison |
| **Phantom features** | Tests for features not mentioned in AC | Feature-to-AC traceability check |
| **Wrong assertions** | Expected results contradict the AC | Semantic similarity scoring |
| **Copied examples** | Output is copy of few-shot examples | Similarity check against examples |

### 3.2.5 Expected vs Actual Output Comparison

```javascript
// ai-output-comparison.test.js
describe('AI Output Comparison', () => {

  goldenDataset.forEach(({ input, expectedOutput, tolerance }) => {

    it(`should generate acceptable output for: ${input.ticketId}`, async () => {
      const actualOutput = await aiService.generateTestCases(input);

      // Structural comparison
      expect(actualOutput.testCases.length)
        .toBeWithinRange(
          expectedOutput.testCases.length - tolerance.countDelta,
          expectedOutput.testCases.length + tolerance.countDelta
        );

      // Coverage comparison
      const expectedCategories = expectedOutput.testCases.map(tc => tc.type);
      const actualCategories = actualOutput.testCases.map(tc => tc.type);
      expect(actualCategories).toContainAllOf(expectedCategories);

      // Semantic similarity for test titles
      for (const expectedTC of expectedOutput.testCases) {
        const bestMatch = findBestSemanticMatch(expectedTC.title, actualOutput.testCases);
        expect(bestMatch.similarity).toBeGreaterThan(tolerance.semanticThreshold);
      }

      // No hallucinations
      const hallucinations = detectHallucinations(actualOutput, input);
      expect(hallucinations).toHaveLength(0);
    });
  });
});
```

---

## 3.3 Model Output Validation

### 3.3.1 JSON Schema Validation

Every LLM response must conform to a strict JSON schema before processing.

**Test Case Output Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["testCases", "metadata"],
  "properties": {
    "testCases": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["id", "title", "type", "priority", "steps", "expectedResult"],
        "properties": {
          "id": { "type": "string", "pattern": "^TC-\\d{3,}$" },
          "title": { "type": "string", "minLength": 10, "maxLength": 200 },
          "type": {
            "type": "string",
            "enum": ["positive", "negative", "edge_case", "boundary", "security", "performance"]
          },
          "priority": {
            "type": "string",
            "enum": ["critical", "high", "medium", "low"]
          },
          "preconditions": {
            "type": "array",
            "items": { "type": "string" }
          },
          "steps": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "object",
              "required": ["stepNumber", "action", "expectedResult"],
              "properties": {
                "stepNumber": { "type": "integer", "minimum": 1 },
                "action": { "type": "string", "minLength": 5 },
                "expectedResult": { "type": "string", "minLength": 5 },
                "testData": { "type": "string" }
              }
            }
          },
          "expectedResult": { "type": "string", "minLength": 10 },
          "tags": {
            "type": "array",
            "items": { "type": "string" }
          },
          "traceability": {
            "type": "object",
            "properties": {
              "acceptanceCriteriaIndex": { "type": "integer" },
              "jiraTicketId": { "type": "string" }
            }
          }
        }
      }
    },
    "metadata": {
      "type": "object",
      "required": ["generatedAt", "promptVersion", "modelVersion", "confidence"],
      "properties": {
        "generatedAt": { "type": "string", "format": "date-time" },
        "promptVersion": { "type": "string" },
        "modelVersion": { "type": "string" },
        "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
        "tokensUsed": { "type": "integer" },
        "processingTimeMs": { "type": "integer" }
      }
    }
  }
}
```

### 3.3.2 Confidence Scoring

The platform assigns a confidence score to each generated output:

**Confidence Calculation:**

```
Confidence Score = (
    W1 × Schema_Compliance_Score    +
    W2 × AC_Coverage_Score          +
    W3 × Hallucination_Free_Score   +
    W4 × Diversity_Score            +
    W5 × Semantic_Coherence_Score
)

Where:
  W1 = 0.20  (Schema compliance weight)
  W2 = 0.30  (AC coverage weight)
  W3 = 0.25  (Hallucination-free weight)
  W4 = 0.10  (Test type diversity weight)
  W5 = 0.15  (Semantic coherence weight)
```

**Confidence Thresholds:**

| Score Range | Action | Label |
|------------|--------|-------|
| 0.90 - 1.00 | Auto-approve for execution | High Confidence |
| 0.70 - 0.89 | Queue for quick human review | Medium Confidence |
| 0.50 - 0.69 | Require full human review | Low Confidence |
| 0.00 - 0.49 | Reject, regenerate with different params | Very Low / Reject |

### 3.3.3 Deterministic vs Non-Deterministic Output Handling

| Aspect | Deterministic | Non-Deterministic |
|--------|--------------|-------------------|
| **Temperature** | 0.0 | 0.3 - 0.7 |
| **Use case** | Regression testing, baseline comparison | Production generation |
| **Testing approach** | Exact match comparison | Semantic similarity + schema validation |
| **Reproducibility** | Same input → same output | Same input → similar outputs |
| **When to use** | Golden dataset tests, CI/CD | User-facing generation |

**Testing Non-Deterministic Outputs:**

```javascript
describe('Non-Deterministic Output Stability', () => {

  it('should produce consistent output quality across 5 runs', async () => {
    const input = goldenTicket('LOGIN_FLOW');
    const results = [];

    for (let i = 0; i < 5; i++) {
      results.push(await aiService.generateTestCases(input));
    }

    // All runs should produce valid schema
    results.forEach(r => expect(schemaValidator.validate(r)).toBe(true));

    // Test count should be within ±2 of median
    const counts = results.map(r => r.testCases.length);
    const median = getMedian(counts);
    counts.forEach(c => expect(Math.abs(c - median)).toBeLessThanOrEqual(2));

    // All runs should cover the same test types
    const typesCoverage = results.map(r =>
      new Set(r.testCases.map(tc => tc.type))
    );
    const requiredTypes = ['positive', 'negative'];
    typesCoverage.forEach(types =>
      requiredTypes.forEach(t => expect(types.has(t)).toBe(true))
    );
  });
});
```

### 3.3.4 Handling Ambiguous Requirements

**Ambiguity Detection Tests:**

| Test ID | Input Characteristic | Expected AI Behavior |
|---------|---------------------|---------------------|
| AMB-001 | AC says "user should see appropriate error" | AI flags ambiguity, asks for specifics or generates multiple interpretations |
| AMB-002 | AC has no mention of negative scenarios | AI generates negative cases with `inferred: true` flag |
| AMB-003 | AC references external system with no details | AI generates test case with `assumptions` field populated |
| AMB-004 | AC is in non-English language | AI detects language, processes correctly or flags |
| AMB-005 | AC contains contradictory statements | AI flags contradiction, generates tests for each interpretation |

---

## 3.4 Golden Dataset Testing

### 3.4.1 Golden Dataset Structure

The golden dataset is the **single source of truth** for AI quality measurement.

```
golden-datasets/
├── v2026-02/
│   ├── dataset.json           # All test pairs
│   ├── categories/
│   │   ├── login-flows.json   # Login/auth related tickets
│   │   ├── crud-operations.json
│   │   ├── search-filter.json
│   │   ├── payment-checkout.json
│   │   ├── edge-cases.json
│   │   └── ambiguous-tickets.json
│   ├── baseline-results.json  # Expected results for current model
│   └── metadata.json          # Dataset version info
└── changelog.md
```

**Golden Dataset Entry Format:**

```json
{
  "id": "GD-001",
  "category": "login-flows",
  "difficulty": "standard",
  "jiraTicket": {
    "key": "PROJ-101",
    "summary": "User login with email and password",
    "description": "As a registered user, I want to login...",
    "acceptanceCriteria": [
      "Given valid credentials, login succeeds and redirects to dashboard",
      "Given invalid password, error message 'Invalid credentials' is shown",
      "Given unregistered email, error message 'Account not found' is shown",
      "Password field masks input characters",
      "Login button is disabled until both fields are filled"
    ],
    "type": "Story",
    "priority": "High"
  },
  "expectedTestCases": {
    "minimumCount": 5,
    "maximumCount": 10,
    "requiredTypes": ["positive", "negative", "edge_case"],
    "requiredCoverage": [
      { "acIndex": 0, "mustCover": true },
      { "acIndex": 1, "mustCover": true },
      { "acIndex": 2, "mustCover": true },
      { "acIndex": 3, "mustCover": true },
      { "acIndex": 4, "mustCover": true }
    ],
    "requiredKeywords": ["login", "credentials", "error", "dashboard", "password"],
    "forbiddenPatterns": ["hardcoded URL", "specific user data", "implementation detail"]
  },
  "tolerances": {
    "countVariance": 2,
    "semanticSimilarityMinimum": 0.75,
    "newCategoriesAllowed": true
  }
}
```

### 3.4.2 Golden Dataset Coverage Requirements

| Category | Number of Entries | Complexity Mix |
|----------|------------------|----------------|
| Login / Authentication | 10 | 4 standard, 3 complex, 3 edge |
| CRUD Operations | 15 | 5 standard, 5 complex, 5 edge |
| Search / Filter / Sort | 10 | 3 standard, 4 complex, 3 edge |
| Payment / Checkout | 8 | 2 standard, 3 complex, 3 edge |
| File Upload / Download | 5 | 2 standard, 2 complex, 1 edge |
| API-focused tickets | 8 | 3 standard, 3 complex, 2 edge |
| Ambiguous / Incomplete | 10 | All edge/ambiguous |
| Non-functional requirements | 5 | All complex |
| **TOTAL** | **71** | — |

### 3.4.3 Drift Detection

**What is drift?** When the AI model's behavior changes over time (due to model updates, prompt changes, or provider-side modifications), the outputs may gradually diverge from the established baseline.

**Drift Detection Strategy:**

```
┌─────────────┐     ┌───────────────┐     ┌─────────────────┐
│  Nightly     │────▶│  Run Golden   │────▶│  Compare vs     │
│  Scheduled   │     │  Dataset      │     │  Baseline       │
│  Job         │     │  (temp=0.0)   │     │  Results        │
└─────────────┘     └───────────────┘     └────────┬────────┘
                                                    │
                                    ┌───────────────┼───────────────┐
                                    ▼               ▼               ▼
                              ┌──────────┐   ┌──────────┐   ┌──────────┐
                              │ No Drift │   │ Warning  │   │ Critical │
                              │ (< 5%)   │   │ (5-15%)  │   │ (> 15%)  │
                              └──────────┘   └────┬─────┘   └────┬─────┘
                                                   │              │
                                                   ▼              ▼
                                             ┌──────────┐  ┌──────────┐
                                             │ Alert    │  │ Block    │
                                             │ QA Lead  │  │ Deploy + │
                                             └──────────┘  │ Alert    │
                                                           └──────────┘
```

**Drift Metrics Tracked:**

| Metric | Calculation | Warning Threshold | Critical Threshold |
|--------|------------|-------------------|-------------------|
| Accuracy Drift | \|current_accuracy - baseline_accuracy\| | > 5% | > 15% |
| Coverage Drift | \|current_coverage - baseline_coverage\| | > 5% | > 10% |
| Schema Compliance Drift | \|current_compliance - baseline_compliance\| | > 2% | > 5% |
| Hallucination Rate Drift | current_hallucination_rate - baseline_rate | > 3% | > 8% |
| Response Time Drift | current_p95 / baseline_p95 | > 1.5x | > 2.5x |

---

## 3.5 AI Testing Tools & Frameworks

| Tool | Purpose | Integration |
|------|---------|------------|
| **DeepEval** | LLM output evaluation framework | CI/CD pipeline |
| **Promptfoo** | Prompt testing and comparison | Prompt regression suite |
| **LangSmith** | LLM observability and tracing | Production monitoring |
| **Custom Harness** | Platform-specific AI validation | Core test infrastructure |
| **Semantic Similarity (sentence-transformers)** | Output comparison | Golden dataset tests |

---

## 3.6 AI Test Execution Schedule

| Test Type | Trigger | Duration | Blocking? |
|-----------|---------|----------|-----------|
| Prompt regression (cached) | Every PR with prompt changes | ~2 min | Yes |
| Schema validation | Every PR | ~1 min | Yes |
| Golden dataset (deterministic) | Nightly | ~15 min | No (alerts) |
| Golden dataset (non-deterministic) | Weekly | ~30 min | No (alerts) |
| Drift detection | Nightly | ~20 min | Alerts only |
| Full AI validation suite | Pre-release | ~45 min | Yes |
| Model change validation | On model update | ~1 hour | Yes |

---

*Previous: [02 — Test Pyramid](./02-test-pyramid.md) | Next: [04 — Test Case Generation Validation](./04-test-case-generation-validation.md)*
