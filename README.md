# Fagan Nomogram Bayesian Updater

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Standards:** CAP / CLSI / ISO / NIST

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## What It Does

Fagan Nomogram & Bayesian Diagnostic Probability Updater calculates composite scores from clinical measurements and classifies them into risk tiers. Includes an enterprise multi-agent evaluation platform with HMAC-SHA256 audit trails and zero-PHI outbound protection.

Author: Dr. Abu Suraih Sakhri · License: MIT

---

## Installation

```bash
# Core (zero-dependency)
pip install -e .

# With web API support
pip install -e ".[web]"

# With test dependencies
pip install -e ".[test]"

# Everything
pip install -e ".[all]"
```

---

## Usage

### 1. Single Evaluation (CLI)

```bash
python fagan_nomogram.py single --v1 14.5 --v2 4.2 --v3 1.8
```

### 2. Batch CSV Processing

```bash
python fagan_nomogram.py batch -i sample.csv -o results.csv
```

### 3. Enterprise Supervisor (Multi-Agent Evaluation)

```bash
# Run a single audit task
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Batch process via supervisor
python cli.py batch -i sample.csv -o dossier_results.csv

# Verify HMAC audit trail integrity
python cli.py verify-audit

# Query supervisory chat
python cli.py chat "Explain current calibration status"
```

### 4. REST API Server

```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

Or with Docker:

```bash
docker build -t fagan-nomogram-bayesian-updater .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret fagan-nomogram-bayesian-updater
```

### 5. High-Throughput Simulation

```bash
python simulator.py 1000
```

---

## Mathematical Formulation

The core `calculate_metrics()` function computes a weighted score:

```
score = v1 + v2/2 + v3/3 + ...
```

Classification tiers:
- **Low / Standard** (score < 10): Standard monitoring
- **Moderate / Intermediate** (10 ≤ score < 25): Close observation
- **High / Severe** (score ≥ 25): Urgent clinical intervention

---

## Security Architecture

* **Zero-PHI Outbound Interceptor:** AST and regex inspection blocking SSNs, MRNs, phone numbers, emails, DOBs, and patient names.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation. Integrity verification recomputes every signature.
* **Secure Secret Management:** No hardcoded secrets in production. `AUDIT_SECRET_KEY` must be provided via environment variable.
* **Path Traversal Protection:** All file I/O resolves and validates paths against directory traversal.

**Important:** Set `AUDIT_SECRET_KEY` in production. Without it, an ephemeral runtime key is generated (and a warning emitted), which means audit trails won't persist across restarts.

---

## Testing

```bash
# Run full test suite
pytest -v

# Run with coverage (if pytest-cov installed)
pytest -v --cov=.
```

The test suite covers:
- Core scoring and classification logic
- Batch CSV processing (including edge cases)
- PHI guard enforcement (MRN, SSN, phone, email patterns)
- Worker agent evaluation
- Supervisor consensus and audit trail
- HMAC integrity verification
- CLI commands (audit, chat, verify-audit)
- Enrichment module suite

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health check |
| GET | `/metrics` | Operational metrics (dossier count, audit blocks) |
| POST | `/api/audit` | Dispatch task across evaluation workers |
| POST | `/api/chat` | Supervisory conversational assistant |
| GET | `/api/audit/logs` | Retrieve and verify HMAC audit trail |

---

## Project Structure

```
fagan-nomogram-bayesian-updater/
├── fagan_nomogram.py     # Core scoring algorithm (zero-dependency)
├── cli.py                # Enterprise CLI (supervisor, batch, serve)
├── simulator.py          # High-throughput simulation
├── enrichment.py         # Enrichment engine suite
├── agents/
│   ├── __init__.py       # Package metadata
│   ├── api.py            # FastAPI REST server
│   ├── base.py           # Security guards, audit trail, PHI protection
│   ├── models.py         # Pydantic data models
│   ├── supervisor.py     # Multi-agent orchestrator
│   ├── workers.py        # Specialized evaluation workers
│   ├── llm_factory.py    # LLM provider abstraction
│   ├── learning.py       # Bayesian calibration engine
│   ├── metrics.py        # Prometheus metrics collector
│   └── streamer.py       # WebSocket telemetry broadcaster
├── tests/                # Pytest test suite
├── web/index.html        # Operations console (static)
├── pyproject.toml        # Package configuration
├── Dockerfile            # Container build
├── docker-compose.yml    # Production deployment
└── openapi_spec.json     # OpenAPI 3.1 specification
```
