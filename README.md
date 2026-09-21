# 11_advanced_systems

> Python reliability and decision-engineering foundation for circuit breakers, retries, rate limiting, bulkheads, rule evaluation, and caching.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Reliability](https://img.shields.io/badge/Focus-Resilience%20Engineering-0F766E)](https://sre.google/sre-book/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-Custom%20Commercial-orange)](./LICENSE)

This repository provides reusable patterns for building services that remain predictable under dependency failures, traffic spikes, transient errors, and changing business rules.

It combines fault-tolerance controls with rule execution and caching patterns so application teams can protect resources, control retries, and make failure behavior explicit.

> **Operational notice:** Resilience controls must be tuned to the behavior of the dependency and workload. Incorrect retry or timeout settings can amplify outages.

## What this project includes

- circuit breaker state management
- retry with exponential backoff
- rate limiting and request throttling
- bulkhead resource isolation
- rule engine and rule DSL extension points
- caching patterns
- Pydantic configuration models
- structured operational logging
- test-oriented modular design

## Repository structure

```text
11_advanced_systems/
├── src/
│   ├── resilience/
│   │   ├── circuit_breaker.py
│   │   ├── rate_limiter.py
│   │   ├── retry.py
│   │   └── bulkhead.py
│   ├── rules/
│   │   ├── engine.py
│   │   └── dsl.py
│   ├── caching/
│   └── main.py
├── tests/
├── pyproject.toml
├── README.md
├── LICENSE
├── .env.example
└── .gitignore
```

## Reliability architecture

```text
┌──────────────────────────────────────────────────────────────────┐
│                         Application Request                       │
└──────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Protection and Control Layer                    │
│ timeout │ rate limit │ bulkhead │ circuit breaker                  │
└──────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                         Dependency Call                            │
│                 retry policy │ idempotency │ caching                │
└──────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                       Decision and Rules                           │
│                 rule evaluation │ policy outcome                    │
└──────────────────────────────────────────────────────────────────┘
```

## Core patterns

### Circuit breaker

A circuit breaker prevents repeated calls to an unhealthy dependency. Typical states are:

- **closed:** calls flow normally while failures are tracked
- **open:** calls fail fast during a configured recovery window
- **half-open:** a limited probe checks whether recovery occurred

Configure failure thresholds, recovery windows, and probe concurrency per dependency.

### Retry with backoff

Retries are appropriate for transient failures, not permanent validation or authorization errors. Use:

- bounded retry counts
- exponential backoff
- jitter to avoid synchronized retries
- clear exception allowlists
- total time budgets
- idempotency protection for writes

### Rate limiting

Rate limits protect services and dependencies from overload. Document whether limits are per user, tenant, API key, IP, or global, and define behavior when the limit is exceeded.

### Bulkheads

Bulkheads isolate resource pools so one slow or failing workload cannot consume all workers, connections, or queue capacity. Monitor rejected work and pool saturation.

### Rule engine

Rule evaluation should be deterministic, explainable, and versioned. Rules should define:

- input schema
- evaluation order
- priority and conflict behavior
- output or decision format
- validation and failure behavior
- audit and test expectations

Never execute untrusted rule code without strict sandboxing and review.

## Quick start

### Prerequisites

- Python 3.10+
- pip and virtual environment support
- a test suite for validating failure and recovery behavior

### Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

### Configure environment

```bash
cp .env.example .env
```

Example configuration:

```env
APP_ENVIRONMENT=development
DEFAULT_TIMEOUT_SECONDS=5
RETRY_MAX_ATTEMPTS=3
RETRY_BASE_DELAY_SECONDS=0.25
CIRCUIT_FAILURE_THRESHOLD=5
CIRCUIT_RECOVERY_TIMEOUT_SECONDS=30
RATE_LIMIT_PER_SECOND=20
BULKHEAD_MAX_CONCURRENCY=10
```

### Run the example

```bash
python -m src.main
```

## Production tuning guidance

Avoid copying default values directly into production. Tune controls using dependency behavior, traffic volume, and measured latency.

- set timeouts below the caller's overall deadline
- ensure retry time is included in the total request budget
- avoid retries for non-idempotent writes unless operations are deduplicated
- use jitter with exponential backoff
- coordinate client and server rate limits
- expose circuit state and rejected-call metrics
- protect critical resources with separate bulkheads
- test recovery, not just failure

## Testing checklist

Test at minimum:

- dependency timeouts and connection failures
- retry exhaustion and exception filtering
- circuit transitions between closed, open, and half-open
- concurrent half-open probes
- rate-limit boundaries and clock behavior
- bulkhead saturation and release after failure
- cache expiry, stale data, and invalidation
- rule ordering, conflicts, invalid inputs, and version changes
- idempotent handling of retried operations

## Production-readiness assessment

### Current maturity: strong resilience-pattern foundation

This repository provides reusable patterns, but resilience behavior must be validated in the context of each service and dependency. Add load testing, failure injection, and operational dashboards before production adoption.

### Strengths

- focuses on common reliability failure modes
- separates resilience controls into reusable modules
- includes rule-engine and caching extension points
- supports predictable failure and recovery behavior
- suitable for APIs, workers, and integration services

### Production gaps to address

1. Add dependency-specific timeout and retry policies.
2. Add metrics for retries, rejects, opens, probes, and fallbacks.
3. Add distributed rate-limit storage where multiple instances require shared limits.
4. Add bounded queues and cancellation propagation.
5. Add chaos and load-testing scenarios.
6. Define fallback behavior for every protected dependency.
7. Add rule versioning, approvals, and audit history.
8. Document incident response and rollback procedures.

## Observability

Track at least:

- request and dependency latency
- retry count and retry exhaustion
- circuit-breaker state transitions
- rate-limit rejects
- bulkhead queue depth and rejected work
- cache hit and miss rates
- fallback usage
- rule evaluation duration and outcomes

Include dependency name and operation as controlled labels; avoid unbounded request or customer identifiers.

## Security considerations

Before deploying:

- validate rule inputs and avoid unsafe dynamic execution
- enforce tenant and authorization boundaries before rule evaluation
- avoid exposing internal failure details to clients
- protect configuration and administrative controls
- prevent sensitive values from entering logs
- review cache keys for cross-user or cross-tenant leakage
- use secure defaults for remote dependency connections

## Monetization opportunities

| Business model | Best use case |
| --- | --- |
| resilience toolkit | reusable reliability layer for SaaS teams |
| SRE consulting | failure-mode and capacity modernization |
| rules platform | configurable business decision workflows |
| integration gateway | protected third-party API orchestration |
| managed reliability service | monitoring and tuning for production systems |

## GitHub discoverability

This repository is positioned around:

- Python circuit breaker pattern
- retry with exponential backoff
- rate limiter and bulkhead isolation
- resilience engineering toolkit
- Python rule engine
- fault-tolerant API integrations
- distributed systems reliability patterns

To improve discoverability:

- add state-transition diagrams and examples
- publish failure-injection tests
- document policy tuning by dependency type
- include benchmark and load-test results
- show metrics and dashboards for resilience controls

## Roadmap ideas

- add async-native resilience primitives
- add Redis-backed distributed rate limiting
- add OpenTelemetry instrumentation
- add fallback and hedged-request patterns
- add chaos-testing utilities
- add rule version registry and approvals
- add adaptive concurrency limits
- add configuration validation and policy linting

## Contributing

Contributions are welcome for:

- resilience algorithm improvements
- async and distributed implementations
- rule validation and versioning
- cache correctness and invalidation
- test and failure-injection coverage
- documentation and operational examples

Please do not submit production credentials, private service URLs, or sensitive business rules.

## License

This repository contains a custom commercial license in `LICENSE`.

Review the complete license before personal earning, commercial, enterprise, redistribution, or client deployment use.
