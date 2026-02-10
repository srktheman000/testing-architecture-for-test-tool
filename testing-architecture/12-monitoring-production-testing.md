# 12 — Monitoring & Production Testing

> **Purpose:** Define synthetic monitoring, health checks, AI accuracy observability, failure alerting, and operational dashboards for production quality assurance.

---

## 12.1 Monitoring Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                    PRODUCTION MONITORING STACK                         │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │  SYNTHETIC   │  │  HEALTH      │  │  AI ACCURACY │               │
│  │  MONITORING  │  │  CHECKS      │  │  MONITORING  │               │
│  │              │  │              │  │              │               │
│  │  Scheduled   │  │  /health     │  │  Confidence  │               │
│  │  E2E probes  │  │  /ready      │  │  tracking    │               │
│  │  every 5 min │  │  /live       │  │  every batch │               │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │
│         │                 │                 │                        │
│         ▼                 ▼                 ▼                        │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │              METRICS AGGREGATION                        │        │
│  │              (Prometheus / Datadog)                      │        │
│  └──────────────────────────┬──────────────────────────────┘        │
│                              │                                       │
│              ┌───────────────┼───────────────┐                      │
│              ▼               ▼               ▼                      │
│       ┌──────────┐    ┌──────────┐    ┌──────────┐                 │
│       │ GRAFANA  │    │ ALERTING │    │ LOG      │                 │
│       │ DASH-    │    │ (Pager-  │    │ ANALYSIS │                 │
│       │ BOARDS   │    │  Duty)   │    │ (ELK)    │                 │
│       └──────────┘    └──────────┘    └──────────┘                 │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 12.2 Synthetic Monitoring

### 12.2.1 Synthetic Test Probes

Automated tests that run continuously against production to detect issues before users do.

| Probe ID | Scenario | Frequency | Timeout | Alert After |
|----------|----------|-----------|---------|-------------|
| SYN-001 | Login and view dashboard | Every 5 min | 30s | 2 consecutive failures |
| SYN-002 | Fetch a known Jira ticket | Every 5 min | 10s | 2 consecutive failures |
| SYN-003 | Generate test cases for sample ticket | Every 15 min | 60s | 1 failure |
| SYN-004 | Execute a simple smoke test | Every 30 min | 120s | 1 failure |
| SYN-005 | Generate and download report | Every 30 min | 30s | 2 consecutive failures |
| SYN-006 | Post comment to test Jira ticket | Every 15 min | 15s | 2 consecutive failures |
| SYN-007 | Full pipeline (mini version) | Every 1 hour | 300s | 1 failure |

### 12.2.2 Synthetic Probe Implementation

```javascript
// monitoring/synthetic/probes/login-probe.js
const { chromium } = require('playwright');

module.exports = {
  name: 'login-and-dashboard',
  interval: '5m',
  timeout: 30000,

  async execute() {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    const metrics = {};

    try {
      // Step 1: Navigate to login
      const startNav = Date.now();
      await page.goto(process.env.PROD_URL + '/login');
      metrics.loginPageLoad = Date.now() - startNav;

      // Step 2: Login
      const startLogin = Date.now();
      await page.fill('#email', process.env.SYNTHETIC_USER);
      await page.fill('#password', process.env.SYNTHETIC_PASSWORD);
      await page.click('#login-button');
      await page.waitForURL('**/dashboard');
      metrics.loginDuration = Date.now() - startLogin;

      // Step 3: Verify dashboard content
      const dashboardTitle = await page.textContent('h1');
      if (!dashboardTitle.includes('Dashboard')) {
        throw new Error(`Unexpected dashboard title: ${dashboardTitle}`);
      }

      // Step 4: Check critical elements
      await page.waitForSelector('[data-testid="recent-executions"]', { timeout: 5000 });
      await page.waitForSelector('[data-testid="metrics-panel"]', { timeout: 5000 });

      metrics.totalDuration = metrics.loginPageLoad + metrics.loginDuration;
      return { status: 'healthy', metrics };

    } catch (error) {
      const screenshot = await page.screenshot();
      return {
        status: 'unhealthy',
        error: error.message,
        screenshot: screenshot.toString('base64'),
        metrics
      };
    } finally {
      await browser.close();
    }
  }
};
```

### 12.2.3 Multi-Region Synthetic Monitoring

| Region | Probes | Purpose |
|--------|--------|---------|
| US-East | Full suite | Primary region monitoring |
| US-West | Availability probes | Cross-region latency check |
| EU-West | Full suite | EU compliance + latency |
| AP-Southeast | Availability probes | Global reach verification |

---

## 12.3 Health Checks

### 12.3.1 Health Check Endpoints

```
GET /health          → Overall system health
GET /health/ready    → Readiness for traffic
GET /health/live     → Liveness (process running)
GET /health/details  → Detailed component health (authenticated)
```

### 12.3.2 Health Check Components

| Component | Check | Healthy | Degraded | Unhealthy |
|-----------|-------|---------|----------|-----------|
| **Database** | SELECT 1 | < 100ms | 100-500ms | > 500ms or error |
| **Redis** | PING | < 50ms | 50-200ms | > 200ms or error |
| **Jira API** | GET /rest/api/3/myself | < 1s | 1-3s | > 3s or error |
| **LLM API** | Lightweight completion | < 5s | 5-15s | > 15s or error |
| **Browser Grid** | GET /status | Available nodes > 0 | < 3 nodes | 0 nodes |
| **Disk Space** | Check free space | > 20% free | 10-20% free | < 10% free |
| **Queue** | Check depth | < 100 items | 100-500 items | > 500 items |

### 12.3.3 Health Check Response

```json
{
  "status": "healthy",
  "timestamp": "2026-02-10T10:00:00Z",
  "version": "2.3.1",
  "uptime": "72h 14m",
  "components": {
    "database": { "status": "healthy", "latency": "12ms" },
    "redis": { "status": "healthy", "latency": "3ms" },
    "jira": { "status": "healthy", "latency": "245ms" },
    "llm": { "status": "healthy", "latency": "1200ms" },
    "browserGrid": { "status": "healthy", "availableNodes": 8 },
    "diskSpace": { "status": "healthy", "freePercent": 67 },
    "queue": { "status": "healthy", "depth": 3 }
  }
}
```

---

## 12.4 AI Accuracy Monitoring

### 12.4.1 Real-Time AI Metrics

| Metric | Collection Method | Dashboard Widget |
|--------|------------------|-----------------|
| **Mean confidence score** | Tracked per generation | Time-series line chart |
| **Schema compliance rate** | Validated per output | Percentage gauge |
| **Hallucination detection rate** | Flagged by validator | Time-series line chart |
| **User override rate** | Tracked when user edits AI output | Percentage gauge |
| **Average test case count per ticket** | Counted per generation | Distribution histogram |
| **Prompt version performance** | Segmented by version | Version comparison chart |
| **Model latency** | Timed per LLM call | P50/P95/P99 chart |
| **Token usage** | Tracked per call | Daily usage bar chart |

### 12.4.2 AI Accuracy Tracking

```javascript
// monitoring/ai-accuracy-tracker.js
class AIAccuracyTracker {

  async trackGeneration(input, output, metadata) {
    const metrics = {
      timestamp: new Date().toISOString(),
      ticketKey: input.key,
      promptVersion: metadata.promptVersion,
      modelVersion: metadata.modelVersion,

      // Quality metrics
      confidence: metadata.confidence,
      testCaseCount: output.testCases.length,
      schemaValid: this.validateSchema(output),
      hallucinationCount: this.detectHallucinations(output, input).length,
      typeDistribution: this.getTypeDistribution(output),

      // Performance metrics
      latencyMs: metadata.processingTimeMs,
      tokensUsed: metadata.tokensUsed,
    };

    // Store in metrics database
    await metricsDB.insert('ai_generation_metrics', metrics);

    // Check thresholds
    if (metrics.confidence < 0.5) {
      await alertManager.warn('LOW_AI_CONFIDENCE', {
        ticketKey: input.key,
        confidence: metrics.confidence
      });
    }

    if (metrics.hallucinationCount > 0) {
      await alertManager.warn('HALLUCINATION_DETECTED', {
        ticketKey: input.key,
        count: metrics.hallucinationCount
      });
    }

    return metrics;
  }

  async getDailyReport() {
    const today = await metricsDB.query('ai_generation_metrics', {
      timestamp: { $gte: startOfDay() }
    });

    return {
      totalGenerations: today.length,
      meanConfidence: mean(today.map(m => m.confidence)),
      schemaComplianceRate: today.filter(m => m.schemaValid).length / today.length,
      hallucinationRate: today.filter(m => m.hallucinationCount > 0).length / today.length,
      meanLatency: mean(today.map(m => m.latencyMs)),
      totalTokens: sum(today.map(m => m.tokensUsed)),
      estimatedCost: this.calculateCost(sum(today.map(m => m.tokensUsed))),
    };
  }
}
```

### 12.4.3 AI Accuracy Alerts

| Alert | Condition | Severity | Response |
|-------|-----------|----------|----------|
| Low confidence trend | Mean confidence < 0.7 for 1 hour | Warning | Investigate, check model status |
| High hallucination rate | Rate > 10% for 30 minutes | Critical | Check prompt, consider rollback |
| Schema compliance drop | Rate < 95% for 15 minutes | Critical | Check LLM response format |
| High override rate | User edits > 40% of outputs | Warning | Review prompt quality |
| Token budget exceeded | Daily tokens > budget | Warning | Review, implement throttling |
| Model latency spike | P95 > 30s for 10 minutes | Warning | Check LLM provider status |

---

## 12.5 Failure Alerting

### 12.5.1 Alert Severity Matrix

| Severity | Examples | Response Time | Notification |
|----------|---------|---------------|-------------|
| **P0 — Critical** | Platform down, data corruption, security breach | 15 min | PagerDuty + Slack + SMS |
| **P1 — High** | AI accuracy < 50%, Jira sync failing, execution engine down | 1 hour | PagerDuty + Slack |
| **P2 — Medium** | Degraded performance, high error rate, queue backup | 4 hours | Slack + Email |
| **P3 — Low** | Minor issues, cosmetic, non-blocking | Next business day | Email + Jira ticket |

### 12.5.2 Alert Rules

```yaml
# monitoring/alert-rules.yml
alerts:
  - name: platform_down
    severity: P0
    condition: synthetic_probe_failures >= 3 in 10m
    channels: [pagerduty, slack-critical, sms-oncall]
    runbook: https://wiki.internal/runbooks/platform-down

  - name: ai_accuracy_critical
    severity: P1
    condition: ai_mean_confidence < 0.5 for 30m
    channels: [pagerduty, slack-ai-team]
    runbook: https://wiki.internal/runbooks/ai-accuracy-drop

  - name: jira_sync_failure
    severity: P1
    condition: jira_update_error_rate > 10% for 15m
    channels: [pagerduty, slack-integration]
    runbook: https://wiki.internal/runbooks/jira-sync-failure

  - name: execution_engine_degraded
    severity: P2
    condition: execution_error_rate > 5% for 30m
    channels: [slack-qa-team]
    runbook: https://wiki.internal/runbooks/execution-degraded

  - name: queue_backup
    severity: P2
    condition: queue_depth > 200 for 15m
    channels: [slack-devops]
    runbook: https://wiki.internal/runbooks/queue-backup

  - name: high_token_usage
    severity: P3
    condition: daily_token_usage > 80% of budget
    channels: [slack-ai-team, email-engineering-lead]
```

---

## 12.6 Dashboards

### 12.6.1 Executive Dashboard

```
┌──────────────────────────────────────────────────────────────┐
│                  EXECUTIVE DASHBOARD                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Platform Status: ● HEALTHY        Uptime: 99.97%           │
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │ Today's Summary  │  │ AI Quality      │                   │
│  │                 │  │                 │                   │
│  │ Tickets: 142    │  │ Accuracy: 91%   │                   │
│  │ Tests Gen: 834  │  │ Confidence: 0.87│                   │
│  │ Executions: 678 │  │ Halluc. Rate: 2%│                   │
│  │ Pass Rate: 87%  │  │ Override: 12%   │                   │
│  └─────────────────┘  └─────────────────┘                   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 7-Day Trend: Tickets Processed                       │   │
│  │ ▃▄▆█▇▅▇                                              │   │
│  │ Mon Tue Wed Thu Fri Sat Sun                           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Active Alerts: 1 Warning                              │   │
│  │ ⚠ Queue depth elevated (current: 45, threshold: 50) │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### 12.6.2 QA Engineering Dashboard

```
┌──────────────────────────────────────────────────────────────┐
│                  QA ENGINEERING DASHBOARD                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Execution Status (last 24h):                                │
│  ┌─────────────────────────────────────┐                    │
│  │ Passed: ████████████████ 678 (87%)  │                    │
│  │ Failed: ███ 78 (10%)                │                    │
│  │ Error:  █ 18 (2%)                   │                    │
│  │ Skipped:  6 (1%)                    │                    │
│  └─────────────────────────────────────┘                    │
│                                                              │
│  Top Failure Reasons:                                        │
│  1. Element not found (34%)                                  │
│  2. Assertion mismatch (28%)                                 │
│  3. Timeout (19%)                                            │
│  4. Backend error (12%)                                      │
│  5. Other (7%)                                               │
│                                                              │
│  Flakiest Tests (last 7 days):                              │
│  1. TC-412: Checkout flow — 4 flaky runs (of 14)           │
│  2. TC-203: Search filter — 3 flaky runs (of 14)           │
│  3. TC-089: File upload — 2 flaky runs (of 14)             │
│                                                              │
│  Jira Sync Status:                                           │
│  ● Updates: 456/458 succeeded (99.6%)                       │
│  ● Queued: 2 (retrying)                                     │
│  ● Failed: 0                                                │
│                                                              │
│  Golden Dataset Status (last nightly):                       │
│  ● Accuracy: 89.2% (baseline: 88.5%) ✓                     │
│  ● Drift: +0.7% (within threshold) ✓                       │
└──────────────────────────────────────────────────────────────┘
```

### 12.6.3 Dashboard Access Matrix

| Dashboard | Admin | PM | Tester | Viewer |
|-----------|-------|-----|--------|--------|
| Executive | Yes | Yes | No | No |
| QA Engineering | Yes | Yes | Yes | No |
| AI Accuracy | Yes | No | Yes | No |
| Infrastructure | Yes | No | No | No |
| Security | Yes | No | No | No |

---

## 12.7 Production Testing Safeguards

| Safeguard | Description |
|-----------|------------|
| Synthetic user isolation | Dedicated test account, separate from real users |
| Read-only probes preferred | Most probes only read, avoid write operations |
| Rate-limited probes | Synthetic traffic capped to not affect real users |
| Separate test Jira project | Synthetic monitoring uses isolated Jira project |
| Automatic cleanup | Any data created by probes is cleaned up immediately |
| Feature flag gating | Probes respect feature flags, don't test disabled features |

---

*Previous: [11 — Test Data Strategy](./11-test-data-strategy.md) | Next: [13 — Sample Artifacts](./13-sample-artifacts.md)*
