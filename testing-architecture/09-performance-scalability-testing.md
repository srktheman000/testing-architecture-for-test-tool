# 09 — Performance & Scalability Testing

> **Purpose:** Define load, stress, and scalability testing for concurrent ticket processing, parallel test execution, and system behavior under pressure.

---

## 9.1 Performance Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                  PERFORMANCE BOTTLENECK MAP                          │
│                                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│  │  Jira    │    │  LLM     │    │  Script  │    │  Browser │     │
│  │  API     │    │  API     │    │  Gen     │    │  Grid    │     │
│  │  I/O     │    │  Latency │    │  CPU     │    │  Capacity│     │
│  │  bound   │    │  bound   │    │  bound   │    │  bound   │     │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘     │
│       │               │               │               │            │
│       ▼               ▼               ▼               ▼            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    QUEUE / ORCHESTRATOR                      │   │
│  │  Manages concurrency, backpressure, and resource allocation │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 9.2 Performance SLAs

| Operation | P50 Target | P95 Target | P99 Target | Max |
|-----------|-----------|-----------|-----------|-----|
| Jira ticket fetch | 200ms | 500ms | 1s | 3s |
| Test case generation (LLM) | 5s | 15s | 30s | 60s |
| Script generation | 1s | 3s | 5s | 10s |
| Script validation (lint+compile) | 500ms | 1s | 2s | 5s |
| Single test execution | 30s | 60s | 120s | 300s |
| Report generation | 2s | 5s | 10s | 30s |
| Jira update (comment + attach) | 500ms | 1s | 3s | 5s |
| **Full pipeline (1 ticket)** | **2 min** | **5 min** | **8 min** | **15 min** |

---

## 9.3 Load Testing

### 9.3.1 Load Test Scenarios

| Scenario | Description | Concurrent Users | Duration | Success Criteria |
|----------|------------|-----------------|----------|-----------------|
| **LT-001**: Steady state | Normal daily load | 10 users | 30 min | All SLAs met, zero errors |
| **LT-002**: Peak hour | Maximum expected load | 25 users | 15 min | P95 within SLA, < 1% errors |
| **LT-003**: Concurrent tickets | Multiple tickets processed simultaneously | 20 tickets | 10 min | All complete, no queue starvation |
| **LT-004**: Parallel execution | Multiple test suites running simultaneously | 15 suites | 20 min | Grid handles load, no OOM |
| **LT-005**: Report generation burst | Many reports generated at once | 30 reports | 5 min | All generated, < 10s each |
| **LT-006**: Jira burst writes | Rapid updates to Jira | 50 updates/min | 10 min | All succeed, no rate limiting |

### 9.3.2 Load Test Configuration (k6)

```javascript
// load-test-concurrent-tickets.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const pipelineDuration = new Trend('pipeline_duration');

export const options = {
  scenarios: {
    concurrent_tickets: {
      executor: 'ramping-vus',
      startVUs: 1,
      stages: [
        { duration: '2m', target: 10 },   // Ramp up
        { duration: '10m', target: 20 },   // Peak load
        { duration: '5m', target: 20 },    // Sustained
        { duration: '2m', target: 0 },     // Ramp down
      ],
    },
  },
  thresholds: {
    'http_req_duration': ['p(95)<15000'],   // 95% of requests < 15s
    'errors': ['rate<0.01'],                 // < 1% error rate
    'pipeline_duration': ['p(95)<300000'],   // 95% pipelines < 5min
  },
};

export default function () {
  // Step 1: Submit ticket for processing
  const submitRes = http.post(`${BASE_URL}/api/generate-tests`, JSON.stringify({
    ticketKey: `LOAD-${__VU}-${__ITER}`,
    options: { framework: 'playwright' }
  }), { headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${TOKEN}` } });

  check(submitRes, { 'submission accepted': (r) => r.status === 202 });
  if (submitRes.status !== 202) { errorRate.add(1); return; }

  const jobId = submitRes.json().jobId;
  const startTime = Date.now();

  // Step 2: Poll for completion
  let status = 'processing';
  let attempts = 0;
  while (status === 'processing' && attempts < 60) {
    sleep(5);
    const statusRes = http.get(`${BASE_URL}/api/jobs/${jobId}`);
    status = statusRes.json().status;
    attempts++;
  }

  const duration = Date.now() - startTime;
  pipelineDuration.add(duration);

  check(status, {
    'pipeline completed': (s) => s === 'completed',
    'pipeline within SLA': () => duration < 300000,
  });

  if (status !== 'completed') { errorRate.add(1); }
  sleep(1);
}
```

### 9.3.3 Load Test for LLM API Concurrency

```javascript
// load-test-llm-concurrency.js
export const options = {
  scenarios: {
    llm_concurrent: {
      executor: 'constant-arrival-rate',
      rate: 10,              // 10 requests per second
      timeUnit: '1s',
      duration: '5m',
      preAllocatedVUs: 20,
      maxVUs: 50,
    },
  },
  thresholds: {
    'http_req_duration{name:llm_call}': ['p(95)<30000'],  // LLM < 30s
    'http_req_failed': ['rate<0.05'],                       // < 5% failure
  },
};

export default function () {
  const res = http.post(`${BASE_URL}/api/generate-tests`, payload, {
    tags: { name: 'llm_call' },
    timeout: '60s',
  });

  check(res, {
    'LLM response OK': (r) => r.status === 200,
    'Valid JSON response': (r) => {
      try { JSON.parse(r.body); return true; }
      catch { return false; }
    },
    'Response time < 30s': (r) => r.timings.duration < 30000,
  });
}
```

---

## 9.4 Stress Testing

### 9.4.1 Stress Test Scenarios

| Scenario | Description | Load | Expected Behavior |
|----------|------------|------|-------------------|
| **ST-001**: LLM API saturation | Exceed LLM rate limits | 100 concurrent requests | Graceful queuing, no data loss |
| **ST-002**: Browser grid exhaustion | More tests than grid capacity | 50 parallel tests, 10-node grid | Queue overflow, priority-based execution |
| **ST-003**: Large acceptance criteria | Ticket with 50+ ACs | Single massive ticket | Token budget managed, chunking works |
| **ST-004**: Long-running suites | Suite with 200+ test cases | 1 suite, 4-hour run | No memory leak, all results captured |
| **ST-005**: Database connection pool | Exhaust DB connections | 200 concurrent operations | Connection pooling, graceful degradation |
| **ST-006**: Memory under load | Sustained high load | 30 VUs for 1 hour | Memory stable, no OOM |
| **ST-007**: Disk space (reports) | Generate thousands of reports | 500 reports with screenshots | Disk monitoring, cleanup triggers |

### 9.4.2 Stress Test: Large Acceptance Criteria

```javascript
// stress-test-large-ac.js
describe('Stress: Large Acceptance Criteria', () => {

  it('should handle ticket with 50 acceptance criteria', async () => {
    const largeTicket = generateTicketWithACs(50);

    const startTime = Date.now();
    const result = await aiService.generateTestCases(largeTicket);
    const duration = Date.now() - startTime;

    // Should complete within timeout
    expect(duration).toBeLessThan(120000); // 2 minutes max

    // Should handle chunking correctly
    expect(result.testCases.length).toBeGreaterThan(0);
    expect(result.metadata.chunksProcessed).toBeGreaterThan(1);

    // Should not lose ACs during chunking
    const coveredACs = new Set(
      result.testCases.map(tc => tc.traceability.acceptanceCriteriaIndex)
    );
    expect(coveredACs.size).toBeGreaterThanOrEqual(40); // >= 80% coverage

    // Should not exceed memory limits
    expect(process.memoryUsage().heapUsed).toBeLessThan(512 * 1024 * 1024);
  });

  it('should handle ticket with extremely long description', async () => {
    const longTicket = generateTicketWithDescription(100000); // 100K chars

    const result = await aiService.generateTestCases(longTicket);

    expect(result.metadata.truncated).toBe(true);
    expect(result.metadata.originalLength).toBe(100000);
    expect(result.testCases.length).toBeGreaterThan(0);
  });
});
```

### 9.4.3 Memory Leak Detection

```javascript
// stress-test-memory.js
describe('Memory Stability', () => {

  it('should maintain stable memory over 100 iterations', async () => {
    const memorySnapshots = [];

    for (let i = 0; i < 100; i++) {
      await aiService.generateTestCases(standardTicket);
      await executionEngine.run(simpleTestSuite);

      if (i % 10 === 0) {
        global.gc(); // Force GC
        memorySnapshots.push({
          iteration: i,
          heapUsed: process.memoryUsage().heapUsed
        });
      }
    }

    // Memory should not grow more than 50% from start
    const initialMemory = memorySnapshots[0].heapUsed;
    const finalMemory = memorySnapshots[memorySnapshots.length - 1].heapUsed;
    const growth = (finalMemory - initialMemory) / initialMemory;

    expect(growth).toBeLessThan(0.5); // < 50% growth
  });
});
```

---

## 9.5 Scalability Testing

### 9.5.1 Horizontal Scaling Tests

| Scenario | Nodes | Expected | Metric |
|----------|-------|----------|--------|
| Single node baseline | 1 | Baseline throughput | X tickets/hour |
| Double capacity | 2 | ~1.8x throughput | Near-linear scaling |
| Triple capacity | 3 | ~2.6x throughput | Near-linear scaling |
| Scale to 10 | 10 | ~8x throughput | Sub-linear acceptable |
| Scale down to 1 | 10 → 1 | No data loss | In-flight jobs complete |

### 9.5.2 Auto-Scaling Triggers

| Metric | Scale Up Trigger | Scale Down Trigger |
|--------|-----------------|-------------------|
| CPU utilization | > 70% for 5 min | < 30% for 10 min |
| Queue depth | > 20 pending jobs | < 5 pending for 10 min |
| Memory utilization | > 80% | < 40% for 10 min |
| Response time P95 | > 2x SLA | < 0.5x SLA for 15 min |
| Browser grid utilization | > 80% slots used | < 30% slots for 10 min |

---

## 9.6 Performance Testing Tools

| Tool | Use Case | Configuration |
|------|----------|---------------|
| **k6** | HTTP load testing, scripted scenarios | JavaScript-based, CI-integrated |
| **JMeter** | Complex load testing with GUI | For large-scale distributed tests |
| **Artillery** | Quick API load tests | YAML-based, lightweight |
| **Grafana + Prometheus** | Real-time performance monitoring | Dashboards during test runs |
| **clinic.js** | Node.js profiling (flame, bubbleprof) | Local performance debugging |
| **Chrome DevTools Protocol** | Browser performance profiling | Automation performance metrics |

---

## 9.7 Performance Test Schedule

| Test Type | Trigger | Duration | Environment |
|-----------|---------|----------|-------------|
| Quick load test (LT-001) | Every PR (if perf-related) | 5 min | CI staging |
| Standard load test (LT-001 to LT-003) | Nightly | 30 min | Staging |
| Full load test suite | Weekly | 2 hours | Staging |
| Stress tests | Pre-release | 4 hours | Staging |
| Scalability tests | Monthly / architecture change | 6 hours | Production-mirror |
| Endurance test | Monthly | 24 hours | Staging |

---

## 9.8 Performance Baseline & Regression Detection

**Baseline Management:**

```
Current Baseline (v2.3.0):
  - Pipeline P50: 2.1 min
  - Pipeline P95: 4.8 min
  - LLM latency P95: 12s
  - Throughput: 45 tickets/hour (10 VUs)
  - Error rate: 0.3%
  - Memory (steady state): 340MB

Regression Thresholds:
  - Any P95 metric > 120% of baseline → WARNING
  - Any P95 metric > 150% of baseline → BLOCK RELEASE
  - Error rate > 2x baseline → BLOCK RELEASE
  - Memory growth > 25% → INVESTIGATE
```

---

*Previous: [08 — Security & Compliance](./08-security-compliance-testing.md) | Next: [10 — CI/CD Testing Strategy](./10-cicd-testing-strategy.md)*
