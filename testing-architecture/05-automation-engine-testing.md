# 05 — Automation Engine Testing

> **Purpose:** Define the testing strategy for the automation script generation engine, locator management, and cross-browser/cross-environment execution.

---

## 5.1 Automation Engine Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTOMATION ENGINE                             │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Test Case   │───▶│   Script     │───▶│   Code       │      │
│  │  (JSON)      │    │   Generator  │    │   Validator   │      │
│  └──────────────┘    └──────────────┘    └──────┬───────┘      │
│                                                  │              │
│                                                  ▼              │
│                                          ┌──────────────┐      │
│                                          │   Locator    │      │
│                                          │   Resolver   │      │
│                                          └──────┬───────┘      │
│                                                  │              │
│                                                  ▼              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Results     │◀───│  Execution   │◀───│   Browser    │      │
│  │  Collector   │    │  Runtime     │    │   Manager    │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5.2 Script Generation Testing

### 5.2.1 Framework Compliance Tests

The generated scripts must correctly use the target automation framework's API.

#### Playwright Compliance Tests

| Test ID | Scenario | Validation | Priority |
|---------|----------|-----------|----------|
| SCR-PW-001 | Navigation actions use `page.goto()` | AST check for correct API usage | P0 |
| SCR-PW-002 | Click actions use `page.click()` or `locator.click()` | Pattern matching | P0 |
| SCR-PW-003 | Input actions use `page.fill()` not `page.type()` | Best practice enforcement | P1 |
| SCR-PW-004 | Assertions use `expect()` from `@playwright/test` | Import validation | P0 |
| SCR-PW-005 | Waits use `waitForSelector` / `waitForNavigation` | No `page.waitForTimeout()` | P1 |
| SCR-PW-006 | Test structure uses `test.describe` / `test()` blocks | Structural validation | P0 |
| SCR-PW-007 | `beforeEach` / `afterEach` hooks used for setup/teardown | Pattern detection | P1 |
| SCR-PW-008 | Page Object Model pattern when > 3 page interactions | Structural analysis | P2 |

#### Selenium Compliance Tests

| Test ID | Scenario | Validation | Priority |
|---------|----------|-----------|----------|
| SCR-SE-001 | Driver initialized with correct options | Constructor validation | P0 |
| SCR-SE-002 | Elements found with supported locator strategies | `By.id`, `By.css`, etc. | P0 |
| SCR-SE-003 | Explicit waits used (no Thread.sleep) | Pattern check | P1 |
| SCR-SE-004 | Driver quit in teardown / finally block | Resource cleanup validation | P0 |
| SCR-SE-005 | Assertions use TestNG/JUnit assertion library | Import validation | P0 |
| SCR-SE-006 | WebDriverWait with appropriate timeouts | Timeout value validation | P1 |

### 5.2.2 Code Compilation & Syntax Validation

Every generated script is validated before execution:

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Generate │────▶│  Parse   │────▶│  Lint    │────▶│  Compile │
│  Script  │     │  (AST)   │     │  Check   │     │  Check   │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                │                │
     │                ▼                ▼                ▼
     │          Syntax errors    Style issues     Type errors
     │          detected?        detected?        detected?
     │                │                │                │
     │                ▼                ▼                ▼
     │           ┌─────────┐    ┌─────────┐     ┌─────────┐
     │           │ FIX or  │    │ AUTO-   │     │ FIX or  │
     │           │ REJECT  │    │ FIX     │     │ REJECT  │
     │           └─────────┘    └─────────┘     └─────────┘
     │
     ▼
  EXECUTABLE
```

**Validation Tests:**

| Test ID | Scenario | Method | Priority |
|---------|----------|--------|----------|
| CVL-001 | Script has valid syntax | AST parsing (babel/typescript compiler) | P0 |
| CVL-002 | All imports resolve correctly | Module resolution check | P0 |
| CVL-003 | No undefined variables | Static analysis / TypeScript check | P0 |
| CVL-004 | ESLint passes with project rules | ESLint execution | P1 |
| CVL-005 | Prettier formatting compliant | Prettier check | P2 |
| CVL-006 | No security vulnerabilities (eval, exec) | Custom lint rules | P0 |
| CVL-007 | Script runs in sandbox without errors | Sandbox execution with mock browser | P0 |

### 5.2.3 Linting & Formatting Rules

Custom ESLint rules for generated automation scripts:

```json
{
  "rules": {
    "no-hardcoded-waits": "error",
    "no-hardcoded-urls": "warn",
    "no-hardcoded-credentials": "error",
    "require-assertion-per-step": "warn",
    "require-cleanup-in-afterEach": "error",
    "max-steps-per-test": ["warn", 20],
    "require-descriptive-test-name": "error",
    "no-eval": "error",
    "no-exec": "error",
    "prefer-locator-over-selector": "warn"
  }
}
```

---

## 5.3 Locator Strategy Testing

### 5.3.1 Locator Stability Tests

Locators are the most fragile part of automation. The platform must generate and validate resilient locators.

**Locator Priority Hierarchy:**

| Priority | Strategy | Stability | Example |
|----------|---------|-----------|---------|
| 1 | `data-testid` | Highest | `[data-testid="login-btn"]` |
| 2 | `id` attribute | High | `#login-button` |
| 3 | `aria-label` / role | High | `[aria-label="Submit"]` |
| 4 | Semantic HTML | Medium | `button[type="submit"]` |
| 5 | CSS class (stable) | Medium | `.btn-primary` |
| 6 | Text content | Low-Medium | `text="Log In"` |
| 7 | XPath (positional) | Low | `//div[3]/button[1]` |

**Locator Stability Tests:**

| Test ID | Scenario | Method | Priority |
|---------|----------|--------|----------|
| LOC-001 | Generated locators exist on target page | Live DOM validation | P0 |
| LOC-002 | Each locator matches exactly one element | Uniqueness check | P0 |
| LOC-003 | Preferred strategies used when available | Strategy audit | P1 |
| LOC-004 | No positional XPath used | Pattern detection | P1 |
| LOC-005 | Locators work after minor CSS changes | Simulated DOM change | P1 |
| LOC-006 | Locators work after content text changes | Simulated text change | P2 |
| LOC-007 | Locator resolution time < 5s | Performance check | P1 |

### 5.3.2 DOM Change Simulation Tests

Simulate common DOM changes to test locator resilience:

```javascript
describe('Locator Resilience', () => {
  const originalDOM = loadDOM('login-page.html');

  it('should survive class name changes', () => {
    const modifiedDOM = modifyDOM(originalDOM, {
      type: 'class-change',
      target: '.login-button',
      newClass: '.btn-login-v2'
    });
    const locator = generateLocator(modifiedDOM, 'loginButton');
    expect(locator.strategy).not.toBe('css-class');
    expect(locator.resolves(modifiedDOM)).toBe(true);
  });

  it('should survive wrapper element insertion', () => {
    const modifiedDOM = modifyDOM(originalDOM, {
      type: 'wrap-element',
      target: '#login-form',
      wrapper: '<div class="form-wrapper">'
    });
    const locators = page.getLocators();
    for (const locator of locators) {
      expect(locator.resolves(modifiedDOM)).toBe(true);
    }
  });

  it('should survive sibling reordering', () => {
    const modifiedDOM = modifyDOM(originalDOM, {
      type: 'reorder-siblings',
      parent: '.form-fields'
    });
    const locators = page.getLocators();
    for (const locator of locators) {
      expect(locator.resolves(modifiedDOM)).toBe(true);
    }
  });

  it('should survive attribute value changes', () => {
    const modifiedDOM = modifyDOM(originalDOM, {
      type: 'attribute-change',
      target: '#email-input',
      attribute: 'placeholder',
      newValue: 'Enter your email address'
    });
    const locator = generateLocator(modifiedDOM, 'emailInput');
    expect(locator.resolves(modifiedDOM)).toBe(true);
  });
});
```

### 5.3.3 Self-Healing Locator Verification

The platform includes self-healing locators that adapt when the primary locator fails.

**Self-Healing Flow:**

```
Primary Locator Fails
        │
        ▼
┌─────────────────┐     ┌─────────────────┐
│ Try Alternative  │────▶│ Element Found?  │── YES ──▶ Continue + Log Healing Event
│ Locator 1       │     └─────────────────┘
└─────────────────┘              │ NO
                                 ▼
┌─────────────────┐     ┌─────────────────┐
│ Try Alternative  │────▶│ Element Found?  │── YES ──▶ Continue + Log Healing Event
│ Locator 2       │     └─────────────────┘
└─────────────────┘              │ NO
                                 ▼
┌─────────────────┐     ┌─────────────────┐
│ Try Visual/AI   │────▶│ Element Found?  │── YES ──▶ Continue + Log Healing Event
│ Matching        │     └─────────────────┘
└─────────────────┘              │ NO
                                 ▼
                        ┌─────────────────┐
                        │ FAIL Test Step  │
                        │ + Screenshot    │
                        │ + DOM Snapshot  │
                        └─────────────────┘
```

**Self-Healing Tests:**

| Test ID | Scenario | Expected | Priority |
|---------|----------|----------|----------|
| SH-001 | Primary locator broken, alt-1 works | Heals to alt-1, test passes, event logged | P0 |
| SH-002 | Primary + alt-1 broken, alt-2 works | Heals to alt-2, test passes, event logged | P1 |
| SH-003 | All locators broken | Test fails with detailed diagnostic | P0 |
| SH-004 | Healed locator used in subsequent runs | Healed locator becomes new primary | P1 |
| SH-005 | Healing event triggers notification | Team alerted about locator drift | P2 |
| SH-006 | Healing doesn't match wrong element | Validation that healed element is correct one | P0 |

---

## 5.4 Cross-Browser & Environment Testing

### 5.4.1 Browser Matrix

| Browser | Versions | Priority | Test Coverage |
|---------|---------|----------|---------------|
| **Chrome** | Latest, Latest-1 | P0 | Full suite |
| **Firefox** | Latest, Latest-1 | P1 | Full suite |
| **Safari** | Latest (macOS) | P2 | Smoke suite |
| **Edge** | Latest | P2 | Smoke suite |
| **Mobile Chrome** | Latest (emulated) | P2 | Mobile-specific tests |
| **Mobile Safari** | Latest (emulated) | P3 | Mobile-specific tests |

### 5.4.2 Environment Matrix

| Environment | URL Pattern | Data | Purpose |
|-------------|-----------|------|---------|
| **QA** | `qa.app.example.com` | Synthetic, resetable | Daily regression |
| **UAT** | `uat.app.example.com` | Production-like snapshot | Pre-release validation |
| **Staging** | `staging.app.example.com` | Sanitized production copy | Final pre-prod check |
| **Prod-like** | `prod-mirror.internal` | Anonymized production | Performance benchmarking |

### 5.4.3 Cross-Browser Test Design

```javascript
// playwright.config.ts
export default defineConfig({
  projects: [
    {
      name: 'chrome',
      use: {
        ...devices['Desktop Chrome'],
        channel: 'chrome',
      },
    },
    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
      },
    },
    {
      name: 'safari',
      use: {
        ...devices['Desktop Safari'],
      },
    },
    {
      name: 'mobile-chrome',
      use: {
        ...devices['Pixel 5'],
      },
    },
  ],

  // Environment-specific base URLs
  use: {
    baseURL: process.env.TARGET_ENV === 'uat'
      ? 'https://uat.app.example.com'
      : 'https://qa.app.example.com',
  },
});
```

### 5.4.4 Cross-Browser/Environment Tests

| Test ID | Scenario | Browsers | Environments | Priority |
|---------|----------|----------|-------------|----------|
| XB-001 | Generated scripts run on Chrome | Chrome | QA | P0 |
| XB-002 | Generated scripts run on Firefox | Firefox | QA | P1 |
| XB-003 | Scripts adapt to mobile viewport | Mobile Chrome | QA | P2 |
| XB-004 | Scripts work across environments | Chrome | QA, UAT, Staging | P1 |
| XB-005 | Screenshots captured correctly per browser | All | QA | P1 |
| XB-006 | Browser-specific CSS selectors handled | All | QA | P2 |
| XB-007 | Cookie/storage handling per browser | All | QA | P2 |

---

## 5.5 Script Execution Sandbox

Before running on real environments, scripts are validated in a sandbox:

```
┌─────────────────────────────────────────────┐
│              SANDBOX ENVIRONMENT              │
│                                              │
│  ┌─────────────┐   ┌──────────────────┐     │
│  │  Mock        │   │  Generated       │     │
│  │  Browser     │   │  Script          │     │
│  │  (headless)  │   │                  │     │
│  └──────┬───────┘   └────────┬─────────┘     │
│         │                    │               │
│         ▼                    ▼               │
│  ┌──────────────────────────────────┐        │
│  │        SANDBOX RUNTIME           │        │
│  │  • No network access to prod     │        │
│  │  • 60s timeout                   │        │
│  │  • Memory limit: 512MB          │        │
│  │  • CPU limit: 1 core            │        │
│  └──────────────────────────────────┘        │
│                      │                       │
│                      ▼                       │
│  ┌──────────────────────────────────┐        │
│  │        SANDBOX RESULTS           │        │
│  │  • Syntax valid: ✓/✗             │        │
│  │  • Runtime errors: [list]        │        │
│  │  • Assertions executed: N        │        │
│  │  • Resource usage: {mem, cpu}    │        │
│  └──────────────────────────────────┘        │
└─────────────────────────────────────────────┘
```

---

*Previous: [04 — Test Case Validation](./04-test-case-generation-validation.md) | Next: [06 — Execution & Report Validation](./06-execution-report-validation.md)*
