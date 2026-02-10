# 07 — Jira Integration Testing

> **Purpose:** Define comprehensive testing for the bi-directional Jira integration covering authentication, read/write operations, automatic bug creation, and failure recovery.

---

## 7.1 Integration Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    JIRA INTEGRATION LAYER                       │
│                                                                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │   Auth       │    │   Reader     │    │   Writer     │     │
│  │   Manager    │    │   Service    │    │   Service    │     │
│  │              │    │              │    │              │     │
│  │  • OAuth 2.0 │    │  • Tickets   │    │  • Comments  │     │
│  │  • API Token │    │  • Fields    │    │  • Status    │     │
│  │  • Refresh   │    │  • Attachmts │    │  • Attach    │     │
│  │  • Scoping   │    │  • Search    │    │  • Create    │     │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘     │
│         │                   │                   │              │
│         ▼                   ▼                   ▼              │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              RESILIENCE LAYER                        │     │
│  │  • Circuit Breaker  • Retry Queue  • Idempotency    │     │
│  │  • Rate Limiter     • Dead Letter  • Audit Log      │     │
│  └──────────────────────────────────────────────────────┘     │
│                             │                                  │
│                             ▼                                  │
│                      ┌──────────────┐                         │
│                      │  Jira REST   │                         │
│                      │  API v3      │                         │
│                      └──────────────┘                         │
└────────────────────────────────────────────────────────────────┘
```

---

## 7.2 Authentication Testing

### 7.2.1 OAuth 2.0 Flow Tests

| Test ID | Scenario | Expected Behavior | Priority |
|---------|----------|-------------------|----------|
| AUTH-001 | Initial OAuth authorization | Redirect to Atlassian, receive auth code, exchange for tokens | P0 |
| AUTH-002 | Access token refresh before expiry | Proactive refresh 5 min before expiry | P0 |
| AUTH-003 | Access token expired, refresh succeeds | Seamless re-auth, no user interruption | P0 |
| AUTH-004 | Refresh token expired | User prompted to re-authorize | P0 |
| AUTH-005 | Invalid client credentials | Clear error message, no data leakage | P0 |
| AUTH-006 | Scope insufficient for operation | 403 error with descriptive message | P1 |
| AUTH-007 | Concurrent token refresh | Only one refresh executed, others wait | P1 |
| AUTH-008 | Token storage security | Tokens encrypted at rest, not in logs | P0 |

### 7.2.2 API Token Authentication Tests

| Test ID | Scenario | Expected Behavior | Priority |
|---------|----------|-------------------|----------|
| AUTH-010 | Valid API token | All operations succeed | P0 |
| AUTH-011 | Expired API token | Clear error, prompt for new token | P0 |
| AUTH-012 | Revoked API token | 401 error, re-authentication flow | P0 |
| AUTH-013 | Token with limited permissions | Operations fail gracefully with descriptive error | P1 |
| AUTH-014 | Token rotation | New token works, old token rejected | P1 |

```javascript
describe('Jira Authentication', () => {

  describe('OAuth 2.0', () => {
    it('should proactively refresh token before expiry', async () => {
      const tokenManager = new JiraTokenManager({
        accessToken: 'valid-token',
        refreshToken: 'refresh-token',
        expiresAt: Date.now() + (4 * 60 * 1000) // 4 min from now
      });

      const refreshSpy = jest.spyOn(tokenManager, 'refreshAccessToken');

      // Trigger an API call
      await jiraClient.getTicket('PROJ-123');

      // Should have proactively refreshed (< 5 min to expiry)
      expect(refreshSpy).toHaveBeenCalledTimes(1);
    });

    it('should handle concurrent operations during refresh', async () => {
      const tokenManager = new JiraTokenManager({
        accessToken: 'expired-token',
        refreshToken: 'valid-refresh',
        expiresAt: Date.now() - 1000 // already expired
      });

      // Trigger 5 concurrent API calls
      const results = await Promise.all([
        jiraClient.getTicket('PROJ-1'),
        jiraClient.getTicket('PROJ-2'),
        jiraClient.getTicket('PROJ-3'),
        jiraClient.getTicket('PROJ-4'),
        jiraClient.getTicket('PROJ-5'),
      ]);

      // Only 1 refresh should have been made
      expect(tokenManager.refreshCount).toBe(1);
      // All calls should succeed
      results.forEach(r => expect(r.status).toBe(200));
    });
  });
});
```

---

## 7.3 Ticket Read/Write Permission Tests

### 7.3.1 Read Operations

| Test ID | Scenario | Expected | Priority |
|---------|----------|----------|----------|
| READ-001 | Fetch ticket by key (PROJ-123) | All fields returned correctly | P0 |
| READ-002 | Fetch ticket with custom fields | Custom fields mapped correctly | P1 |
| READ-003 | Fetch ticket with attachments | Attachment metadata returned | P1 |
| READ-004 | Fetch ticket from restricted project | 403 error, not exposed | P0 |
| READ-005 | Fetch non-existent ticket | 404 error with clear message | P0 |
| READ-006 | Search tickets by JQL | Correct results, pagination works | P0 |
| READ-007 | Fetch ticket with large description | Full content returned, no truncation | P1 |
| READ-008 | Fetch ticket comments | Comments returned in order | P1 |
| READ-009 | Handle Jira Cloud vs Server API differences | Adapter pattern handles both | P2 |

### 7.3.2 Write Operations

| Test ID | Scenario | Expected | Priority |
|---------|----------|----------|----------|
| WRITE-001 | Post comment to ticket | Comment appears on ticket with correct formatting | P0 |
| WRITE-002 | Update ticket status | Transition executed correctly | P0 |
| WRITE-003 | Attach file to ticket | File uploaded and linked correctly | P0 |
| WRITE-004 | Update custom field | Field value updated correctly | P1 |
| WRITE-005 | Add label to ticket | Label added without removing existing | P1 |
| WRITE-006 | Write to read-only ticket | Error handled gracefully | P0 |
| WRITE-007 | Concurrent writes to same ticket | No data loss, no duplicates | P1 |
| WRITE-008 | Write with invalid field values | Validation error, no partial update | P0 |

---

## 7.4 Automatic Bug Creation Testing

### 7.4.1 Bug Creation Flow

```
Test Execution Failed
        │
        ▼
┌─────────────────┐     ┌─────────────────┐
│ Check: Existing │────▶│ Existing bug    │── YES ──▶ Update existing bug
│ bug for same    │     │ found?          │          (add comment, link)
│ failure?        │     └─────────────────┘
└─────────────────┘              │ NO
                                 ▼
┌─────────────────┐     ┌─────────────────┐
│ Create new Jira │────▶│ Bug created     │──▶ Link to source story
│ bug ticket      │     │ successfully?   │
└─────────────────┘     └─────────────────┘
                                 │ NO
                                 ▼
                        ┌─────────────────┐
                        │ Retry / Queue   │
                        │ for manual      │
                        │ creation        │
                        └─────────────────┘
```

### 7.4.2 Bug Creation Tests

| Test ID | Scenario | Expected | Priority |
|---------|----------|----------|----------|
| BUG-001 | Create bug from test failure | Bug created with correct summary, description, priority | P0 |
| BUG-002 | Bug includes failure evidence | Screenshot, logs, stack trace attached | P0 |
| BUG-003 | Bug linked to source story | Issue link created between bug and story | P0 |
| BUG-004 | Bug has correct fields | Project, type, priority, assignee (if configured) | P1 |
| BUG-005 | Duplicate bug prevention | No new bug if existing open bug for same failure | P0 |
| BUG-006 | Bug description includes steps to reproduce | Derived from test steps | P1 |
| BUG-007 | Bug includes environment info | Browser, URL, timestamp | P1 |
| BUG-008 | Bug includes AI root cause | RCA suggestion in description | P2 |
| BUG-009 | Bug creation for multiple failures | Separate bugs for separate failures | P1 |
| BUG-010 | Bug creation in configured project | Bug goes to correct Jira project | P0 |

**Bug Creation Test Example:**

```javascript
describe('Automatic Bug Creation', () => {

  it('should create bug with all required fields from test failure', async () => {
    const testResult = {
      id: 'TC-005',
      title: 'Verify error message on invalid login',
      status: 'failed',
      sourceTicket: 'PROJ-123',
      error: {
        message: 'Expected text "Invalid credentials" but found "Error"',
        step: 3,
        screenshot: 'screenshots/TC-005_step3_20260210.png'
      },
      environment: { browser: 'Chrome 120', url: 'https://qa.app.com' }
    };

    const createdBug = await jiraBugCreator.createFromFailure(testResult);

    expect(createdBug.fields.project.key).toBe('PROJ');
    expect(createdBug.fields.issuetype.name).toBe('Bug');
    expect(createdBug.fields.summary).toContain('Login error message incorrect');
    expect(createdBug.fields.description).toContain('Steps to reproduce');
    expect(createdBug.fields.description).toContain('Expected: "Invalid credentials"');
    expect(createdBug.fields.description).toContain('Actual: "Error"');
    expect(createdBug.fields.priority.name).toBe('High');
    expect(createdBug.attachments).toHaveLength(1);
    expect(createdBug.links[0].outwardIssue.key).toBe('PROJ-123');
  });

  it('should not create duplicate bug for same failure', async () => {
    // First failure creates bug
    const bug1 = await jiraBugCreator.createFromFailure(testResult);
    expect(bug1.key).toBeDefined();

    // Second identical failure should update existing
    const bug2 = await jiraBugCreator.createFromFailure(testResult);
    expect(bug2.key).toBe(bug1.key);
    expect(bug2.action).toBe('updated');
    expect(bug2.commentAdded).toBe(true);
  });
});
```

---

## 7.5 Test Execution to Jira Story Linking

| Test ID | Scenario | Expected | Priority |
|---------|----------|----------|----------|
| LINK-001 | Link test execution results to story | Results comment on story | P0 |
| LINK-002 | Link includes pass/fail summary | "5/7 tests passed" format | P0 |
| LINK-003 | Link includes report URL | Clickable link to full report | P0 |
| LINK-004 | Multiple executions linked | History visible on Jira story | P1 |
| LINK-005 | Link test case to AC | Traceability visible on ticket | P1 |
| LINK-006 | Custom Jira field updated | Test status field set to pass/fail | P1 |

**Jira Comment Format Validation:**

```javascript
describe('Jira Result Comment', () => {

  it('should format result comment correctly', () => {
    const executionResult = {
      suiteId: 'SUITE-001',
      sourceTicket: 'PROJ-123',
      total: 7,
      passed: 5,
      failed: 2,
      duration: '3m 42s',
      reportUrl: 'https://reports.app.com/SUITE-001'
    };

    const comment = jiraCommentFormatter.formatResult(executionResult);

    expect(comment).toContain('Test Execution Results');
    expect(comment).toContain('5 of 7 tests passed');
    expect(comment).toContain('2 failures');
    expect(comment).toContain('Duration: 3m 42s');
    expect(comment).toContain('[View Full Report]');
    expect(comment).toContain(executionResult.reportUrl);
  });
});
```

---

## 7.6 Failure Recovery Testing

### 7.6.1 Jira Downtime Handling

```
Jira API Call Fails
        │
        ▼
┌─────────────────┐
│ Circuit Breaker │
│ State?          │
├─────────────────┤
│ CLOSED:         │──▶ Retry with backoff (up to 3 times)
│ HALF-OPEN:      │──▶ Send probe request to check recovery
│ OPEN:           │──▶ Queue operation for later
└─────────────────┘
        │
        ▼ (if all retries fail)
┌─────────────────┐
│ Queue to Dead   │──▶ Persist operation details locally
│ Letter Queue    │    Process when Jira recovers
└─────────────────┘
        │
        ▼ (when Jira recovers)
┌─────────────────┐
│ Replay queued   │──▶ Execute in order, verify idempotency
│ operations      │
└─────────────────┘
```

### 7.6.2 Recovery Tests

| Test ID | Scenario | Expected | Priority |
|---------|----------|----------|----------|
| RCV-001 | Jira returns 503 once, then recovers | Retry succeeds, operation completed | P0 |
| RCV-002 | Jira down for 5 minutes | Operations queued, replayed on recovery | P0 |
| RCV-003 | Jira down for 1 hour | Alert triggered, operations queued, no data loss | P1 |
| RCV-004 | Circuit breaker opens after 5 failures | Subsequent calls short-circuit, no flood | P0 |
| RCV-005 | Circuit breaker half-open probe | Probe request sent, circuit closes on success | P1 |
| RCV-006 | Queued operations replayed in order | Chronological order maintained | P0 |
| RCV-007 | Duplicate prevention during replay | Idempotent operations don't create duplicates | P0 |
| RCV-008 | Dead letter queue overflow | Alert triggered, oldest items preserved | P2 |
| RCV-009 | Rate limiting (429) handled | Backoff respects Retry-After header | P1 |
| RCV-010 | Partial Jira outage (writes fail, reads work) | Read operations continue, writes queued | P1 |

```javascript
describe('Jira Failure Recovery', () => {

  it('should queue operations when Jira is down and replay on recovery', async () => {
    // Simulate Jira downtime
    jiraMock.setStatus(503);

    // Attempt to post result
    await jiraWriter.postResult('PROJ-123', executionResult);

    // Verify operation was queued
    expect(operationQueue.length).toBe(1);
    expect(operationQueue[0].operation).toBe('postResult');
    expect(operationQueue[0].ticketKey).toBe('PROJ-123');

    // Simulate recovery
    jiraMock.setStatus(200);
    await recoveryService.replayQueuedOperations();

    // Verify operation was executed
    expect(operationQueue.length).toBe(0);
    expect(jiraMock.getComments('PROJ-123')).toHaveLength(1);
  });

  it('should prevent duplicate operations during replay', async () => {
    jiraMock.setStatus(503);

    // Same operation attempted twice
    await jiraWriter.postResult('PROJ-123', executionResult);
    await jiraWriter.postResult('PROJ-123', executionResult);

    expect(operationQueue.length).toBe(1); // Deduplication

    jiraMock.setStatus(200);
    await recoveryService.replayQueuedOperations();

    expect(jiraMock.getComments('PROJ-123')).toHaveLength(1);
  });
});
```

---

## 7.7 Jira Data Validation

| Test ID | Validation | Method | Priority |
|---------|-----------|--------|----------|
| JDV-001 | Comment Markdown renders correctly | Visual check in Jira | P1 |
| JDV-002 | Status transitions follow workflow | Validate against Jira workflow rules | P0 |
| JDV-003 | Custom field values are valid | Schema validation before write | P1 |
| JDV-004 | Attachment content matches source | Hash comparison | P1 |
| JDV-005 | Labels don't exceed Jira limits | Length validation | P2 |
| JDV-006 | Unicode handling in comments | Non-ASCII characters display correctly | P2 |

---

*Previous: [06 — Execution & Report Validation](./06-execution-report-validation.md) | Next: [08 — Security & Compliance Testing](./08-security-compliance-testing.md)*
