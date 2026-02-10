# 06 — Execution & Report Validation

> **Purpose:** Define testing for real-time execution monitoring, retry logic, evidence capture, report correctness, and export format validation.

---

## 6.1 Execution Lifecycle

```
┌─────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ QUEUED  │──▶│ RUNNING  │──▶│ PASSED / │──▶│ REPORT   │──▶│ JIRA     │
│         │   │          │   │ FAILED   │   │ GENERATED│   │ UPDATED  │
└─────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
     │              │              │
     │              │              ▼
     │              │        ┌──────────┐
     │              │        │ RETRY    │──▶ (back to RUNNING, max 3x)
     │              │        └──────────┘
     │              ▼
     │        ┌──────────┐
     │        │ TIMEOUT  │──▶ FAILED (with timeout metadata)
     │        └──────────┘
     ▼
┌──────────┐
│ CANCELLED│
└──────────┘
```

---

## 6.2 Real-Time Execution Status Testing

### 6.2.1 Status Transition Tests

| Test ID | Scenario | Initial State | Trigger | Expected State | Priority |
|---------|----------|--------------|---------|----------------|----------|
| EXE-001 | Test starts executing | QUEUED | Execution begins | RUNNING | P0 |
| EXE-002 | Test completes successfully | RUNNING | All assertions pass | PASSED | P0 |
| EXE-003 | Test fails on assertion | RUNNING | Assertion failure | FAILED | P0 |
| EXE-004 | Test times out | RUNNING | Exceeds timeout | FAILED (timeout) | P0 |
| EXE-005 | Test is cancelled by user | RUNNING | Cancel request | CANCELLED | P1 |
| EXE-006 | Test crashes (unhandled error) | RUNNING | Runtime exception | ERROR | P0 |
| EXE-007 | Status updates in real-time | RUNNING | Each step completes | Progress updated | P1 |
| EXE-008 | Parallel tests show independent status | Multiple RUNNING | Mixed results | Each has own status | P1 |

### 6.2.2 Real-Time Progress Validation

```javascript
describe('Real-time Execution Monitoring', () => {

  it('should emit progress events for each test step', async () => {
    const events = [];
    executionEngine.on('progress', (event) => events.push(event));

    await executionEngine.run(testSuite);

    // Verify progress events
    expect(events.length).toBeGreaterThan(0);
    expect(events[0].type).toBe('suite_start');
    expect(events[events.length - 1].type).toBe('suite_end');

    // Each test should have start and end events
    const testEvents = events.filter(e => e.testId === 'TC-001');
    expect(testEvents.find(e => e.type === 'test_start')).toBeDefined();
    expect(testEvents.find(e => e.type === 'test_end')).toBeDefined();

    // Steps should be sequential
    const stepEvents = testEvents.filter(e => e.type === 'step_complete');
    for (let i = 1; i < stepEvents.length; i++) {
      expect(stepEvents[i].timestamp).toBeGreaterThan(stepEvents[i-1].timestamp);
      expect(stepEvents[i].stepNumber).toBe(stepEvents[i-1].stepNumber + 1);
    }
  });

  it('should report elapsed time accurately', async () => {
    const startTime = Date.now();
    const result = await executionEngine.run(simpleTest);
    const endTime = Date.now();

    const reportedDuration = result.duration;
    const actualDuration = endTime - startTime;

    // Within 500ms tolerance
    expect(Math.abs(reportedDuration - actualDuration)).toBeLessThan(500);
  });
});
```

---

## 6.3 Retry Logic Testing

### 6.3.1 Retry Configuration

```json
{
  "retry": {
    "maxAttempts": 3,
    "retryOn": ["timeout", "network_error", "element_not_found"],
    "doNotRetryOn": ["assertion_failure", "script_error"],
    "backoffStrategy": "exponential",
    "backoffBase": 2000,
    "backoffMax": 30000,
    "retryScope": "test"
  }
}
```

### 6.3.2 Retry Tests

| Test ID | Scenario | Expected Behavior | Priority |
|---------|----------|-------------------|----------|
| RTR-001 | Test fails due to timeout, succeeds on retry 2 | Status: PASSED, attempts: 2 | P0 |
| RTR-002 | Test fails all 3 retries | Status: FAILED, attempts: 3, all failures logged | P0 |
| RTR-003 | Test fails on assertion (no retry configured) | Status: FAILED, attempts: 1 | P0 |
| RTR-004 | Network error triggers retry | Retry initiated with backoff | P1 |
| RTR-005 | Element not found triggers retry | Retry initiated, self-healing attempted first | P1 |
| RTR-006 | Backoff timing is correct | Retry 1: 2s, Retry 2: 4s delays observed | P1 |
| RTR-007 | Retry uses clean browser state | New browser context per retry | P1 |
| RTR-008 | All retry attempts are logged | Complete log for each attempt | P0 |
| RTR-009 | Retry count visible in report | Report shows "Passed on attempt 2 of 3" | P1 |

```javascript
describe('Retry Logic', () => {

  it('should retry on timeout and succeed', async () => {
    let attempt = 0;
    mockBrowser.setHandler(() => {
      attempt++;
      if (attempt < 2) throw new TimeoutError('Element not found in 10s');
      return { status: 'pass' };
    });

    const result = await executionEngine.run(testCase, { maxRetries: 3 });

    expect(result.status).toBe('passed');
    expect(result.attempts).toBe(2);
    expect(result.retryHistory).toHaveLength(1);
    expect(result.retryHistory[0].reason).toBe('timeout');
  });

  it('should not retry on assertion failures', async () => {
    mockBrowser.setHandler(() => {
      throw new AssertionError('Expected "Dashboard" but got "Login"');
    });

    const result = await executionEngine.run(testCase, { maxRetries: 3 });

    expect(result.status).toBe('failed');
    expect(result.attempts).toBe(1);
    expect(result.retryHistory).toHaveLength(0);
  });

  it('should apply exponential backoff between retries', async () => {
    const retryTimestamps = [];
    executionEngine.on('retry', (event) => retryTimestamps.push(event.timestamp));

    mockBrowser.setHandler(() => { throw new TimeoutError(); });

    await executionEngine.run(testCase, { maxRetries: 3 });

    const delay1 = retryTimestamps[1] - retryTimestamps[0];
    const delay2 = retryTimestamps[2] - retryTimestamps[1];

    expect(delay1).toBeGreaterThanOrEqual(1800);  // ~2s ±200ms
    expect(delay2).toBeGreaterThanOrEqual(3600);  // ~4s ±400ms
  });
});
```

---

## 6.4 Evidence Capture Testing

### 6.4.1 Screenshot Capture Tests

| Test ID | Scenario | Expected | Priority |
|---------|----------|----------|----------|
| SS-001 | Screenshot on test failure | Full-page screenshot captured, attached to result | P0 |
| SS-002 | Screenshot on each step (optional mode) | Screenshot per step, in order | P2 |
| SS-003 | Screenshot on assertion failure | Screenshot shows page state at failure | P0 |
| SS-004 | Screenshot file naming | Format: `{testId}_{stepNum}_{timestamp}.png` | P1 |
| SS-005 | Screenshot quality and size | PNG, < 2MB, readable resolution | P1 |
| SS-006 | Screenshot in headless mode | Correct viewport size, full render | P0 |
| SS-007 | Screenshot of modal/popup | Modal visible in screenshot | P1 |
| SS-008 | Screenshot of scrollable page | Full page captured including below fold | P2 |

### 6.4.2 Log Completeness Tests

| Test ID | Scenario | Expected Log Content | Priority |
|---------|----------|---------------------|----------|
| LOG-001 | Successful test execution | Start time, each step, end time, duration | P0 |
| LOG-002 | Failed test execution | All of above + error message, stack trace, screenshot path | P0 |
| LOG-003 | Network requests logged | URL, method, status, duration for each request | P1 |
| LOG-004 | Console errors captured | Browser console errors/warnings captured | P1 |
| LOG-005 | Test data values logged | Input data used in each step | P1 |
| LOG-006 | Environment info in logs | Browser, OS, URL, viewport | P0 |
| LOG-007 | Timestamp format consistent | ISO 8601 format throughout | P1 |
| LOG-008 | Log levels appropriate | INFO for steps, ERROR for failures, DEBUG for details | P1 |

**Log Completeness Validation:**

```javascript
describe('Log Completeness', () => {

  it('should produce complete logs for failed execution', async () => {
    const result = await executionEngine.run(failingTest);
    const logs = result.logs;

    // Required sections
    expect(logs.find(l => l.level === 'INFO' && l.message.includes('Suite started'))).toBeDefined();
    expect(logs.find(l => l.level === 'INFO' && l.message.includes('Test started'))).toBeDefined();
    expect(logs.find(l => l.level === 'ERROR' && l.message.includes('Assertion failed'))).toBeDefined();
    expect(logs.find(l => l.level === 'INFO' && l.message.includes('Suite ended'))).toBeDefined();

    // Error details
    const errorLog = logs.find(l => l.level === 'ERROR');
    expect(errorLog.stackTrace).toBeDefined();
    expect(errorLog.screenshotPath).toBeDefined();
    expect(errorLog.stepNumber).toBeDefined();

    // Environment info
    const envLog = logs.find(l => l.type === 'environment');
    expect(envLog.browser).toBeDefined();
    expect(envLog.url).toBeDefined();
    expect(envLog.viewport).toBeDefined();
  });
});
```

---

## 6.5 AI-Generated Root Cause Analysis

The platform uses AI to analyze test failures and suggest root causes.

### 6.5.1 Root Cause Accuracy Tests

| Test ID | Failure Type | Expected Root Cause Category | Priority |
|---------|-------------|-----------------------------|---------| 
| RCA-001 | Element not found (removed from DOM) | UI Change — Element Removed | P0 |
| RCA-002 | Assertion: text mismatch | Content Change — Text Updated | P0 |
| RCA-003 | Timeout on page load | Performance — Slow Page Load | P1 |
| RCA-004 | 500 error in network log | Backend Error — Server Error | P0 |
| RCA-005 | SSL certificate error | Environment — Certificate Issue | P1 |
| RCA-006 | Element found but not clickable | UI Change — Overlay/Modal Blocking | P1 |
| RCA-007 | Unexpected redirect | Navigation Change — Route Changed | P1 |
| RCA-008 | Multiple failures same page | Systematic — Page Broken | P0 |

### 6.5.2 Root Cause Validation

```javascript
describe('Root Cause Analysis', () => {

  it('should correctly identify element removal as root cause', async () => {
    const failureContext = {
      error: 'TimeoutError: waiting for selector "#submit-btn" failed',
      screenshot: 'screenshot-001.png',
      domSnapshot: '<html>...(no #submit-btn)...</html>',
      networkLogs: [],
      consoleLogs: []
    };

    const rca = await rootCauseAnalyzer.analyze(failureContext);

    expect(rca.category).toBe('UI_CHANGE');
    expect(rca.subcategory).toBe('ELEMENT_REMOVED');
    expect(rca.confidence).toBeGreaterThan(0.8);
    expect(rca.suggestion).toContain('update locator');
  });

  it('should correctly identify backend error', async () => {
    const failureContext = {
      error: 'AssertionError: expected status 200 but got error page',
      networkLogs: [
        { url: '/api/users', status: 500, response: 'Internal Server Error' }
      ]
    };

    const rca = await rootCauseAnalyzer.analyze(failureContext);

    expect(rca.category).toBe('BACKEND_ERROR');
    expect(rca.networkEvidence).toBeDefined();
    expect(rca.suggestion).toContain('backend investigation');
  });
});
```

---

## 6.6 Report Validation

### 6.6.1 HTML Report Correctness

| Test ID | Aspect | Validation | Priority |
|---------|--------|-----------|----------|
| RPT-H-001 | Summary section | Correct pass/fail/skip counts match execution data | P0 |
| RPT-H-002 | Test details | Each test shows steps, status, duration, screenshots | P0 |
| RPT-H-003 | Charts/graphs | Pie chart percentages sum to 100% | P1 |
| RPT-H-004 | Navigation | All links work, anchors resolve | P1 |
| RPT-H-005 | Responsive design | Report readable on mobile and desktop | P2 |
| RPT-H-006 | Screenshot embedding | All screenshots load, correct test association | P0 |
| RPT-H-007 | Duration accuracy | Reported durations match execution logs | P1 |
| RPT-H-008 | Filtering/sorting | UI filters work correctly | P2 |
| RPT-H-009 | Environment info | Browser, URL, timestamp correct | P1 |
| RPT-H-010 | Error details | Stack traces, RCA displayed correctly | P0 |

### 6.6.2 PDF Layout Validation

| Test ID | Aspect | Validation | Priority |
|---------|--------|-----------|----------|
| RPT-P-001 | Page layout | No text overflow, correct margins | P1 |
| RPT-P-002 | Table formatting | Tables don't break across pages incorrectly | P1 |
| RPT-P-003 | Image quality | Screenshots readable in PDF | P1 |
| RPT-P-004 | Page numbers | Correct, sequential page numbering | P2 |
| RPT-P-005 | Table of contents | TOC links work, page numbers match | P2 |
| RPT-P-006 | File size | PDF < 50MB for reasonable suites | P2 |
| RPT-P-007 | Company branding | Logo, colors, header/footer correct | P3 |

### 6.6.3 Jira-Compatible Attachment Validation

| Test ID | Aspect | Validation | Priority |
|---------|--------|-----------|----------|
| RPT-J-001 | Attachment size | Within Jira attachment size limit (default 10MB) | P0 |
| RPT-J-002 | File format | Supported Jira attachment format (PDF, HTML, PNG) | P0 |
| RPT-J-003 | File naming | No special characters that break Jira upload | P1 |
| RPT-J-004 | Attachment link | Jira comment includes link to attachment | P0 |
| RPT-J-005 | Multiple attachments | All files attached correctly | P1 |

---

## 6.7 Report Data Integrity Tests

```javascript
describe('Report Data Integrity', () => {

  it('should match execution results exactly', async () => {
    const executionResult = await executionEngine.run(testSuite);
    const report = await reportGenerator.generate(executionResult);

    // Counts match
    expect(report.summary.total).toBe(executionResult.tests.length);
    expect(report.summary.passed).toBe(
      executionResult.tests.filter(t => t.status === 'passed').length
    );
    expect(report.summary.failed).toBe(
      executionResult.tests.filter(t => t.status === 'failed').length
    );

    // Individual test details match
    for (const test of executionResult.tests) {
      const reportTest = report.tests.find(rt => rt.id === test.id);
      expect(reportTest).toBeDefined();
      expect(reportTest.status).toBe(test.status);
      expect(reportTest.duration).toBe(test.duration);
      expect(reportTest.steps.length).toBe(test.steps.length);
    }

    // Timestamps match
    expect(report.startTime).toBe(executionResult.startTime);
    expect(report.endTime).toBe(executionResult.endTime);
  });
});
```

---

*Previous: [05 — Automation Engine Testing](./05-automation-engine-testing.md) | Next: [07 — Jira Integration Testing](./07-jira-integration-testing.md)*
