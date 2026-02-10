# 10 — CI/CD Testing Strategy

> **Purpose:** Define the testing stages in the CI/CD pipeline, including pre-commit hooks, PR validation, nightly regression, AI model change impact testing, and canary deployment for prompts.

---

## 10.1 Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CI/CD PIPELINE STAGES                            │
│                                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │  PRE-    │  │  PR      │  │  POST-   │  │  NIGHTLY │  │  PRE-   │ │
│  │  COMMIT  │  │  VALID-  │  │  MERGE   │  │  REGRESS-│  │  RELEASE│ │
│  │          │  │  ATION   │  │          │  │  ION     │  │         │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │
│       │              │              │              │              │     │
│       ▼              ▼              ▼              ▼              ▼     │
│  • Lint         • Unit tests  • E2E smoke   • Full E2E      • Full   │
│  • Format       • Integration • Deploy to   • Golden dataset   suite  │
│  • Secrets      • AI schema     staging     • Performance    • Perf   │
│  • Type check   • Prompt reg  • Health chk  • Drift detect  • Sec    │
│  • Commit msg   • Security                  • AI accuracy   • Canary │
│                 • Coverage                                            │
│                                                                         │
│  ◀─── ~30s ───▶ ◀── ~8min ──▶ ◀── ~5min ──▶ ◀── ~45min ──▶ ◀─ 2hr ─▶│
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 10.2 Pre-Commit Stage

**Trigger:** Every `git commit`
**Duration:** < 30 seconds
**Blocking:** Yes (commit rejected on failure)

### 10.2.1 Pre-Commit Hooks

```yaml
# .husky/pre-commit or .pre-commit-config.yaml
hooks:
  - id: eslint
    name: Lint (ESLint)
    entry: npx eslint --cache --max-warnings 0
    files: '\.(ts|tsx|js|jsx)$'

  - id: prettier
    name: Format check (Prettier)
    entry: npx prettier --check
    files: '\.(ts|tsx|js|jsx|json|md|yaml)$'

  - id: typecheck
    name: TypeScript type checking
    entry: npx tsc --noEmit
    pass_filenames: false

  - id: secrets
    name: Secret detection (gitleaks)
    entry: gitleaks protect --staged
    pass_filenames: false

  - id: commitlint
    name: Commit message lint
    entry: npx commitlint --edit
    stages: [commit-msg]

  - id: prompt-change-alert
    name: Flag prompt file changes
    entry: scripts/check-prompt-changes.sh
    files: 'prompts/'
```

### 10.2.2 Pre-Commit Test Scope

| Check | Tool | Blocking | Time |
|-------|------|----------|------|
| Linting | ESLint | Yes | ~5s |
| Formatting | Prettier | Yes | ~3s |
| Type checking | TypeScript | Yes | ~10s |
| Secret detection | gitleaks | Yes | ~3s |
| Commit message format | commitlint | Yes | ~1s |
| Prompt change detection | Custom script | Warning only | ~1s |
| Affected test detection | jest --changedSince | Info only | ~5s |

---

## 10.3 PR Validation Stage

**Trigger:** Every Pull Request creation/update
**Duration:** < 10 minutes
**Blocking:** Yes (PR cannot merge on failure)

### 10.3.1 PR Validation Pipeline

```yaml
# .github/workflows/pr-validation.yml
name: PR Validation
on:
  pull_request:
    branches: [main, develop]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npm run test:unit -- --coverage
      - uses: codecov/codecov-action@v4
        with:
          fail_ci_if_error: true
          minimum_coverage: 80

  integration-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 8
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test
          POSTGRES_PASSWORD: test
      redis:
        image: redis:7
      wiremock:
        image: wiremock/wiremock:latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run test:integration
        env:
          JIRA_MOCK_URL: http://wiremock:8080
          LLM_MOCK_URL: http://wiremock:8081

  ai-validation:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    if: contains(github.event.pull_request.changed_files, 'prompts/') ||
        contains(github.event.pull_request.changed_files, 'src/ai/')
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run test:ai:schema
      - run: npm run test:ai:prompt-regression -- --cached
      - name: Post AI validation results
        uses: actions/github-script@v7
        with:
          script: |
            // Post AI validation summary as PR comment

  security-scan:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - name: Dependency vulnerability scan
        run: npx snyk test --severity-threshold=high
      - name: SAST scan
        uses: github/codeql-action/analyze@v3

  quality-gate:
    needs: [unit-tests, integration-tests, ai-validation, security-scan]
    runs-on: ubuntu-latest
    steps:
      - name: Check all gates passed
        run: echo "All quality gates passed"
```

### 10.3.2 PR Validation Matrix

| Test Category | Tests Run | Coverage Req | Blocking? | Time |
|--------------|-----------|-------------|-----------|------|
| Unit tests | All unit tests | 80% overall, 90% AI layer | Yes | ~3 min |
| Integration tests | All integration (mocked) | All critical paths | Yes | ~5 min |
| AI schema validation | Schema compliance tests | 100% pass | Yes | ~1 min |
| Prompt regression (cached) | Golden dataset with cached LLM responses | 95% match | Yes (if prompt changed) | ~2 min |
| Security scan | Dependency + SAST | Zero high/critical | Yes | ~3 min |
| Lint + Format | Full codebase | Zero errors | Yes | ~1 min |

---

## 10.4 Post-Merge Stage

**Trigger:** Merge to `main` or `develop`
**Duration:** < 10 minutes
**Blocking:** Deployment paused on failure

```yaml
post-merge:
  steps:
    - name: Build and push Docker image
      run: |
        docker build -t ai-test-platform:${{ github.sha }} .
        docker push registry/ai-test-platform:${{ github.sha }}

    - name: Deploy to staging
      run: kubectl set image deployment/ai-test-platform app=registry/ai-test-platform:${{ github.sha }}

    - name: Health check
      run: scripts/health-check.sh staging 120  # 2-minute timeout

    - name: E2E smoke tests
      run: npm run test:e2e:smoke
      env:
        TARGET_URL: https://staging.ai-test-platform.com

    - name: Rollback on failure
      if: failure()
      run: kubectl rollout undo deployment/ai-test-platform
```

---

## 10.5 Nightly Regression Stage

**Trigger:** Scheduled (02:00 UTC daily)
**Duration:** ~45 minutes
**Blocking:** No (alerts and reports)

### 10.5.1 Nightly Pipeline

```yaml
nightly-regression:
  schedule:
    - cron: '0 2 * * *'

  jobs:
    full-e2e:
      timeout-minutes: 30
      steps:
        - run: npm run test:e2e:full
          env:
            TARGET_URL: https://staging.ai-test-platform.com
            BROWSERS: chrome,firefox

    golden-dataset:
      timeout-minutes: 20
      steps:
        - run: npm run test:ai:golden-dataset
          env:
            LLM_TEMPERATURE: 0  # Deterministic mode
        - run: npm run test:ai:drift-detection
        - name: Upload golden dataset results
          uses: actions/upload-artifact@v4

    performance:
      timeout-minutes: 15
      steps:
        - run: npm run test:perf:nightly
        - name: Compare with baseline
          run: scripts/compare-perf-baseline.sh

    report:
      needs: [full-e2e, golden-dataset, performance]
      steps:
        - name: Generate nightly report
          run: npm run report:nightly
        - name: Send Slack notification
          uses: slackapi/slack-github-action@v1
          with:
            payload: |
              {
                "text": "Nightly regression: ${{ needs.full-e2e.result }}, AI drift: ${{ needs.golden-dataset.result }}, Perf: ${{ needs.performance.result }}"
              }
        - name: Alert on failure
          if: failure()
          run: scripts/alert-on-failure.sh
```

### 10.5.2 Nightly Test Scope

| Test Suite | Tests | Time | Alert On |
|-----------|-------|------|----------|
| Full E2E (Chrome + Firefox) | ~50 tests × 2 browsers | ~20 min | Any P0/P1 failure |
| Golden dataset (deterministic) | ~71 entries | ~15 min | Accuracy < 85% |
| Drift detection | Golden dataset comparison | ~5 min | Drift > 5% |
| Performance baseline | Standard load test | ~10 min | P95 > 120% baseline |
| AI accuracy monitoring | Confidence score analysis | ~5 min | Mean confidence < 0.7 |

---

## 10.6 AI Model Change Impact Testing

### 10.6.1 When It Triggers

Model change testing is triggered when:
- LLM provider updates the model version
- Platform switches to a different model
- Model parameters change (temperature, max tokens)
- New fine-tuned model is deployed

### 10.6.2 Model Change Testing Pipeline

```
┌──────────────────┐
│ Model Change     │
│ Detected         │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐
│ Run Full Golden  │────▶│ Compare vs       │
│ Dataset (temp=0) │     │ Previous Baseline│
└──────────────────┘     └────────┬─────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │ < 5%     │ │ 5-15%    │ │ > 15%    │
              │ Change   │ │ Change   │ │ Change   │
              │ → Auto   │ │ → Review │ │ → Block  │
              │   approve│ │   + test │ │   + fix  │
              └──────────┘ └──────────┘ └──────────┘
```

### 10.6.3 Model Change Tests

| Test ID | Check | Threshold | Action |
|---------|-------|-----------|--------|
| MC-001 | Overall accuracy vs baseline | < 5% drop | Auto-approve |
| MC-002 | Schema compliance rate | Must be >= 95% | Block if below |
| MC-003 | Hallucination rate change | Must not increase > 3% | Block if above |
| MC-004 | Response time change | Must not increase > 50% | Warning if above |
| MC-005 | Test type distribution change | Must maintain min positive + negative | Block if missing types |
| MC-006 | Token usage change | Monitor for cost impact | Warning if > 20% increase |

---

## 10.7 Canary Testing for New Prompts

### 10.7.1 Canary Deployment Strategy

```
Production Traffic (100%)
         │
         ▼
┌──────────────────────┐
│  Canary Router       │
│  (Feature Flag)      │
├──────────┬───────────┤
│  95%     │    5%     │
│  Current │   New     │
│  Prompt  │   Prompt  │
│  v1.2    │   v1.3    │
└──────┬───┘───┬───────┘
       │       │
       ▼       ▼
  Collect metrics for both
       │       │
       ▼       ▼
┌──────────────────────┐
│  Compare Metrics     │
│  • Accuracy          │
│  • Confidence        │
│  • User acceptance   │
│  • Error rate        │
└──────────┬───────────┘
           │
     ┌─────┼─────┐
     ▼     ▼     ▼
  Promote  Hold   Rollback
  to 100%  at 5%  to 0%
```

### 10.7.2 Canary Success Criteria

| Metric | Measurement Period | Promote Criteria | Rollback Criteria |
|--------|-------------------|------------------|-------------------|
| Accuracy | 24 hours | >= current version accuracy | < 90% of current |
| Schema compliance | 24 hours | >= 98% | < 95% |
| Confidence scores | 24 hours | Mean >= current | Mean < 0.6 |
| User override rate | 48 hours | <= current | > 150% of current |
| Error rate | 24 hours | <= current | > 2x current |

### 10.7.3 Canary Monitoring

```javascript
// canary-monitor.js
const canaryMetrics = {
  async compare(currentVersion, canaryVersion, period = '24h') {
    const current = await getMetrics(currentVersion, period);
    const canary = await getMetrics(canaryVersion, period);

    return {
      accuracy: {
        current: current.accuracy,
        canary: canary.accuracy,
        delta: canary.accuracy - current.accuracy,
        verdict: canary.accuracy >= current.accuracy * 0.95 ? 'PASS' : 'FAIL'
      },
      schemaCompliance: {
        current: current.schemaCompliance,
        canary: canary.schemaCompliance,
        verdict: canary.schemaCompliance >= 0.98 ? 'PASS' : 'FAIL'
      },
      confidence: {
        current: current.meanConfidence,
        canary: canary.meanConfidence,
        verdict: canary.meanConfidence >= current.meanConfidence * 0.9 ? 'PASS' : 'FAIL'
      },
      overrideRate: {
        current: current.overrideRate,
        canary: canary.overrideRate,
        verdict: canary.overrideRate <= current.overrideRate * 1.5 ? 'PASS' : 'FAIL'
      },
      recommendation: 'PROMOTE' | 'HOLD' | 'ROLLBACK'
    };
  }
};
```

---

## 10.8 Pipeline Summary

| Stage | Trigger | Duration | Tests | Blocking |
|-------|---------|----------|-------|----------|
| Pre-commit | `git commit` | ~30s | Lint, format, secrets, types | Commit |
| PR Validation | PR created/updated | ~8 min | Unit, integration, AI schema, security | Merge |
| Post-merge | Merge to main | ~5 min | Build, deploy, smoke E2E | Deployment |
| Nightly | Cron 02:00 UTC | ~45 min | Full E2E, golden dataset, performance | Alerts |
| Pre-release | Manual / tag | ~2 hr | Full suite + perf + security | Release |
| Model change | Model version update | ~1 hr | Golden dataset + comparison | Deployment |
| Canary | New prompt version | 24-48 hr | A/B comparison metrics | Promotion |

---

*Previous: [09 — Performance & Scalability](./09-performance-scalability-testing.md) | Next: [11 — Test Data Strategy](./11-test-data-strategy.md)*
