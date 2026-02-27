# FastAPI Market Endpoint Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Bootstrap a minimal FastAPI server with a `/api/market` endpoint using strict TDD (failing test first, then minimal implementation).

**Architecture:** Single FastAPI app module (`app/main.py`) with one route returning a typed JSON response. Tests use `httpx` via `TestClient` from `starlette.testclient`. Each task is a self-contained RED-GREEN commit.

**Tech Stack:** Python 3.11+, FastAPI, pytest, httpx (for TestClient)

---

## Constraints

- Modify at most **1 production file** and **1 test file** per task.
- Write failing pytest **FIRST** — no production code before a failing test.
- No external APIs. No refactors. YAGNI.

---

### Task 1: RED — Write the failing test for GET /api/market

**Files:**
- Create: `tests/test_market_endpoint.py`

**Step 1: Write the failing test**

```python
# tests/test_market_endpoint.py
from fastapi.testclient import TestClient


def test_get_market_returns_200_with_schema():
    from app.main import app  # will fail: module does not exist yet
    client = TestClient(app)
    response = client.get("/api/market")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["symbol"], str)
    assert isinstance(body["data"], list)
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_market_endpoint.py -v
```

Expected: **FAIL** — `ModuleNotFoundError: No module named 'app'`
(Failing for the right reason — the app does not exist yet.)

**Step 3: Commit the failing test**

```bash
git add tests/test_market_endpoint.py
git commit -m "test(RED): add failing test for GET /api/market schema"
```

---

### Task 2: GREEN — Implement minimal FastAPI app to pass the test

**Files:**
- Create: `app/__init__.py` (empty)
- Create: `app/main.py`

**Step 1: Write minimal implementation**

```python
# app/main.py
from fastapi import FastAPI

app = FastAPI()


@app.get("/api/market")
def get_market():
    return {"symbol": "AAPL", "data": []}
```

**Step 2: Run test to verify it passes**

```bash
pytest tests/test_market_endpoint.py -v
```

Expected: **PASS** — `test_get_market_returns_200_with_schema PASSED`

**Step 3: Commit the implementation**

```bash
git add app/__init__.py app/main.py
git commit -m "feat(GREEN): add minimal FastAPI app with /api/market endpoint"
```

---

## Notes

- `requirements.txt` should include `fastapi`, `uvicorn`, `httpx`, `pytest`.
- Task 1 is intentionally commit-only (RED) — no production code touches this commit.
- Task 2 is the minimum code to turn RED → GREEN. No models, no DB, no config.
