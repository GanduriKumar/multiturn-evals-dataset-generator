# Eval Dataset Generator – Technical Requirements & Design (TRD)

## 1. Overview

The **Eval Dataset Generator** is an internal tool that generates **synthetic, structured evaluation datasets** and corresponding **golden datasets** for multi-turn LLM/agent evaluation across **multiple industry verticals**.

Examples of supported verticals:
- Commerce / Merchant
- Banking
- Insurance
- Healthcare
- Retail
- Telecom

The system is **vertical-agnostic** at the core, and each vertical brings its own:
- **Workflows** (business flows for that vertical)
- **User behaviours** (behaviour knobs)
- **Variation axes** (constraints / scenario conditions)

The system outputs:
- **Eval dataset** (`eval_dataset.jsonl`) – user turns + metadata for running evals.
- **Golden dataset** (`golden_dataset.jsonl`) – ideal conversation + expected actions, key facts, and scoring rules.
- Optional: **Scored results** (`scored_results.jsonl`) – when combined with external model outputs.

**Model execution (LLM/agent inference) is explicitly out of scope** for this system.

Each **generation request** targets **exactly one vertical**.

---

## 2. Goals

- Provide a **config-driven, repeatable** way to generate realistic multi-turn conversations for **any supported vertical**.
- Allow users to:
  - Select a vertical (e.g., commerce, banking).
  - Choose one or more **workflows** within that vertical.
  - Toggle **vertical-specific behaviours**.
  - Set **vertical-specific axes/constraints**.
- Emit both:
  - Eval datasets for LLM/agent runs.
  - Golden datasets for deterministic scoring.
- Support **template-based generation only** (no LLM in generation path) for:
  - determinism
  - compliance
  - ease of QA.
- Provide a **scoring harness** that:
  - consumes a golden dataset + model outputs.
  - computes structured metrics per conversation.

---

## 3. Non-goals

- Not a model runner / inference orchestrator.
- Not a general-purpose data labeling tool.
- Not intended for training data creation (primary use is **evaluation**, not model training).
- Not responsible for:
  - provisioning GPU/LLM infra.
  - long-term data warehousing.
  - dashboards (though data is designed for easy integration into BI).

---

## 4. Vertical, Workflow, Behaviour, and Axes

### Vertical

A **vertical** is a top-level industry or domain, e.g., `commerce`, `banking`, `insurance`. Each vertical has its own configuration and templates under `config/verticals/<vertical>/`.

### Workflows

Within each vertical, there are multiple **workflows** representing business flows.

Examples:
- **Commerce** – `ProductDiscoveryAndSearch`, `CheckoutAndPayments`, `ReturnsRefundsAndExchanges`, `TrustSafetyAndFraud`, etc.
- **Banking** – `LostOrStolenCard`, `AccountKYCUpdate`, `LoanEligibility`, `TransactionDispute`, etc.

The list of workflows is defined per vertical in a configuration file, e.g.:
`config/verticals/commerce/workflows.yaml`.

### Behaviours

Behaviours describe how the user behaves in the conversation. These are **vertical-specific**, but may reuse common patterns:

Examples (generic patterns):
- HappyPath
- ConstraintHeavyQueries
- AmbiguousQueries
- MultiTurnConversations
- UserCorrections
- AdversarialTrapQueries

Each vertical may define which behaviours it supports and how they are applied in its own `behaviours.yaml`.

### Axes / Constraints

Axes represent scenario conditions for the conversation. These are also **vertical-specific**.

Examples for **commerce**:
- price_sensitivity: HIGH | MED | LOW
- brand_bias: NONE | HIGH | MED
- availability: AVAILABLE | LOW | OUT_OF_STOCK
- policy_boundary: ALLOWED | PARTIAL_ALLOWED | NOT_ALLOWED

Examples for **banking** (illustrative):
- risk_level: LOW | MED | HIGH
- kyc_status: COMPLETE | PARTIAL
- transaction_type: POS | ONLINE | ATM

Each vertical defines its axes in `axes.yaml`.

---

## 5. Actors & Use Cases

### Actors

- **PM / Product Owner** – designs eval scenarios and golden expectations per vertical.
- **QA / Test Engineer** – uses datasets for regression testing and release validation.
- **Data Scientist / MLE** – compares models/agents using the generated evals across verticals.
- **Platform Engineer** – integrates generator & scorer into CI/CD or pipelines.

### Primary Use Cases

1. **Generate evaluation datasets** for a chosen vertical + workflows + behaviours + axes.
2. **Upload custom templates/schemas** to adapt to specific clients or merchants within a vertical.
3. **Upload golden dataset + model outputs** and obtain scored results.
4. **Slice results** by vertical, workflow, behaviour combination, or axes to understand weaknesses.

---

## 6. Functional Requirements

1. **Vertical Selection (FR-1)**
   - User must select exactly one `vertical` per generation request.
   - Supported verticals are defined in configuration.

2. **Vertical Config Discovery (FR-2)**
   - API endpoint `GET /config/verticals/{vertical}` returns:
     - list of workflows for that vertical,
     - list of behaviours,
     - axes and allowed values.

3. **Workflow Selection (FR-3)**
   - For the chosen vertical, user can select one or more workflows.
   - Each conversation belongs to exactly one workflow.

4. **Behaviour Selection (FR-4)**
   - For the chosen vertical, user can toggle any subset of behaviours (independent knobs).
   - Behaviours influence turn structure and template choices.

5. **Axes Configuration (FR-5)**
   - Axes are vertical-specific:
     - For commerce, axes may include price sensitivity, brand bias, availability, policy boundary.
     - For other verticals, axes are defined in config.
   - User must choose one value per axis.

6. **Dataset Generation (FR-6)**
   - For given `vertical`, `workflows`, `behaviours`, `axes`, and `num_samples_per_combo`:
     - Generate `N` conversations per (workflow × behaviour-set × axes) combination.
     - For each conversation:
       - `EvalConversation` (user-only turns + metadata).
       - `GoldenConversation` (full ideal conversation with scoring_rules).
   - Return datasets as a ZIP:
     - `eval_dataset.jsonl`.
     - `golden_dataset.jsonl`.
     - `manifest.json`.

7. **Schema Override via Upload (FR-7)**
   - API supports optional upload of:
     - vertical-specific workflow schema (`domain_schema`).
     - behaviour schema (`behaviour_schema`).
     - axes schema (`axes_schema`).
   - When provided, overrides default configs for that request.

8. **Scoring Harness Input (FR-8)**
   - Accepts:
     - `golden_dataset.jsonl`.
     - `model_outputs.jsonl`.
     - `model_id`.
   - Produces:
     - `scored_results.jsonl` (per-conversation scores).

9. **Frontend UI (FR-9)**
   - React-based UI to:
     - Select `vertical`.
     - Fetch vertical-specific workflows/behaviours/axes from `/config/verticals/{vertical}`.
     - Select workflows and behaviours, set axes values.
     - Set `num_samples_per_combo`, `language_locale`, `channel`.
     - Upload optional schema overrides.
     - Trigger dataset generation and download ZIP.
     - Upload `golden_dataset.jsonl` + `model_outputs.jsonl` and download scoring results.
     - View JSON config preview for transparency.
     - Manage local presets (saved configs) per vertical via `localStorage`.

---

## 7. Non-functional Requirements

- **NFR-1 – Determinism**  
  Given the same `vertical`, `config`, and random seed, generator must produce identical datasets.

- **NFR-2 – Performance**  
  Support generation of at least several thousand conversations per request without timeouts in standard deployment (exact thresholds TBD by infra).

- **NFR-3 – Reliability**  
  Robust error handling with meaningful error messages (400 vs 500).

- **NFR-4 – Security**  
  No PII or real customer data; all data is synthetic.
  Validate uploaded schemas; avoid dynamic code execution from untrusted input.

- **NFR-5 – Observability**  
  Structured logging for:
  - incoming configs,
  - errors,
  - generation counts,
  - scoring runs.

---

## 8. System Architecture

See `architecture-diagram.md` for the Mermaid diagram and description.

---

## 9. Data & File Artifacts

- `eval_dataset.jsonl`.
- `golden_dataset.jsonl`.
- `manifest.json`.
- `model_outputs.jsonl` (external producer).
- `scored_results.jsonl` (produced by scoring engine).

All follow the JSON schemas defined in the design.

---

## 10. API Specifications (Summary)

### `GET /health`

- Returns `{ "status": "ok" }` for readiness checks.

### `GET /config/verticals/{vertical}`

- **Purpose:** Return configuration metadata for the selected vertical.
- **Response (200):**
  - `vertical`: string
  - `workflows`: array of workflow IDs/names
  - `behaviours`: array of behaviour IDs/names
  - `axes`: object of axis names → allowed values

### `POST /generate-dataset`

- **Request:** `multipart/form-data`  
  - `config`: JSON string of `GenerationRequest` (includes `vertical`, `workflows`, `behaviours`, `axes`, etc.).
  - `domain_schema` (optional file) – vertical-specific workflows override.
  - `behaviour_schema` (optional file).
  - `axes_schema` (optional file).

- **Response:** `application/zip`  
  - `eval_dataset.jsonl`.
  - `golden_dataset.jsonl`.
  - `manifest.json`.

### `POST /score-run`

- **Request:** `multipart/form-data`.
  - `golden_dataset`: file (JSONL).
  - `model_outputs`: file (JSONL).
  - `model_id`: text.

- **Response:** `application/jsonl`  
  - `scored_results.jsonl` (as file stream).

---

## 11. Configuration & Templates

Directory layout (example):

```text
config/
  verticals/
    commerce/
      workflows.yaml
      behaviours.yaml
      axes.yaml
      utterances/
        returns_refunds_templates.yaml
        checkout_payments_templates.yaml
        ...
    banking/
      workflows.yaml
      behaviours.yaml
      axes.yaml
      utterances/
        lost_card.yaml
        kyc_update.yaml
        ...
    ...
```

All configs are versioned with the codebase.

---

## 12. Error Handling & Logging

- Validation errors → HTTP 400 with structured error response.
- Internal exceptions → HTTP 500 with generic error + correlation ID.
- Log:
  - vertical, workflows, behaviours, axes, sample counts.
  - error stack traces to central logging.

---

## 13. Security & Compliance

- No real user data; synthetic only.
- Uploaded schemas are treated as data, not code.
- CORS restricted to internal frontend domains in production.
- AuthN/AuthZ can be added via reverse proxy or API gateway if needed.

---

## 14. Deployment & Environments

- Containerized FastAPI service (e.g., Docker).
- React frontend served via static hosting or behind a reverse proxy.
- Environments:
  - `dev` – active development & debugging.
  - `stage` – integration testing.
  - `prod` – internal production use.

---

## 15. Open Issues / Risks

- Quality of scoring depends on heuristics / detectors; might need iterative refinement.
- Template coverage across all verticals and workflows will grow over time.
- Might later want an LLM-as-judge mode; design scoring engine to be pluggable.
