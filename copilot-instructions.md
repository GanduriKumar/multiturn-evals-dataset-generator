# Copilot instructions for this repo

## Purpose

Vertical‑agnostic eval dataset generator. The FastAPI backend builds evaluation
datasets and golden expectations from YAML config and templates. The React/Vite
frontend drives generation and scoring uploads.

## Architecture

Backend (`backend/app/`): FastAPI routes in `backend/app/main.py`.
Config loader: `backend/app/config_loader.py` reads
`config/verticals/<vertical>/{workflows,behaviours,axes}.yaml` and
`templates/*.yaml`.
Template engine: `backend/app/template_engine.py` selects and renders templates
for user/assistant turns.
Generation: `backend/app/generation.py` builds `ConversationPlan` objects and
manifests.
Dataset builders: `backend/app/dataset_builder.py` emits
`<dataset_id>.dataset.json` and `<dataset_id>.golden.json`.
Scoring: `backend/app/scoring.py` scores JSONL inputs (legacy format) for
`/score-run`.
Frontend (`frontend/`): React + Vite UI with proxy routes in
`frontend/vite.config.ts`.

## Core workflows

Backend dev: `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000`.
Frontend dev: in `frontend/` run `npm install` then `npm run dev` (backend at
<http://localhost:8000>).
API endpoints: `GET /health`, `GET /config/verticals/{vertical}`,
`POST /generate-dataset` (multipart form, returns ZIP with dataset/golden +
manifest), and `POST /score-run` (JSONL in/out for heuristic scoring).

## Conventions and patterns

Dataset outputs are JSON (not JSONL): `<dataset_id>.dataset.json` and
`<dataset_id>.golden.json`.
Dataset JSON contains `dataset_id`, `version`, `metadata`, and `conversations`
(user‑only turns).
Golden JSON contains `dataset_id`, `version`, and `entries` with expected
variants and policy decision.
Scoring endpoint expects JSONL entries with `expected_actions`, `key_facts`,
`scoring_rules` (legacy format).
Templates live in `config/verticals/<vertical>/templates/*.yaml` and may use
`{variable}` placeholders.
Conversation IDs use a normalized domain/behavior/axes + hash format.

## Integration points

Vite proxy routes: `/config`, `/generate-dataset`, `/score-run` → backend on
port 8000. There is no database; file system outputs are streamed as ZIPs for
download.

## Pitfalls and gotchas

`TemplateEngine.realise_turn` raises if no template matches; ensure templates
cover workflows/behaviours/axes.
`/score-run` is not wired to the generated golden JSON format; it expects JSONL
with explicit scoring fields.
For deterministic generation, supply `random_seed` and keep `min_turns` and
`max_turns` stable.

## Key references

Backend entrypoint: `backend/app/main.py`.
Generation: `backend/app/generation.py`.
Dataset structure: `backend/app/dataset_builder.py`.
Config examples: `config/verticals/`.
Frontend UI: `frontend/src/App.tsx`.
