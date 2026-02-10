# 02 — Test Pyramid for the AI Test Automation Platform

> **Purpose:** Define a layered testing strategy covering unit, integration, and end-to-end tests with clear ownership, tooling, and coverage targets.

---

## 2.1 Pyramid Overview

```
                    ┌───────────┐
                    │   E2E     │   ~10% of total tests
                    │  Tests    │   Slow, expensive, high confidence
                    ├───────────┤
                    │           │
                  ┌─┤Integration├─┐   ~25% of total tests
                  │ │  Tests    │ │   Medium speed, real contracts
                  │ ├───────────┤ │
                  │ │           │ │
                ┌─┤ │   Unit    │ ├─┐   ~65% of total tests
                │ │ │   Tests   │ │ │   Fast, isolated, deterministic
                └─┴─┴───────────┴─┴─┘
```

| Layer | Count Target | Execution Time | Runs When |
|-------|-------------|----------------|-----------|
| Unit | 500+ tests | < 2 minutes | Every commit, pre-push |
| Integration | 150+ tests | < 10 minutes | Every PR, nightly |
| E2E | 50+ tests | < 30 minutes | PR merge, nightly, pre-release |

---

## 2.2 Unit Testing

### 2.2.1 Backend Services

#### Jira Parser Unit Tests

The Jira Parser is responsible for extracting structured data from Jira API responses.

**What to test:**

| Test Category | Example Test Cases | Priority |
|--------------|-------------------|----------|
| Field extraction | Extract summary, description, acceptance criteria, labels, priority | P0 |
| HTML/Markdown parsing | Strip Jira wiki markup, convert to clean text | P0 |
| Custom field handling | Parse custom fields (story points, sprints, components) | P1 |
| Attachment extraction | Identify and download attached images, documents | P1 |
| Error handling | Missing fields, null values, unexpected data types | P0 |
| Multi-format support | Handle Jira Cloud vs Server API differences | P2 |

**Sample test structure:**

```javascript
// jira-parser.test.js
describe('JiraParser', () => {

  describe('extractAcceptanceCriteria', () => {
    it('should extract AC from description using Given/When/Then format', () => {
      const ticket = mockJiraTicket({
        description: 'Given a logged-in user\nWhen they click logout\nThen they are redirected to login page'
      });
      const result = parser.extractAcceptanceCriteria(ticket);
      expect(result).toHaveLength(1);
      expect(result[0].given).toBe('a logged-in user');
      expect(result[0].when).toBe('they click logout');
      expect(result[0].then).toBe('they are redirected to login page');
    });

    it('should handle bullet-point style acceptance criteria', () => {
      const ticket = mockJiraTicket({
        description: '* User can enter email\n* User can enter password\n* Error shown for invalid email'
      });
      const result = parser.extractAcceptanceCriteria(ticket);
      expect(result).toHaveLength(3);
    });

    it('should return empty array when no AC found', () => {
      const ticket = mockJiraTicket({ description: 'Just a plain description' });
      const result = parser.extractAcceptanceCriteria(ticket);
      expect(result).toHaveLength(0);
      expect(result.warnings).toContain('NO_AC_FOUND');
    });

    it('should handle Jira markup (h2, {code}, [links])', () => {
      const ticket = mockJiraTicket({
        description: 'h2. Acceptance Criteria\n* {code}username{code} field is required'
      });
      const result = parser.extractAcceptanceCriteria(ticket);
      expect(result[0].rawText).toContain('username');
      expect(result[0].rawText).not.toContain('{code}');
    });
  });
});
```

#### Acceptance Criteria Analyzer Unit Tests

**What to test:**

| Test Category | Example Test Cases | Priority |
|--------------|-------------------|----------|
| Completeness scoring | Score AC based on clarity, specificity, testability | P0 |
| Ambiguity detection | Flag vague terms: "should work", "appropriate", "fast" | P0 |
| Entity extraction | Identify actors, actions, expected results | P1 |
| Dependency detection | Identify preconditions, setup requirements | P1 |
| Classification | Categorize as functional, non-functional, edge case | P1 |

```javascript
describe('AcceptanceCriteriaAnalyzer', () => {

  it('should flag ambiguous criteria with low testability score', () => {
    const ac = 'The page should load quickly';
    const analysis = analyzer.analyze(ac);
    expect(analysis.testabilityScore).toBeLessThan(0.5);
    expect(analysis.ambiguityFlags).toContain('VAGUE_PERFORMANCE_REQUIREMENT');
  });

  it('should score well-defined criteria highly', () => {
    const ac = 'Given a user with valid credentials, when they submit the login form, then they are redirected to /dashboard within 2 seconds';
    const analysis = analyzer.analyze(ac);
    expect(analysis.testabilityScore).toBeGreaterThan(0.8);
    expect(analysis.entities.actor).toBe('user');
    expect(analysis.entities.action).toBe('submit the login form');
    expect(analysis.entities.expectedResult).toContain('redirected to /dashboard');
  });

  it('should detect missing negative scenarios', () => {
    const criteria = [
      'User can login with valid credentials',
      'User sees dashboard after login'
    ];
    const gaps = analyzer.detectGaps(criteria);
    expect(gaps.missingCategories).toContain('NEGATIVE_SCENARIO');
    expect(gaps.suggestions).toContain('Add test for invalid credentials');
  });
});
```

#### Test Case Generator Unit Tests

**What to test:**

| Test Category | Example Test Cases | Priority |
|--------------|-------------------|----------|
| Output structure | Generated test cases match expected JSON schema | P0 |
| Test type coverage | Generates positive, negative, edge, boundary cases | P0 |
| Step completeness | Each test case has preconditions, steps, expected results | P0 |
| Deduplication | No duplicate test cases generated | P1 |
| Priority assignment | Test cases have appropriate priority levels | P1 |
| Traceability | Each test case links back to source AC | P0 |

#### Automation Script Generator Unit Tests

**What to test:**

| Test Category | Example Test Cases | Priority |
|--------------|-------------------|----------|
| Code validity | Generated scripts are syntactically valid | P0 |
| Framework compliance | Scripts use correct Playwright/Selenium API | P0 |
| Assertion generation | Appropriate assertions for each expected result | P0 |
| Wait strategy | Proper waits (not hardcoded sleeps) | P1 |
| Page object pattern | Generates page objects when appropriate | P2 |
| Error handling | Scripts include try/catch and cleanup | P1 |

### 2.2.2 AI Layer Unit Tests

#### Prompt Validation Tests

```javascript
describe('PromptBuilder', () => {

  it('should construct prompt within token limit', () => {
    const jiraData = largeJiraTicket();
    const prompt = promptBuilder.build(jiraData);
    const tokenCount = tokenizer.count(prompt);
    expect(tokenCount).toBeLessThan(MAX_TOKENS);
  });

  it('should include system instructions in every prompt', () => {
    const prompt = promptBuilder.build(minimalJiraTicket());
    expect(prompt.systemMessage).toContain('You are a QA engineer');
    expect(prompt.systemMessage).toContain('Generate test cases');
  });

  it('should sanitize PII from Jira data before including in prompt', () => {
    const ticket = mockJiraTicket({
      description: 'User john.doe@company.com should be able to login'
    });
    const prompt = promptBuilder.build(ticket);
    expect(prompt.userMessage).not.toContain('john.doe@company.com');
    expect(prompt.userMessage).toContain('[EMAIL_REDACTED]');
  });

  it('should use correct prompt version from configuration', () => {
    const prompt = promptBuilder.build(minimalJiraTicket(), { version: 'v2.3' });
    expect(prompt.metadata.promptVersion).toBe('v2.3');
  });
});
```

#### Output Schema Validation Tests

```javascript
describe('LLMOutputValidator', () => {

  it('should validate correct test case schema', () => {
    const validOutput = {
      testCases: [{
        id: 'TC-001',
        title: 'Verify successful login',
        type: 'positive',
        priority: 'high',
        preconditions: ['User exists in system'],
        steps: [
          { action: 'Navigate to login page', expected: 'Login page displayed' },
          { action: 'Enter valid username', expected: 'Username field populated' }
        ],
        expectedResult: 'User is redirected to dashboard'
      }]
    };
    expect(validator.validate(validOutput)).toEqual({ valid: true, errors: [] });
  });

  it('should reject output missing required fields', () => {
    const invalidOutput = { testCases: [{ title: 'Incomplete test' }] };
    const result = validator.validate(invalidOutput);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('Missing required field: steps');
    expect(result.errors).toContain('Missing required field: expectedResult');
  });

  it('should reject output that is not valid JSON', () => {
    const rawOutput = 'Here are some test cases:\n1. Test login\n2. Test logout';
    const result = validator.validate(rawOutput);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('Output is not valid JSON');
  });
});
```

### 2.2.3 Unit Testing Tools & Configuration

| Tool | Usage | Configuration |
|------|-------|---------------|
| **Jest** | JavaScript/TypeScript unit tests | `jest.config.ts` with coverage thresholds |
| **JUnit 5** | Java backend service tests | Maven/Gradle with Surefire plugin |
| **Mockito** | Java mocking framework | Integrated with JUnit 5 |
| **ts-mockito** | TypeScript mocking | Used for LLM client mocking |
| **faker.js** | Test data generation | Deterministic seeds for reproducibility |

**Coverage Requirements:**

```json
{
  "coverageThreshold": {
    "global": {
      "branches": 80,
      "functions": 85,
      "lines": 85,
      "statements": 85
    },
    "./src/ai/": {
      "branches": 90,
      "functions": 90,
      "lines": 90,
      "statements": 90
    }
  }
}
```

---

## 2.3 Integration Testing

### 2.3.1 Jira API <-> Backend Integration

| Test ID | Test Scenario | Type | Priority |
|---------|--------------|------|----------|
| INT-JIRA-001 | Fetch ticket by ID with all fields | Real API | P0 |
| INT-JIRA-002 | Fetch tickets by JQL query | Real API | P0 |
| INT-JIRA-003 | Post comment to ticket | Real API | P0 |
| INT-JIRA-004 | Update ticket status/fields | Real API | P0 |
| INT-JIRA-005 | Attach file to ticket | Real API | P1 |
| INT-JIRA-006 | Handle expired OAuth token gracefully | Mock | P0 |
| INT-JIRA-007 | Handle Jira API rate limiting (429) | Mock | P1 |
| INT-JIRA-008 | Handle Jira downtime (5xx) | Mock | P0 |
| INT-JIRA-009 | Validate webhook payload processing | Mock | P1 |
| INT-JIRA-010 | Handle pagination for large query results | Real API | P1 |

**Mock vs Real Strategy:**

```
┌─────────────────────────────────────────────────────┐
│              INTEGRATION TEST STRATEGY               │
├────────────────────┬────────────────────────────────┤
│    CI Pipeline     │    Nightly / Pre-Release       │
│  (Every PR)        │    (Scheduled)                 │
├────────────────────┼────────────────────────────────┤
│  WireMock stubs    │  Real Jira sandbox instance    │
│  for Jira API      │  with test project             │
│                    │                                │
│  Recorded HTTP     │  Real LLM API with             │
│  responses for LLM │  budget-capped account         │
│                    │                                │
│  Docker containers │  Staging environment with      │
│  for dependencies  │  real browser grid             │
├────────────────────┼────────────────────────────────┤
│  Speed: ~5 min     │  Speed: ~20 min               │
│  Cost: $0          │  Cost: ~$5/run (LLM API)      │
└────────────────────┴────────────────────────────────┘
```

### 2.3.2 Backend <-> LLM API Integration

| Test ID | Test Scenario | Type | Priority |
|---------|--------------|------|----------|
| INT-LLM-001 | Send prompt and receive valid JSON response | Real/Mock | P0 |
| INT-LLM-002 | Handle token limit exceeded error | Mock | P0 |
| INT-LLM-003 | Handle API timeout (>30s response) | Mock | P0 |
| INT-LLM-004 | Handle rate limiting from LLM provider | Mock | P1 |
| INT-LLM-005 | Verify prompt is within token budget | Unit+Int | P0 |
| INT-LLM-006 | Handle malformed/non-JSON LLM response | Mock | P0 |
| INT-LLM-007 | Verify retry logic on transient failures | Mock | P1 |
| INT-LLM-008 | Handle model version deprecation | Mock | P2 |
| INT-LLM-009 | Validate streaming vs batch response handling | Real | P1 |
| INT-LLM-010 | Measure response latency within SLA | Real | P1 |

### 2.3.3 Backend <-> Automation Engine Integration

| Test ID | Test Scenario | Type | Priority |
|---------|--------------|------|----------|
| INT-AUT-001 | Submit generated script for execution | Real | P0 |
| INT-AUT-002 | Receive execution results (pass/fail) | Real | P0 |
| INT-AUT-003 | Handle browser launch failure | Mock | P0 |
| INT-AUT-004 | Capture screenshots on failure | Real | P1 |
| INT-AUT-005 | Handle grid/cloud capacity exhaustion | Mock | P1 |
| INT-AUT-006 | Verify parallel execution of multiple scripts | Real | P1 |
| INT-AUT-007 | Validate cleanup after execution (browser close, temp files) | Real | P1 |
| INT-AUT-008 | Handle script timeout (execution exceeds limit) | Mock | P0 |

### 2.3.4 Report Generation Pipeline Integration

| Test ID | Test Scenario | Type | Priority |
|---------|--------------|------|----------|
| INT-RPT-001 | Generate HTML report from execution results | Real | P0 |
| INT-RPT-002 | Generate PDF report with correct layout | Real | P1 |
| INT-RPT-003 | Include screenshots in report | Real | P1 |
| INT-RPT-004 | Handle partial results (some tests incomplete) | Real | P1 |
| INT-RPT-005 | Verify report data matches execution data | Real | P0 |

### 2.3.5 Integration Testing Tools

| Tool | Purpose |
|------|---------|
| **WireMock / MSW** | HTTP API mocking for Jira and LLM APIs |
| **Testcontainers** | Spin up Docker containers for databases, queues |
| **Supertest** | HTTP assertion library for REST API testing |
| **REST Assured** | Java-based REST API testing |
| **nock** | HTTP request interception for Node.js |

---

## 2.4 End-to-End (E2E) Testing

### 2.4.1 Full User Journey Tests

#### Journey 1: Jira Ticket → Test Case → Execution → Report → Jira Update

```
┌──────────┐     ┌────────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Create   │────▶│  Review    │────▶│  Execute │────▶│  View    │────▶│  Verify  │
│  Jira     │     │  Generated │     │  Tests   │     │  Report  │     │  Jira    │
│  Ticket   │     │  Test Cases│     │          │     │          │     │  Updated │
└──────────┘     └────────────┘     └──────────┘     └──────────┘     └──────────┘
```

**Test Steps:**

| Step | Action | Verification |
|------|--------|-------------|
| 1 | Create Jira ticket with well-defined AC | Ticket created successfully |
| 2 | Trigger test generation for ticket | Test cases appear in review queue |
| 3 | Review generated test cases | All ACs are covered, structure is valid |
| 4 | Approve test cases | Status changes to "Ready for Execution" |
| 5 | Trigger test execution | Execution starts, progress visible |
| 6 | Wait for execution completion | All tests reach terminal state |
| 7 | Verify report generated | HTML/PDF report available with correct data |
| 8 | Verify Jira updated | Comment added, status updated, attachment linked |

#### Journey 2: Failed Test → Bug Creation → Re-test

| Step | Action | Verification |
|------|--------|-------------|
| 1 | Execute test suite with known failures | Failures detected correctly |
| 2 | View failure details | Screenshots, logs, root cause available |
| 3 | Verify automatic bug creation | New Jira bug created with correct details |
| 4 | Fix target application | Bug is resolved |
| 5 | Re-trigger test execution | Previously failed tests now pass |
| 6 | Verify Jira bug updated | Bug status updated to "Verified" |

#### Journey 3: Bulk Ticket Processing

| Step | Action | Verification |
|------|--------|-------------|
| 1 | Select multiple Jira tickets (5-10) | All selected correctly |
| 2 | Trigger batch test generation | All tickets processed |
| 3 | Monitor progress | Real-time status for each ticket |
| 4 | Review results | All tickets have test cases |
| 5 | Execute all test suites | Parallel execution works correctly |
| 6 | Verify all Jira tickets updated | Each ticket has its own results |

### 2.4.2 Role-Based Flow Tests

#### Project Manager Flow

| Test | Action | Expected |
|------|--------|----------|
| PM-001 | View dashboard with project metrics | Metrics displayed correctly |
| PM-002 | Filter results by sprint/epic | Filtering works as expected |
| PM-003 | Export summary report | PDF/CSV export successful |
| PM-004 | Cannot modify test cases | Edit actions are disabled |
| PM-005 | View Jira sync status | Sync status is visible and accurate |

#### Tester Flow

| Test | Action | Expected |
|------|--------|----------|
| TST-001 | Trigger test generation for a ticket | Generation starts within 5s |
| TST-002 | Edit generated test cases | Changes saved correctly |
| TST-003 | Add manual test case | Manual case integrated with generated ones |
| TST-004 | Execute selected test cases | Only selected cases run |
| TST-005 | Re-run failed tests | Only failed tests re-execute |
| TST-006 | View detailed execution logs | Logs include steps, timestamps, screenshots |

#### Admin Flow

| Test | Action | Expected |
|------|--------|----------|
| ADM-001 | Configure Jira connection | Connection established and verified |
| ADM-002 | Configure LLM settings (model, temperature) | Settings saved, reflected in generation |
| ADM-003 | Manage user roles and permissions | Role changes take effect immediately |
| ADM-004 | View system health dashboard | All services show correct status |
| ADM-005 | Configure automation engine (browser, grid) | Settings applied to next execution |
| ADM-006 | Purge old test data | Data removed, no orphaned records |

### 2.4.3 E2E Testing Tools & Configuration

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **Playwright** | Browser automation for E2E tests | Multi-browser, headless/headed |
| **Cypress** | Alternative E2E framework (if SPA) | For component + E2E hybrid |
| **Allure** | Test reporting | Integrated with Playwright |
| **Docker Compose** | Full environment orchestration | All services in containers |

**E2E Test Environment:**

```yaml
# docker-compose.e2e.yml
services:
  app:
    image: ai-test-platform:latest
    environment:
      - JIRA_URL=http://jira-mock:8080
      - LLM_API_URL=http://llm-mock:9090
  
  jira-mock:
    image: wiremock/wiremock:latest
    volumes:
      - ./e2e/mocks/jira:/home/wiremock/mappings
  
  llm-mock:
    image: wiremock/wiremock:latest
    volumes:
      - ./e2e/mocks/llm:/home/wiremock/mappings
  
  browser-grid:
    image: selenium/standalone-chrome:latest
```

---

## 2.5 Test Layer Responsibilities Summary

| Aspect | Unit | Integration | E2E |
|--------|------|------------|-----|
| **Scope** | Single function/class | Two+ services | Full user journey |
| **Speed** | < 50ms each | < 5s each | < 5min each |
| **Isolation** | Full (mocked deps) | Partial (real APIs) | None (full stack) |
| **Who writes** | Developers | Dev + QA | QA Engineers |
| **When runs** | Every commit | Every PR | Nightly + Pre-release |
| **Flakiness tolerance** | 0% | < 2% | < 5% |
| **Coverage focus** | Logic correctness | Contract validation | Business flow |

---

*Previous: [01 — Testing Goals](./01-testing-goals-quality-objectives.md) | Next: [03 — AI-Specific Testing](./03-ai-specific-testing-strategy.md)*
