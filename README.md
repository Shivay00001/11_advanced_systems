# 11_advanced_systems - Patterns & Resilience

> Production-grade advanced patterns demonstrating circuit breakers, rule engines, and resilience patterns.

## 🎯 Overview

This module implements:

- **Circuit Breaker** - Fault tolerance pattern
- **Rule Engine** - Business rules execution
- **Rate Limiter** - Request throttling
- **Retry with Backoff** - Transient failure handling
- **Bulkhead** - Resource isolation

## 📁 Structure

```
11_advanced_systems/
├── src/
│   ├── resilience/          # Resilience patterns
│   │   ├── circuit_breaker.py
│   │   ├── rate_limiter.py
│   │   ├── retry.py
│   │   └── bulkhead.py
│   ├── rules/               # Rule engine
│   │   ├── engine.py        # Rule execution
│   │   └── dsl.py           # Rule DSL
│   └── caching/             # Caching patterns
├── tests/                   # Test suite
└── pyproject.toml           # Dependencies
```

## 🚀 Quick Start

```bash
pip install -e .
python -m src.main
```

## 📄 License

MIT
