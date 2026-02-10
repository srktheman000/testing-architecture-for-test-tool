# 11 — Test Data Strategy

> **Purpose:** Define the strategy for test data management including Jira ticket mocks, synthetic data generation, environment-specific data, and cleanup procedures.

---

## 11.1 Test Data Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    TEST DATA ECOSYSTEM                            │
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │  STATIC DATA     │    │  DYNAMIC DATA    │                   │
│  │                  │    │                  │                   │
│  │  • Golden dataset │    │  • Faker.js      │                   │
│  │  • Fixture files  │    │  • Factory-bot   │                   │
│  │  • Mock responses │    │  • Random seeds  │                   │
│  │  • Baseline data  │    │  • DB seeding    │                   │
│  └────────┬─────────┘    └────────┬─────────┘                   │
│           │                       │                              │
│           ▼                       ▼                              │
│  ┌──────────────────────────────────────────────┐               │
│  │           TEST DATA MANAGER                   │               │
│  │  • Select data based on test context         │               │
│  │  • Isolate data per test / suite             │               │
│  │  • Manage lifecycle (create → use → cleanup) │               │
│  └──────────────────────────────────────────────┘               │
│                          │                                       │
│             ┌────────────┼────────────┐                          │
│             ▼            ▼            ▼                          │
│       ┌──────────┐ ┌──────────┐ ┌──────────┐                   │
│       │  Unit    │ │  Integ-  │ │  E2E     │                   │
│       │  Tests   │ │  ration  │ │  Tests   │                   │
│       │  (mocks) │ │  (seeds) │ │  (live)  │                   │
│       └──────────┘ └──────────┘ └──────────┘                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 11.2 Jira Ticket Mocks

### 11.2.1 Mock Ticket Library

A comprehensive library of mock Jira tickets covering all test scenarios.

**Mock Categories:**

| Category | Count | Purpose |
|----------|-------|---------|
| Standard stories | 20 | Normal user stories with clear ACs |
| Complex stories | 10 | Multi-AC stories with dependencies |
| Bug tickets | 10 | Bug reports with repro steps |
| Edge case tickets | 15 | Minimal, maximal, ambiguous tickets |
| Security-sensitive | 5 | Tickets containing PII, credentials |
| Non-English | 5 | Multi-language ticket content |
| Empty/Invalid | 10 | Missing fields, malformed data |

### 11.2.2 Mock Ticket Schema

```javascript
// test-data/mocks/jira-tickets/factory.js
const { faker } = require('@faker-js/faker');

class JiraTicketFactory {

  static standard(overrides = {}) {
    return {
      key: overrides.key || `PROJ-${faker.number.int({ min: 100, max: 9999 })}`,
      fields: {
        summary: overrides.summary || faker.lorem.sentence(),
        description: overrides.description || this._generateDescription(),
        issuetype: { name: overrides.type || 'Story' },
        priority: { name: overrides.priority || 'Medium' },
        status: { name: overrides.status || 'To Do' },
        assignee: {
          displayName: faker.person.fullName(),
          emailAddress: faker.internet.email()
        },
        reporter: {
          displayName: faker.person.fullName(),
          emailAddress: faker.internet.email()
        },
        labels: overrides.labels || ['test-automation'],
        created: faker.date.recent().toISOString(),
        updated: faker.date.recent().toISOString(),
        customfield_10001: overrides.storyPoints || faker.number.int({ min: 1, max: 13 }),
        ...overrides.fields
      }
    };
  }

  static withAcceptanceCriteria(criteria, overrides = {}) {
    const acText = criteria.map((ac, i) => `* AC-${i + 1}: ${ac}`).join('\n');
    return this.standard({
      ...overrides,
      description: `h2. Description\n${faker.lorem.paragraph()}\n\nh2. Acceptance Criteria\n${acText}`
    });
  }

  static loginFlow() {
    return this.withAcceptanceCriteria([
      'Given valid credentials, when user submits login form, then user is redirected to dashboard',
      'Given invalid password, when user submits login form, then error message "Invalid credentials" is displayed',
      'Given unregistered email, when user submits login form, then error message "Account not found" is displayed',
      'Password field should mask input characters',
      'Login button should be disabled until both email and password fields are filled',
      'User can toggle password visibility'
    ], {
      key: 'PROJ-101',
      summary: 'User Login with Email and Password'
    });
  }

  static crudOperation() {
    return this.withAcceptanceCriteria([
      'User can create a new item with name, description, and category',
      'Required field validation shows inline errors',
      'Successful creation shows confirmation toast',
      'User can view item details page',
      'User can edit existing item fields',
      'User can delete item with confirmation dialog',
      'Deleted items are removed from the list immediately'
    ], {
      key: 'PROJ-201',
      summary: 'CRUD Operations for Product Catalog'
    });
  }

  static ambiguous() {
    return this.withAcceptanceCriteria([
      'The page should load fast',
      'Everything should work properly',
      'Users should be able to do their tasks'
    ], {
      key: 'PROJ-301',
      summary: 'Improve User Experience'
    });
  }

  static withPII() {
    return this.standard({
      key: 'PROJ-401',
      summary: 'Fix login for specific user',
      description: `User john.doe@company.com (ID: 12345) reported that login 
        fails from IP 10.0.0.15. Their SSN 123-45-6789 was used for verification.
        Contact them at +1-555-123-4567.`
    });
  }

  static empty() {
    return {
      key: 'PROJ-501',
      fields: {
        summary: '',
        description: null,
        issuetype: { name: 'Story' },
        priority: null,
        status: { name: 'To Do' }
      }
    };
  }

  static _generateDescription() {
    return `h2. Description\n${faker.lorem.paragraphs(2)}\n\nh2. Acceptance Criteria\n* ${faker.lorem.sentence()}\n* ${faker.lorem.sentence()}\n* ${faker.lorem.sentence()}`;
  }
}

module.exports = { JiraTicketFactory };
```

### 11.2.3 Jira API Mock Responses

```json
// test-data/mocks/jira-api/get-ticket-200.json
{
  "id": "10001",
  "key": "PROJ-123",
  "self": "https://jira.example.com/rest/api/3/issue/10001",
  "fields": {
    "summary": "User Login with Email and Password",
    "description": {
      "type": "doc",
      "version": 1,
      "content": [
        {
          "type": "heading",
          "attrs": { "level": 2 },
          "content": [{ "type": "text", "text": "Acceptance Criteria" }]
        },
        {
          "type": "bulletList",
          "content": [
            {
              "type": "listItem",
              "content": [{
                "type": "paragraph",
                "content": [{
                  "type": "text",
                  "text": "Given valid credentials, user is redirected to dashboard"
                }]
              }]
            }
          ]
        }
      ]
    },
    "issuetype": { "name": "Story", "id": "10001" },
    "priority": { "name": "High", "id": "2" },
    "status": { "name": "In Progress", "id": "3" },
    "labels": ["authentication", "sprint-42"],
    "created": "2026-02-01T10:00:00.000+0000",
    "updated": "2026-02-05T14:30:00.000+0000"
  }
}
```

---

## 11.3 Synthetic Test Data

### 11.3.1 Data Generation Strategies

| Data Type | Generation Method | Determinism |
|-----------|------------------|-------------|
| User credentials | Faker.js with fixed seed | Reproducible |
| Form field data | Category-specific generators | Reproducible |
| Edge case data | Predefined constants | Deterministic |
| Boundary values | Computed from field constraints | Deterministic |
| Random data | Faker.js with random seed | Non-reproducible (logged) |

### 11.3.2 Synthetic Data Generators

```javascript
// test-data/generators/form-data.js
class FormDataGenerator {

  static loginForm(variant = 'valid') {
    const generators = {
      valid: () => ({
        email: 'test.user@example.com',
        password: 'ValidP@ss123!',
      }),
      invalidEmail: () => ({
        email: 'not-an-email',
        password: 'ValidP@ss123!',
      }),
      emptyFields: () => ({
        email: '',
        password: '',
      }),
      sqlInjection: () => ({
        email: "' OR 1=1 --",
        password: "' OR 1=1 --",
      }),
      xss: () => ({
        email: '<script>alert("xss")</script>',
        password: '<img onerror="alert(1)" src="x">',
      }),
      longValues: () => ({
        email: 'a'.repeat(256) + '@example.com',
        password: 'x'.repeat(1000),
      }),
      unicode: () => ({
        email: 'user@examplé.com',
        password: 'p@$$wörd_日本語',
      }),
      specialChars: () => ({
        email: 'user+tag@example.com',
        password: 'P@$$w0rd!#%&*',
      }),
    };

    if (!generators[variant]) throw new Error(`Unknown variant: ${variant}`);
    return generators[variant]();
  }

  static searchForm(variant = 'standard') {
    const generators = {
      standard: () => ({
        query: 'laptop computer',
        category: 'Electronics',
        minPrice: 100,
        maxPrice: 2000,
      }),
      empty: () => ({
        query: '',
        category: '',
        minPrice: null,
        maxPrice: null,
      }),
      boundaryPrices: () => ({
        query: 'item',
        minPrice: 0,
        maxPrice: 999999.99,
      }),
      inversePrices: () => ({
        query: 'item',
        minPrice: 500,
        maxPrice: 100, // min > max
      }),
    };

    return generators[variant]();
  }
}
```

### 11.3.3 LLM Response Mocks

```javascript
// test-data/mocks/llm-responses/test-case-generation.js
const llmResponses = {

  validLoginTestCases: {
    testCases: [
      {
        id: 'TC-001',
        title: 'Verify successful login with valid credentials',
        type: 'positive',
        priority: 'critical',
        preconditions: ['User account exists', 'User is on login page'],
        steps: [
          { stepNumber: 1, action: 'Enter valid email', expectedResult: 'Email field populated' },
          { stepNumber: 2, action: 'Enter valid password', expectedResult: 'Password field populated (masked)' },
          { stepNumber: 3, action: 'Click Login button', expectedResult: 'User redirected to dashboard' }
        ],
        expectedResult: 'User is successfully logged in and sees the dashboard',
        traceability: { acceptanceCriteriaIndex: 0, jiraTicketId: 'PROJ-101' }
      },
      // ... more test cases
    ],
    metadata: {
      generatedAt: '2026-02-10T10:00:00Z',
      promptVersion: 'v1.2.0',
      modelVersion: 'gpt-4-turbo-2026-01',
      confidence: 0.92,
      tokensUsed: 2847,
      processingTimeMs: 8500
    }
  },

  malformedOutput: 'This is not JSON. Here are some test ideas:\n1. Test login\n2. Test logout',

  emptyTestCases: {
    testCases: [],
    metadata: { generatedAt: '2026-02-10T10:00:00Z', confidence: 0.1 }
  },

  hallucinated: {
    testCases: [{
      id: 'TC-001',
      title: 'Test payment processing',  // Not in original ticket
      type: 'positive',
      steps: [
        { stepNumber: 1, action: 'Go to https://fake-url.com/pay', expectedResult: 'Payment page loads' }
      ],
      expectedResult: 'Payment succeeds'
    }],
    metadata: { confidence: 0.45 }
  }
};
```

---

## 11.4 Environment-Specific Test Data

### 11.4.1 Environment Data Matrix

| Environment | Data Source | User Accounts | Jira Project | Reset Frequency |
|-------------|-----------|---------------|-------------|-----------------|
| **Local dev** | In-memory / SQLite | Hardcoded fixtures | Mock (WireMock) | Every test run |
| **CI** | Docker PostgreSQL | Seeded from fixtures | Mock (WireMock) | Every pipeline run |
| **QA** | Shared PostgreSQL | Managed test accounts | Dedicated test project | Daily (overnight) |
| **UAT** | Production-mirror DB | Anonymized real users | UAT Jira project | Weekly |
| **Staging** | Sanitized production | Service accounts only | Staging Jira | Before each release |

### 11.4.2 Environment Configuration

```javascript
// test-data/config/environments.js
const environments = {
  local: {
    database: 'sqlite::memory:',
    jira: {
      baseUrl: 'http://localhost:8080',
      project: 'TEST',
      type: 'mock'
    },
    llm: {
      baseUrl: 'http://localhost:9090',
      type: 'mock'
    },
    users: {
      admin: { email: 'admin@test.local', password: 'admin123' },
      tester: { email: 'tester@test.local', password: 'tester123' },
    }
  },

  ci: {
    database: process.env.DATABASE_URL || 'postgresql://test:test@localhost:5432/test',
    jira: {
      baseUrl: process.env.JIRA_MOCK_URL || 'http://wiremock:8080',
      project: 'TEST',
      type: 'mock'
    },
    llm: {
      baseUrl: process.env.LLM_MOCK_URL || 'http://wiremock:8081',
      type: 'mock'
    }
  },

  qa: {
    database: process.env.QA_DATABASE_URL,
    jira: {
      baseUrl: 'https://jira.example.com',
      project: 'QA-TEST',
      type: 'real',
      apiToken: process.env.JIRA_QA_TOKEN
    },
    llm: {
      baseUrl: 'https://api.openai.com/v1',
      type: 'real',
      apiKey: process.env.LLM_QA_KEY,
      budgetLimit: '$10/day'
    }
  }
};
```

---

## 11.5 Data Cleanup Strategy

### 11.5.1 Cleanup Principles

1. **Every test cleans up after itself** — No test leaves data that affects other tests
2. **Cleanup runs even on failure** — Use `afterEach` / `finally` blocks
3. **Environment reset as safety net** — Nightly reset of shared environments
4. **Idempotent cleanup** — Cleanup operations are safe to run multiple times

### 11.5.2 Cleanup Implementation

```javascript
// test-data/cleanup/cleanup-manager.js
class CleanupManager {
  constructor() {
    this.registry = [];
  }

  // Register a resource for cleanup
  register(type, identifier, cleanupFn) {
    this.registry.push({
      type,
      identifier,
      cleanupFn,
      registeredAt: Date.now()
    });
  }

  // Run all registered cleanups (LIFO order)
  async cleanup() {
    const errors = [];
    for (const item of this.registry.reverse()) {
      try {
        await item.cleanupFn();
        console.log(`Cleaned up ${item.type}: ${item.identifier}`);
      } catch (error) {
        errors.push({ item, error });
        console.error(`Failed to clean up ${item.type}: ${item.identifier}`, error);
      }
    }
    this.registry = [];
    if (errors.length > 0) {
      console.warn(`${errors.length} cleanup failures occurred`);
    }
  }
}

// Usage in tests
describe('Test with cleanup', () => {
  const cleanup = new CleanupManager();

  afterEach(async () => {
    await cleanup.cleanup();
  });

  it('should create and clean up test data', async () => {
    // Create test ticket in Jira
    const ticket = await jira.createTicket(testData);
    cleanup.register('jira-ticket', ticket.key, () => jira.deleteTicket(ticket.key));

    // Create test execution record
    const execution = await db.createExecution(executionData);
    cleanup.register('db-execution', execution.id, () => db.deleteExecution(execution.id));

    // Create report file
    const reportPath = await reportGenerator.generate(results);
    cleanup.register('file', reportPath, () => fs.unlink(reportPath));

    // ... test assertions ...
  });
});
```

### 11.5.3 Environment Reset Schedule

| Environment | Reset Type | Schedule | Method |
|-------------|-----------|----------|--------|
| Local | Full reset | Every test run | Drop & recreate SQLite |
| CI | Full reset | Every pipeline | Docker volume recreation |
| QA | Selective cleanup | Nightly 01:00 UTC | Cleanup script + DB truncate |
| QA | Full reset | Weekly Sunday 00:00 | DB restore from clean snapshot |
| UAT | Anonymized refresh | Before each release | ETL from production + anonymization |
| Staging | Sanitized restore | Monthly | Full restore from production backup |

### 11.5.4 Data Isolation Strategy

```
┌──────────────────────────────────────────┐
│  PARALLEL TEST EXECUTION                  │
│                                          │
│  Test A (user: test-a@example.com)       │
│  └─ Jira Project: TEST-A                │
│  └─ DB Schema: test_a                   │
│  └─ Reports: /reports/test-a/           │
│                                          │
│  Test B (user: test-b@example.com)       │
│  └─ Jira Project: TEST-B                │
│  └─ DB Schema: test_b                   │
│  └─ Reports: /reports/test-b/           │
│                                          │
│  No shared state between A and B         │
└──────────────────────────────────────────┘
```

---

## 11.6 Test Data Versioning

Test data (especially golden datasets and fixture files) is versioned alongside code:

```
test-data/
├── fixtures/
│   ├── v1/
│   │   ├── jira-tickets.json
│   │   └── expected-outputs.json
│   └── v2/
│       ├── jira-tickets.json
│       └── expected-outputs.json
├── golden-datasets/
│   └── (see Document 03)
├── mocks/
│   ├── jira-api/
│   ├── llm-responses/
│   └── wiremock-mappings/
├── generators/
│   ├── form-data.js
│   ├── jira-ticket-factory.js
│   └── user-factory.js
└── cleanup/
    ├── cleanup-manager.js
    └── environment-reset.sh
```

---

*Previous: [10 — CI/CD Testing Strategy](./10-cicd-testing-strategy.md) | Next: [12 — Monitoring & Production Testing](./12-monitoring-production-testing.md)*
