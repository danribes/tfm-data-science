# Archived: Sovereign Fiscal Scenario Explorer (MVP v1)

Archived 2026-08-06 at the user's request to clear the workspace for a new
app design that consolidates this MVP's plans, the earlier Plan Predictor
project (`legacy/old`), and the v01-v16 design mockups (`legacy/design_data`).

This is the complete, working MVP as merged to master (final commit
`844c0c9`): 67/67 tests passing, live-verified in the browser. Nothing was
deleted — the full history is in git, and this folder is a working snapshot.

To run it again from this folder, the package imports expect to run from a
root containing `app/`, `data/`, `engine/`, `personas/` — either move these
folders back to the repo root, or run from inside `archive/mvp-app-v1/`:

```bash
cd archive/mvp-app-v1
../../.venv/bin/python -m streamlit run app/main.py
```

(The `sys.path.insert` in `app/main.py` anchors imports to this folder's
root, so running from here works as-is.)

Design spec and implementation plan for this MVP remain in
`docs/superpowers/`.
