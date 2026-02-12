# Slide 5 — Module 1: Jira Ingestion & Validation

## The Gateway — Where Everything Begins

---

## Module Overview

The Jira Ingestion module is the **entry point** of the entire platform. It connects to Jira, retrieves stories/bugs/tasks, validates their structure, and normalizes them into a canonical format that downstream agents can consume.

> **Architect's Rule:** If garbage enters here, every downstream agent produces garbage. This module must be the most defensively coded component in the system.

---

## Responsibilities

| Responsibility | What It Does | Why It Matters |
|---------------|-------------|----------------|
| **Read Jira ID / Raw Story** | Connect via OAuth/API token, fetch story by ID or batch by project | This is the system's only external data source |
| **Validate Structure** | Check that required fields (summary, description, AC) exist and are well-formed | Missing fields cause downstream failures |
| **Normalize Content** | Strip HTML, resolve Jira macros, standardize field names, encode properly | Consistent input format for the AI layer |

---

## Architecture Detail

```
┌───────────────┐     ┌───────────────────┐     ┌───────────────────┐
│   JIRA API    │────▶│   CONNECTOR       │────▶│   PARSER          │
│  (Cloud/Server)│     │   • Auth (OAuth)  │     │   • Extract fields│
│               │     │   • Rate limiting  │     │   • Strip HTML    │
│               │     │   • Retry logic    │     │   • Resolve macros│
└───────────────┘     └───────────────────┘     └────────┬──────────┘
                                                          │
                                                          ▼
                      ┌───────────────────┐     ┌───────────────────┐
                      │   NORMALIZER      │◀────│   VALIDATOR       │
                      │   • Canonical     │     │   • Required      │
                      │     format        │     │     fields check  │
                      │   • Encoding fix  │     │   • Format check  │
                      │   • Field mapping │     │   • Size limits   │
                      └────────┬──────────┘     └───────────────────┘
                               │
                               ▼
                      ┌───────────────────┐
                      │  NORMALIZED       │
                      │  STORY OUTPUT     │
                      │  (JSON payload)   │
                      └───────────────────┘
```

---

## Testing Considerations — What Can Go Wrong

### 1. Empty or Malformed Stories

| Scenario | Input | Expected Behavior |
|----------|-------|-------------------|
| No acceptance criteria | Story with empty AC field | Flag as "incomplete", route to human review |
| No description at all | Story with only title | Return validation error with specific missing fields |
| HTML-heavy description | Story written in Jira rich text with tables, images, code blocks | Parse correctly, extract text content, preserve structure |
| Extremely long story | 10,000+ character description | Accept but truncate/chunk for downstream processing with warning |
| Non-English content | Story written in Japanese, Hindi, etc. | Either process or clearly reject with language unsupported error |
| Jira macros/plugins | Story uses Jira macros like `{code}`, `{panel}`, `{noformat}` | Resolve macros to plain text, don't pass raw macro syntax |

### 2. Unsupported Formats

| Scenario | Expected Behavior |
|----------|-------------------|
| Story has only attachments (no text) | Flag as unsupported, log reason |
| Story type is "Epic" (not a testable story) | Filter out or convert sub-tasks to testable units |
| Story in a custom Jira workflow with non-standard fields | Use field mapping configuration, warn on unmapped fields |

### 3. Access & Permission Checks

| Scenario | Expected Behavior |
|----------|-------------------|
| Expired OAuth token | Return 401, trigger re-authentication flow |
| User lacks project access | Return 403 with clear "no access to project X" message |
| Jira server is unreachable | Return connection error after timeout, retry with backoff |
| Rate limit exceeded (429) | Queue request, retry after `Retry-After` header value |
| Jira instance returns 500 | Log error, do not retry indefinitely, alert operator |

---

## Test Cases — Functional

| TC ID | Test Case | Priority | Type |
|-------|-----------|----------|------|
| JI-001 | Fetch valid story by ID — all fields populated | P0 | Positive |
| JI-002 | Fetch story with missing AC — validation flags it | P0 | Negative |
| JI-003 | Fetch story with rich text/HTML — parser strips correctly | P1 | Positive |
| JI-004 | Fetch with expired token — returns clear auth error | P0 | Negative |
| JI-005 | Fetch from unauthorized project — returns 403 | P1 | Negative |
| JI-006 | Jira server down — timeout and retry behavior | P1 | Negative |
| JI-007 | Rate limit (429) — backoff and retry | P2 | Negative |
| JI-008 | Bulk fetch 100 stories — pagination works correctly | P1 | Positive |
| JI-009 | Story with special characters (XSS payload) — sanitized | P0 | Security |
| JI-010 | Story with Jira macros — resolved to plain text | P2 | Positive |
| JI-011 | Normalized output matches expected JSON schema | P0 | Contract |
| JI-012 | Concurrent fetch requests — no data mixing | P1 | Concurrency |

---

## Test Cases — Integration

| TC ID | Test Case | Validates |
|-------|-----------|-----------|
| JI-INT-001 | Ingestion output feeds correctly to Requirement Agent | Layer 1 → Layer 2 contract |
| JI-INT-002 | Validation error stops pipeline (doesn't reach AI layer) | Error propagation |
| JI-INT-003 | Bulk ingestion feeds multiple stories to parallel Requirement Agents | Throughput and isolation |

---

## Metrics for This Module

| Metric | Formula | Target | Alert Threshold |
|--------|---------|--------|-----------------|
| **Ingestion Success Rate** | (successful fetches / total attempts) × 100 | >= 98% | < 95% |
| **Parsing Error Rate** | (parsing failures / total parsed) × 100 | < 2% | > 5% |
| **Validation Pass Rate** | (stories passing validation / total stories) × 100 | >= 90% | < 85% |
| **Avg Ingestion Latency** | Mean time from API call to normalized output | < 2 seconds | > 5 seconds |
| **Rate Limit Hit Rate** | (429 responses / total API calls) × 100 | < 1% | > 3% |

---

## Architect's Testing Strategy

```
Unit Tests:
  • Parser logic for each Jira field type (text, rich text, arrays, custom fields)
  • Validator rules for each required field
  • Normalizer transformations (HTML strip, encoding, field mapping)

Integration Tests:
  • Real Jira sandbox with known test stories
  • WireMock for simulated Jira API responses (errors, rate limits, timeouts)
  • Contract tests verifying output schema matches Requirement Agent's expected input

E2E Smoke Test:
  • Fetch a real story → validate it → normalize it → verify output structure
  • Run on every deployment

Performance Tests:
  • Bulk fetch 500 stories — measure throughput and memory
  • Concurrent requests — verify thread safety and data isolation
```

---

## Edge Cases to Never Forget

1. **Jira field renamed by admin** — Your parser looks for `customfield_10023` but it was renamed. Use configurable field mapping, not hardcoded field IDs.
2. **Story updated mid-ingestion** — You start fetching a story, and someone edits it before you finish. Use versioning or timestamp to detect stale data.
3. **Unicode edge cases** — Emojis, RTL languages, zero-width characters in story text. Test with real-world multi-language content.

---

*This module is "simple" in concept but critical in execution. A Testing Architect treats it with the same rigor as a database layer — because it IS the data layer for the entire platform.*
