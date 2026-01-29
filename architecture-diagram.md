# Eval Dataset Generator – Architecture (Vertical-Agnostic)

```mermaid
flowchart LR
  subgraph FE[Frontend]
    UI[React Web UI
"Eval Dataset Generator"]
  end

  subgraph BE[Backend - FastAPI Service]
    API[REST API Layer
/health, /config/verticals/{vertical}, /generate-dataset, /score-run]
    CFGLOADER[Vertical Config Loader
Loads workflows, behaviours, axes per vertical]
    GEN[Dataset Generation Engine
  - Scenario planner
  - Workflow & behaviour logic
  - Dataset JSON builder]
    TPL[Template Engine
Vertical-specific YAML utterance templates]
    SC[Scoring Engine
- Action match
- Fact accuracy
- Policy checks]
    FS[(Storage / File System)
(local disk, blob, or NFS)]
  end

  subgraph CFG[Config Assets]
    VERTS[Vertical Definitions
(e.g. commerce, banking, insurance)]
    WF_CFG[Workflows per Vertical
config/verticals/<vertical>/workflows.yaml]
    BEH_CFG[Behaviours per Vertical
config/verticals/<vertical>/behaviours.yaml]
    AXES_CFG[Axes per Vertical
config/verticals/<vertical>/axes.yaml]
    UT_CFG[Utterance Templates per Vertical
  config/verticals/<vertical>/templates/*.yaml]
  end

  subgraph EXT[External Systems (Out of Scope)]
    MR[Model / Agent Runner
  Uses <dataset_id>.dataset.json
  Produces model_outputs.jsonl]
  end

  UI -->|Select vertical
Fetch config| API
  API -->|GET /config/verticals/{vertical}| CFGLOADER
  CFGLOADER -->|workflows, behaviours, axes| API
  API -->|send config JSON| UI

  UI -->|Chosen vertical, workflows, behaviours, axes, counts
+ optional schema overrides| API
  API -->|POST /generate-dataset| GEN

  GEN -->|reads vertical config| CFGLOADER
  GEN -->|uses templates| TPL
  GEN -->|writes
(<dataset_id>.dataset.json,
<dataset_id>.golden.json,
manifest.json)| FS
  API -->|returns ZIP| UI

  MR -->|reads <dataset_id>.dataset.json
(runs outside this system)| FS
  MR -->|writes model_outputs.jsonl| FS

  UI -->|Upload golden_dataset.jsonl
+ model_outputs.jsonl
+ model_id| API
  API -->|POST /score-run| SC
  SC -->|reads golden + model_outputs| FS
  SC -->|writes scored_results.jsonl| FS
  API -->|returns scored_results.jsonl| UI

  VERTS -.-> CFGLOADER
  WF_CFG -.-> CFGLOADER
  BEH_CFG -.-> CFGLOADER
  AXES_CFG -.-> CFGLOADER
  UT_CFG -.-> TPL
```

## Key Concepts

- **Vertical** – An industry or domain such as commerce, banking, insurance, healthcare, etc.
- **Workflow** – A business flow within a vertical (e.g., for commerce: Returns & Refunds; for banking: Lost Card).
- **Behaviours** – User behaviour knobs defined per vertical (e.g., ambiguous, adversarial, multi-turn).
- **Axes/Constraints** – Scenario conditions defined per vertical (e.g., price sensitivity, risk level, policy boundary).

## Key Components

- **Frontend (React)** – Lets the user:
  - Select a vertical
  - See vertical-specific workflows, behaviours, and axes
  - Configure generation parameters
  - Upload optional overrides, golden + model outputs
  - Download datasets and scoring results

- **Backend (FastAPI)** – Exposes:
  - `GET /config/verticals/{vertical}` to return workflows/behaviours/axes for that vertical
  - `POST /generate-dataset` to generate eval & golden datasets
  - `POST /score-run` to score model outputs against golden

- **Vertical Config Loader** – Loads per-vertical configuration from
  `config/verticals/<vertical>/...`.

- **Template Engine** – Uses vertical-specific YAML templates to realise natural language for user and agent turns.

- **Dataset Generation Engine** – Builds `<dataset_id>.dataset.json` and
  `<dataset_id>.golden.json` for the selected vertical and workflows, applying
  behaviours and axes.

- **Scoring Engine** – Compares model outputs to the legacy JSONL golden inputs
  and produces `scored_results.jsonl` with metrics per conversation.

- **External Model Runner (Out of Scope)** – Any external system that runs an
  LLM/agent on `<dataset_id>.dataset.json` and produces `model_outputs.jsonl`.
