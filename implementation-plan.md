# Implementation Plan – Vertical-Agnostic Eval Dataset Generator (with Tailwind CSS Frontend)

This plan is designed to be executed using **GitHub Copilot Chat (VS Code)** with **Tailwind CSS** for styling the frontend UI.

For each phase:
1. Paste the **Implementation Prompt** into Copilot.
2. Review generated code.
3. Paste the **Tests Prompt** and write tests.
4. Run & verify before advancing.

> **Important:** App is **vertical-agnostic**, supports **one vertical per generation request**, and loads workflows, behaviours, and axes dynamically from backend configuration.

---

## Phase 0 – Repo Setup & Tailwind Integration

### Prompt 0.1 – Monorepo + Tailwind Setup

> Create a monorepo folder structure:
> ```text
> repo/
>   backend/
>   frontend/
> ```
>
> In `frontend/`:
> - Initialize React + TypeScript project using Vite.
> - Install Tailwind CSS following official docs (postcss + autoprefixer).
> - Create `tailwind.config.js` with content paths.
> - Update `index.css` to import Tailwind layers:
>   ```css
>   @tailwind base;
>   @tailwind components;
>   @tailwind utilities;
>   ```
>
> In `backend/`:
> - Create FastAPI skeleton with `/health`.
> - Add dependencies: fastapi, uvicorn, pydantic, python-multipart, pyyaml.
> Generate minimal placeholder code.

### Prompt 0.2 – Tailwind + Layout Tests

> Write tests or visual checks that Tailwind builds successfully:
> - Ensure `npm run dev` shows Tailwind styles.
> - Ensure a sample `<button class="bg-blue-600 text-white">` renders as expected.

---

## Phase 1 – Core Models & Config Endpoint

### Prompt 1.1 – Pydantic Models

> In `backend/app/models.py`, create models:
> - `IndustryVertical` enum
> - `GenerationRequest`
> - `BehaviourFlag`
> - Generic `axes: Dict[str, str]`
> - `workflows: List[str]`
> - Full schema as previously defined.

### Prompt 1.2 – `/config/verticals/{vertical}` Endpoint

> Implement FastAPI endpoint returning per-vertical:
> - workflows
> - behaviours
> - axes definitions
> Use YAML configs under `config/verticals/<vertical>/...`.

### Prompt 1.3 – Basic Tests

> Add tests ensuring valid vertical loads workflows, behaviours, and axes.

---

## Phase 2 – Config Loader + Template Engine

### Prompt 2.1 – Vertical Config Loader

> Implement loader:
> - `load_vertical_config(vertical)` – reads workflows.yaml, behaviours.yaml, axes.yaml
> - `load_vertical_templates(vertical)` – loads utterance YAMLs per workflow
>
> Add error handling for missing files.

### Prompt 2.2 – Template Engine

> Add `TemplateEngine.realise_turn()` selecting template based on:
> - vertical
> - workflow
> - speaker
> - role
> - behaviour
> - axes branches
> Render NL with `.format()`.

### Prompt 2.3 – Tests

> Add fixture configs under `tests/data/config/...` and test the loader + TemplateEngine.

---

## Phase 3 – Dataset Generation Engine

### Prompt 3.1 – Conversation Plan

> Implement `ConversationPlan` with fields:
> - vertical
> - workflow
> - scenario_id
> - behaviours
> - axes
> - turn_plan
>
> Add a demo workflow (ReturnsRefunds for commerce).

### Prompt 3.2 – Eval & Golden Builders

> Implement builders to emit `eval_dataset.jsonl` and `golden_dataset.jsonl`.

### Prompt 3.3 – Tests

> Test both builders:
> - eval: user-only turns
> - golden: user + agent_expected

---

## Phase 4 – Scoring Engine

### Prompt 4.1 – Scoring Module

> Implement scoring with heuristics for:
> - expected_actions
> - key_facts
> - policy violations

### Prompt 4.2 – `/score-run` Endpoint

> Accept files, run scoring, return `scored_results.jsonl`.

### Prompt 4.3 – Tests

> Add tests using local fixtures.

---

## Phase 5 – React Frontend (Tailwind Styled)

### Prompt 5.1 – Vertical Selector + Config Fetch

> Build React UI using Tailwind:
> - Add a top-level vertical dropdown:
>   ```jsx
>   <select className="border p-2 rounded bg-white shadow">
>   ```
> - On change, call `/config/verticals/{vertical}`.
> - Populate:
>   - workflow checkboxes
>   - behaviour checkboxes
>   - axis dropdowns
>
> Use Tailwind utility classes for:
> - spacing (`p-4`, `m-2`)
> - colors (`bg-gray-100`, `text-blue-600`)
> - layout (`grid`, `gap-4`, `flex`, `rounded`, `shadow`)
>
> Example card:
> ```html
> <div class="bg-white p-4 rounded shadow border border-gray-200">
>   ...
> </div>
> ```

### Prompt 5.2 – JSON Preview Panel (Tailwind)

> Add preview box:
> ```html
> <pre class="bg-gray-900 text-green-300 text-sm p-4 rounded overflow-auto">
>   {json}
> </pre>
> ```

### Prompt 5.3 – Presets per Vertical

> Save presets as:
> `eval_preset_${vertical}_${presetName}`.

### Prompt 5.4 – File Upload + Generate Button

> Add Tailwind button styles:
> ```html
> <button class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded shadow">
> ```

### Prompt 5.5 – Scoring Upload UI

> Add inputs for golden, model_outputs, model_id:
> ```html
> <input type="file" class="block p-2 border rounded" />
> ```

---

## Phase 6 – Polish, Logging, CI

### Prompt 6.1 – Logging

> Add structured logs for vertical, workflows, behaviours, axes.

### Prompt 6.2 – GitHub Actions CI

> Build steps:
> - Install Node + Python
> - Build frontend
> - Run backend tests
> - Optional scoring smoke test
