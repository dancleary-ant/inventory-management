---
name: verify
description: How to build, run, and drive this app end-to-end to verify changes.
---

# Verifying changes in this repo

## Launch

`uv` may not be installed — the backend has a committed venv:

```bash
# Backend (port 8001) — in-memory data, restart to reset state
cd server && .venv/bin/python main.py

# Frontend (port 3000)
cd client && npm run dev
```

Both must run OUTSIDE the sandbox (port binding is blocked inside).
Kill stale servers first: `lsof -ti:3000,8001 | xargs kill -9` — run
this unsandboxed too, or lsof won't see the processes.

Health checks: `curl localhost:8001/docs` and `curl localhost:3000`.

## Drive

- UI: browser tools against http://localhost:3000 — nav tabs are
  Overview, Inventory, Orders, Finance (/spending), Demand Forecast,
  Restocking, Reports.
- API: curl against http://localhost:8001/api/... (interactive docs
  at /docs).
- Data is in-memory from server/data/*.json; POSTs mutate process
  state only. Restart the backend after probing to clear test orders.

## Gotchas

- Known pre-existing console error on every page load: `GET
  /api/tasks` 404 (client calls it in App.vue but the backend has no
  tasks route). Not a regression.
- `GET /api/orders/{order_id}` looks up by numeric `id` ("1".."250"),
  not by order_number like "ORD-2025-0004".
- Language switcher (bottom of sidebar) toggles English/日本語 —
  check both when touching locales.
