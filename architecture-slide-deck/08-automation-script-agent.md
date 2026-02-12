# Slide 8 — Module 4: Automation Script Agent

## From Test Cases to Executable Code

---

## Module Overview

The Automation Script Agent receives approved test cases and **generates executable automation code** — supporting UI (Playwright/Selenium), API (REST Assured/Supertest), and database validation scripts.

> **Architect's Standard:** Generated code must be production-quality: compilable, maintainable, following established patterns (POM), and robust enough to survive real-world execution.

---

## Responsibilities

| Responsibility | What It Does | Why It Matters |
|---------------|-------------|----------------|
| **Convert Test Cases into Code** | Transform structured TCs into executable scripts with locators, actions, assertions | This is where testing intent becomes testable reality |
| **Support UI, API, DB Automation** | Generate scripts for browser interactions, REST API calls, and database queries | Real applications need multi-layer validation |
| **Follow Framework Patterns** | Use Page Object Model, data-driven design, proper waits, error handling | Maintainability and team adoption depend on code quality |

---

## Script Generation Pipeline

```
┌──────────────────────┐
│  Approved Test Cases  │
│  (from Module 3)      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│                  AUTOMATION SCRIPT AGENT                          │
│                                                                  │
│  Step 1: Script Type Detection                                   │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ Analyze TC steps to determine script type:              │     │
│  │   • UI interactions → Playwright/Selenium script        │     │
│  │   • API calls → REST Assured/Supertest script           │     │
│  │   • Data validation → SQL/DB query script               │     │
│  │   • Hybrid → Combined script with multiple layers       │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  Step 2: Code Generation                                         │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ For UI scripts:                                         │     │
│  │   • Generate Page Object classes                        │     │
│  │   • Create locator strategies (data-testid > id > CSS)  │     │
│  │   • Add explicit waits (no hard-coded sleeps)           │     │
│  │   • Include assertions matching expected results        │     │
│  │                                                         │     │
│  │ For API scripts:                                        │     │
│  │   • Generate request builders with headers/body         │     │
│  │   • Add response validation (status, schema, data)      │     │
│  │   • Include auth token management                       │     │
│  │                                                         │     │
│  │ For DB scripts:                                         │     │
│  │   • Generate parameterized queries                      │     │
│  │   • Add result set validation                           │     │
│  │   • Include connection management and cleanup           │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  Step 3: Validation & Quality Check                              │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ Static analysis: syntax check, lint, compile            │     │
│  │ Pattern compliance: POM structure, naming conventions    │     │
│  │ Locator robustness score                                │     │
│  │ Assertion completeness check                            │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Testing Strategy

### 1. Script Compilation Success

Every generated script must pass these gates before it reaches the Execution Engine:

```
COMPILATION GATE:
  ✓ Syntax valid? (Can the language parser/compiler process it?)
  ✓ Imports resolved? (All dependencies available?)
  ✓ No undefined variables? (Every variable is declared and used?)
  ✓ Linter passes? (ESLint/Pylint rules satisfied?)
  
  Target: >= 95% of generated scripts compile successfully
  Alert:  < 90% compilation rate
```

### 2. Locator Robustness

| Locator Strategy | Robustness Score | When to Use |
|-----------------|-----------------|-------------|
| `data-testid` | 10/10 | Always preferred — survives UI redesigns |
| `id` attribute | 8/10 | Good if IDs are stable and unique |
| `name` attribute | 7/10 | Acceptable for form elements |
| CSS selector (class-based) | 5/10 | Risky — classes change frequently |
| XPath (absolute) | 2/10 | Fragile — any DOM change breaks it |
| XPath (with index) | 1/10 | Never acceptable — breaks with any list change |

**Validation Rule:** Generated scripts must have an average locator robustness score >= 7/10.

### 3. Framework Compliance (Page Object Model)

```
COMPLIANCE CHECKLIST:

  Structure:
    ✓ Page classes are separate from test classes
    ✓ Locators are defined as class properties, not inline
    ✓ Actions are methods on page objects (login(), fillForm())
    ✓ Test files import and use page objects
  
  Naming:
    ✓ Page classes: LoginPage, DashboardPage
    ✓ Test files: login.test.ts, dashboard.spec.ts
    ✓ Methods: descriptive verbs (clickLoginButton, enterEmail)
  
  Practices:
    ✓ No hard-coded waits (sleep/setTimeout)
    ✓ Explicit waits (waitForSelector, waitForResponse)
    ✓ Test data is parameterized, not embedded
    ✓ Setup/teardown hooks for test isolation
```

---

## Test Cases for This Module

| TC ID | Test Case | Priority | Type |
|-------|-----------|----------|------|
| AS-001 | UI test case → generates valid Playwright script that compiles | P0 | Positive |
| AS-002 | API test case → generates valid REST request with assertions | P0 | Positive |
| AS-003 | Generated script uses POM structure | P0 | Compliance |
| AS-004 | All locators use stable strategies (data-testid, id) | P1 | Quality |
| AS-005 | No hard-coded sleeps in generated code | P1 | Quality |
| AS-006 | Every expected result maps to an assertion in code | P0 | Completeness |
| AS-007 | Generated script passes ESLint/static analysis | P1 | Quality |
| AS-008 | Ambiguous TC step → agent flags as non-automatable | P1 | Edge Case |
| AS-009 | TC with 20+ steps → script generated without truncation | P2 | Scalability |
| AS-010 | Same TC run 3 times → same script structure (determinism) | P1 | Reliability |
| AS-011 | Script with invalid locator → compilation catches it | P1 | Validation |
| AS-012 | DB validation TC → generates parameterized SQL | P2 | Positive |

---

## Failure Handling — Self-Healing

The Automation Script Agent has built-in self-healing capabilities:

### Auto-Heal Locators

```
SCENARIO: A UI element's ID changes from "login-btn" to "submit-login-btn"

TRADITIONAL AUTOMATION:
  ✗ Test fails → QA manually updates locator → Commits → Reruns
  Time to recover: hours to days

SELF-HEALING AGENT:
  Step 1: Detect locator failure (element not found)
  Step 2: Search DOM for similar elements (text match, nearby elements, role)
  Step 3: Propose alternative locator with confidence score
  Step 4: If confidence > 0.8 → auto-update and retry
  Step 5: If confidence < 0.8 → flag for human review
  Time to recover: seconds to minutes
```

### Regenerate Scripts

```
SCENARIO: Application flow changed (new step added to checkout process)

SELF-HEALING FLOW:
  1. Execution fails at unexpected page/state
  2. RCA Agent identifies "flow change" as root cause
  3. Supervisor triggers Script Agent re-generation
  4. Script Agent re-analyzes the test case against current app state
  5. New script generated with updated flow
  6. Validation gate → Re-execution
```

---

## Sample Generated Script (Playwright + POM)

```typescript
// pages/LoginPage.ts
import { Page, Locator } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly loginButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.locator('[data-testid="email-input"]');
    this.passwordInput = page.locator('[data-testid="password-input"]');
    this.loginButton = page.locator('[data-testid="login-button"]');
    this.errorMessage = page.locator('[data-testid="error-message"]');
  }

  async login(email: string, password: string): Promise<void> {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
  }

  async getErrorMessage(): Promise<string> {
    await this.errorMessage.waitFor({ state: 'visible' });
    return await this.errorMessage.textContent() ?? '';
  }
}
```

```typescript
// tests/login.spec.ts
import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';

test.describe('PROJ-123: User Login', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await page.goto('/login');
  });

  test('TC-PROJ123-AC1-001: Login with valid credentials', async ({ page }) => {
    await loginPage.login('test@example.com', 'ValidPass@123');
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.locator('[data-testid="welcome-message"]')).toBeVisible();
  });

  test('TC-PROJ123-AC1-002: Login with invalid password', async () => {
    await loginPage.login('test@example.com', 'WrongPass');
    const error = await loginPage.getErrorMessage();
    expect(error).toContain('Invalid credentials');
  });
});
```

---

## Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Script Compilation Success Rate | >= 95% | < 90% |
| Locator Robustness Score (avg) | >= 7/10 | < 5/10 |
| POM Compliance Rate | >= 95% | < 85% |
| Assertion Completeness | >= 90% | < 80% |
| Auto-Heal Success Rate | >= 70% | < 50% |
| Script Regeneration Success | >= 80% | < 60% |

---

*This agent bridges the gap between "what to test" and "how to test it" — generating code that's not just functional, but maintainable, robust, and self-repairing.*
