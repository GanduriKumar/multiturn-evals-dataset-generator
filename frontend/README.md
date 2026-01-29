# Eval Dataset Generator – Frontend

This frontend is a React + Vite UI for generating evaluation datasets and uploading scoring inputs.

## Prerequisites

- Node.js 18+
- Backend running on <http://localhost:8000>

## Run the frontend (development)

1. Install dependencies:
   - `npm install`
2. Start the dev server:
   - `npm run dev`

The app will run on <http://localhost:5173> and proxy API calls to the backend as
defined in `vite.config.ts`.

## Key routes (proxied)

- `/config` → backend config endpoints
- `/generate-dataset` → dataset generation
- `/score-run` → legacy JSONL scoring

## Build for production

- `npm run build`
- `npm run preview`

## Notes

- The UI expects dataset generation to return a ZIP containing `<dataset_id>.dataset.json`, `<dataset_id>.golden.json`, and `manifest.json`.
- Scoring uses JSONL inputs (`golden_dataset.jsonl`, `model_outputs.jsonl`).
