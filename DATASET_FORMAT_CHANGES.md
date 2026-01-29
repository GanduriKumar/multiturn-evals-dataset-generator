# Dataset Format Changes Required

## Overview

This document outlines the required changes to support **two JSON output formats**. As of 2026‑01‑29, these changes are implemented and the generator emits:
1. **Dataset Format** – Full conversation data with all turns in `<dataset_id>.dataset.json`.
2. **Golden Format** – Evaluation expectations in `<dataset_id>.golden.json`.

> Legacy note: `/score-run` still accepts **JSONL** inputs (`golden_dataset.jsonl` and `model_outputs.jsonl`) with `expected_actions`, `key_facts`, and `scoring_rules`.

## Current vs. Target Format Analysis

### Target Format (from attached file: `coverage-promotions-pricing-combined-1.0.0.dataset.json`)

```json
{
  "dataset_id": "coverage-promotions-pricing-combined-1.0.0",
  "version": "1.0.0",
  "metadata": {
    "domain": "commerce",
    "difficulty": "mixed",
    "tags": ["combined", "Promotions & Pricing"]
  },
  "conversations": [
    {
      "conversation_id": "promotions-pricing.refund-exchange-cancellation.price_sensitivity=low,brand_bias=hard,availability=limited_stock,policy_boundary=within_policy.0bce40a674",
      "metadata": {
        "domain_label": "Promotions & Pricing",
        "behavior": "Refund/Exchange/Cancellation",
        "axes": {
          "price_sensitivity": "low",
          "brand_bias": "hard",
          "availability": "limited_stock",
          "policy_boundary": "within_policy"
        },
        "policy_excerpt": "# Promotions & Pricing Policy (Excerpt)\n\n- Coupon stacking not allowed unless explicitly stated.\n- Price match requires active public listing and identical SKU/spec.\n- Promo codes are single-use unless specified; expire at 23:59 local time.",
        "facts_bullets": "- Order was delivered 20 days ago; quantity 5.\n- Price is not the primary concern for the customer.\n- Customer prefers a specific brand and resists substitutions.\n- Inventory is limited; prompt action is required to secure items.\n- Request is within standard policy guidelines.",
        "short_description": "Refund/Exchange/Cancellation with axes {...}"
      },
      "turns": [
        {
          "role": "user",
          "text": "I need help with my recent order..."
        },
        {
          "role": "assistant",
          "text": "I'd be happy to help you with your order..."
        }
      ]
    }
  ]
}
```

### Current Format (JSON - Dataset)

```json
{
  "dataset_id": "commerce-combined-1.0.0",
  "version": "1.0.0",
  "metadata": {
    "domain": "commerce",
    "difficulty": "mixed",
    "tags": ["combined", "Promotions & Pricing"]
  },
  "conversations": [
    {
      "conversation_id": "promotions-pricing.refund-exchange-cancellation.price_sensitivity=low,brand_bias=hard,availability=limited_stock,policy_boundary=within_policy.0bce40a674",
      "metadata": {
        "domain_label": "Promotions & Pricing",
        "behavior": "Refund/Exchange/Cancellation",
        "axes": {
          "price_sensitivity": "low",
          "brand_bias": "hard",
          "availability": "limited_stock",
          "policy_boundary": "within_policy"
        },
        "policy_excerpt": "# Promotions & Pricing Policy (Excerpt)\n\n- Coupon stacking not allowed unless explicitly stated.",
        "facts_bullets": "- Order was delivered 20 days ago; quantity 5.",
        "short_description": "Refund/Exchange/Cancellation with axes {...}"
      },
      "turns": [
        {
          "role": "user",
          "text": "I need help with my recent order..."
        }
      ]
    }
  ]
}
```

## Key Differences & Required Changes

Status: All items below are **implemented** in `backend/app/generation.py`, `backend/app/dataset_builder.py`, and `backend/app/main.py`.

### 1. **Root Structure** (NEW)
- **Current**: Single JSON object with top-level metadata and `conversations` array
- **Target**: Single JSON object with top-level metadata and conversations array
- **Implemented**:
  - Add `dataset_id` field (e.g., `{vertical}-{behavior}-combined-{version}`)
  - Add `version` field (e.g., `1.0.0`)
  - Add `metadata` object with:
    - `domain`: vertical name
    - `difficulty`: "mixed", "easy", "hard" (derived from behaviors)
    - `tags`: Array of tags (e.g., ["combined", "Behavior Name"])
  - Wrap all conversations in `conversations` array

### 2. **Conversation Metadata** (ENHANCED)
**Current**:
```json
{
  "conversation_id": "...",
  "vertical": "...",
  "workflow": "...",
  "behaviours": [],
  "axes": {}
}
```

**Target**:
```json
{
  "conversation_id": "...",
  "metadata": {
    "domain_label": "Domain Name",
    "behavior": "Specific Behavior",
    "axes": { /* axis key-value pairs */ },
    "policy_excerpt": "# Policy Title\n\n- Bullet 1\n- Bullet 2",
    "facts_bullets": "- Fact 1\n- Fact 2\n- Fact 3",
    "short_description": "Behavior with axes {...}"
  }
}
```

**Implemented**:
- Move `vertical`, `workflow`, `behaviours`, `axes` into nested `metadata` object
- **Rename** `behaviours` → `behavior` (singular) in metadata
- **Add** `domain_label`: Human-readable domain name
- **Add** `policy_excerpt`: Policy text relevant to the behavior/workflow
- **Add** `facts_bullets`: Context facts about the scenario (customer situation, constraints, etc.)
- **Add** `short_description`: Summary of the conversation scenario
- **Update** `conversation_id` format: `{domain_label}.{behavior}.{axes_key=value,pairs}.{hash}`
  - Example: `promotions-pricing.refund-exchange-cancellation.price_sensitivity=low,brand_bias=hard,availability=limited_stock,policy_boundary=within_policy.0bce40a674`

### 3. **Turn Structure** (SIMPLIFIED)
**Current**:
```json
{
  "turn_index": 0,
  "speaker": "user",
  "role": "customer",
  "text": "..."
}
```

**Target**:
```json
{
  "role": "user",
  "text": "..."
}
```

**Implemented**:
- Remove `turn_index` field
- **Rename** `speaker` → `role` (use "user" or "assistant" values)
- Remove `speaker` field entirely
- Simplify to just `role` and `text`

### 4. **Policy & Context Data** (NEW)
**Add to configuration files**:
- `policy_excerpt`: Store in workflow YAML or behavior YAML
- `facts_bullets`: Template-based generation based on axes and scenario
- Example structure in YAML:
  ```yaml
  workflows:
    refund:
      label: "Refund/Exchange/Cancellation"
      policy_excerpt: |
        # Policy Title
        - Bullet points
      facts_template: |
        - Order was delivered {days_ago} days ago; quantity {quantity}.
        - Price sensitivity: {price_sensitivity}
  ```

### 5. **Conversation ID Format** (UPDATED)
**Current**: `{vertical}-{workflow}-{counter}`
- Example: `commerce-refund-0001`

**Target**: `{domain_label}.{behavior}.{axes_key=value,comma_separated}.{hash}`
- Example: `promotions-pricing.refund-exchange-cancellation.price_sensitivity=low,brand_bias=hard,availability=limited_stock,policy_boundary=within_policy.0bce40a674`

**Implemented**:
- Extract behavior name from workflow mapping
- Build axes string from axis values
- Generate 8-10 character hash from combination
- Use URL-safe formatting (hyphens for spaces)

### 6. **Export Format** (NEW)
**Current**: ZIP archive containing dataset, golden, and manifest JSON files.
**Target**: Single JSON file containing:
- Root metadata
- All conversations in array

**Implemented**:
- `/generate-dataset` returns a ZIP with `<dataset_id>.dataset.json`, `<dataset_id>.golden.json`, and `manifest.json`.
- Conversations are aggregated into a single JSON structure.

---

## Implementation Checklist

### Backend Changes (`app/models.py`)
- [x] Add `domain_label` field to ConversationPlan
- [x] Add `policy_excerpt` field to ConversationPlan
- [x] Add `facts_bullets` field to ConversationPlan
- [x] Add `behavior_label` field to ConversationPlan
- [x] Update turn output to use `role` instead of `speaker`
- [x] Remove `turn_index` from dataset output turns
- [ ] Add dataset metadata model with `dataset_id`, `version`, `metadata`, `conversations`

### Backend Changes (`app/generation.py`)
- [x] Update conversation_id generation to include behavior and axes in URL format
- [x] Add behavior-label lookup from config
- [x] Add policy excerpt lookup from config
- [x] Add facts generation from template (using axes values)
- [x] Generate hash for conversation_id tail

### Backend Changes (`app/dataset_builder.py`)
- [x] Update turn structure (remove `turn_index`, rename `speaker` to `role`)
- [x] Move conversation metadata into nested `metadata` object
- [x] Update payload structure to match target format

### Backend Changes (`app/main.py` - `/generate-dataset` endpoint)
- [x] Update response to return JSON files inside a ZIP archive
- [x] Include root-level dataset metadata
- [x] Wrap conversations array
- [x] Generate dataset_id and version

### Configuration Files
- [ ] Add `policy_excerpt` to each workflow in YAML files (partially done for commerce)
- [ ] Add `domain_label` mapping for all workflows and verticals (partially done)
- [ ] Add `facts_template` to workflows for dynamic bullet generation (partially done)
- [ ] Map workflows to behavior labels across all verticals (partially done)

### Tests
- [ ] Update test expectations for new format (current tests still assert JSONL shape)
- [ ] Add tests for conversation_id generation
- [ ] Add tests for metadata structure

---

## Example Mapping for Commerce Vertical

### Workflow → Behavior Mapping
```yaml
workflows:
  refund:
    label: "Refund/Exchange/Cancellation"
    domain_label: "Promotions & Pricing"
  price_match:
    label: "Price match/Discount/Coupon stacking"
    domain_label: "Promotions & Pricing"
  post_purchase:
    label: "Post-purchase modifications"
    domain_label: "Promotions & Pricing"
```

### Policy Excerpt Example
```yaml
policy_excerpt: |
  # Promotions & Pricing Policy (Excerpt)
  
  - Coupon stacking not allowed unless explicitly stated.
  - Price match requires active public listing and identical SKU/spec.
  - Promo codes are single-use unless specified; expire at 23:59 local time.
```

### Facts Template Example
```yaml
facts_template: |
  - Order was delivered {delivery_days} days ago; quantity {quantity}.
  - Price is{' not' if price_sensitivity == 'low' else ''} the primary concern for the customer.
  - Customer{'prefers a specific brand and resists substitutions' if brand_bias == 'hard' else ' has no brand preference' if brand_bias == 'none' else ' has soft brand preference'}.
  - Inventory is {availability.replace('_', ' ')}.
  - Request is {policy_boundary.replace('_', ' ')}.
```
- `backend/app/models.py`: Conversation metadata fields added (`domain_label`, `policy_excerpt`, `facts_bullets`, `behavior_label`).
- `backend/app/generation.py`: Conversation ID format, policy excerpts, and facts generation implemented.
- `backend/app/dataset_builder.py`: Dataset JSON structure with nested metadata and simplified turns (`role`, `text`).
- `backend/app/main.py`: ZIP output with `<dataset_id>.dataset.json`, `<dataset_id>.golden.json`, and `manifest.json`.
- `config/verticals/*`: Partial coverage for `policy_excerpt`, `facts_template`, and `domain_label` (complete for commerce only).

Known gaps:
- Tests in `backend/tests/` still assert JSONL shapes and need updates.
- `/score-run` uses legacy JSONL scoring inputs and does not consume the generated golden JSON format.

| File | Changes |
|------|---------|
| `models.py` | Add domain_label, policy_excerpt, facts_bullets, behavior_label; update turn model; add golden dataset models |
| `generation.py` | Update conversation_id format; add policy/facts lookup and generation |
| `dataset_builder.py` | Restructure turns; move metadata into nested object; add golden dataset builder |
| `main.py` | Update endpoint to return single JSON with root metadata; support both dataset and golden formats |
| `config/*.yaml` | Add policy_excerpt, domain_label, facts_template, expected_responses |
| Tests | Update expectations for new format |

---

## Golden Dataset Format (NEW)

### Target Format (from `coverage-promotions-pricing-combined-1.0.0.golden.json`)

```json
{
  "dataset_id": "coverage-promotions-pricing-combined-1.0.0",
  "version": "1.0.0",
  "entries": [
    {
      "conversation_id": "promotions-pricing.refund-exchange-cancellation.price_sensitivity=low,brand_bias=hard,availability=limited_stock,policy_boundary=within_policy.0bce40a674",
      "turns": [
        {
          "turn_index": 7,
          "expected": {
            "variants": [
              "I will verify your order and, per policy, process a refund or exchange. If stock is unavailable, I can issue a refund or offer store credit."
            ]
          }
        }
      ],
      "final_outcome": {
        "decision": "ALLOW"
      },
      "constraints": {
        "respect_policy": true
      }
    }
  ]
}
```

### Golden Dataset Structure Breakdown

**Root Level**:
- `dataset_id`: Same as dataset file (e.g., `"coverage-promotions-pricing-combined-1.0.0"`)
- `version`: Same as dataset file (e.g., `"1.0.0"`)
- `entries`: Array of evaluation entries (NOT `conversations`)

**Entry Structure**:
- `conversation_id`: Matches conversation_id from dataset file
- `turns`: Array of turn expectations (NOT full turns, only specific indices to evaluate)
- `final_outcome`: Expected outcome decision
- `constraints`: Policy constraints for evaluation

**Turn Expectation Structure**:
- `turn_index`: Which turn number to evaluate (e.g., 7 for the last assistant turn)
- `expected`: Object containing expected response variants
  - `variants`: Array of acceptable response strings

**Final Outcome**:
- `decision`: "ALLOW" or "DENY" (expected resolution)

**Constraints**:
- `respect_policy`: boolean indicating if policy must be respected

### Key Differences: Dataset vs Golden

| Aspect | Dataset Format | Golden Format |
|--------|---------------|---------------|
| Root array name | `conversations` | `entries` |
| Content type | Full conversation | Evaluation expectations |
| Turns structure | All turns with role+text | Specific turn indices with expected variants |
| Metadata | Full conversation metadata | Only conversation_id |
| Additional fields | None | `final_outcome`, `constraints` |
| Purpose | Full conversation data | Evaluation ground truth |

### Golden Dataset Requirements

1. **Turn Index Selection**: Typically evaluates the **last assistant turn** (e.g., turn_index 7 for 4-turn conversations)

2. **Expected Variants**: Multiple acceptable response patterns for the same scenario
   - Example: For refund scenarios, all variants mention verification, policy compliance, and alternatives

3. **Final Outcome Decision**:
   - `ALLOW`: Policy permits the action
   - `DENY`: Policy blocks the action
   - Based on `policy_boundary` axis value

4. **Constraints**:
   - `respect_policy`: true for all commerce scenarios
   - Can include other constraints based on domain

### Configuration Additions for Golden Dataset

Add to workflow YAML files:

```yaml
workflows:
  refund:
    label: "Refund/Exchange/Cancellation"
    domain_label: "Promotions & Pricing"
    policy_excerpt: |
      # Policy text here
    expected_responses:
      within_policy:
        variants:
          - "I will verify your order and, per policy, process a refund or exchange. If stock is unavailable, I can issue a refund or offer store credit."
          - "Let me verify your order details. Per our policy, I can process this refund/exchange for you. If the item is out of stock, I can offer a full refund or store credit."
        decision: "ALLOW"
      near_edge_allowed:
        variants:
          - "I will verify your order and, per policy, process a refund or exchange. If stock is unavailable, I can issue a refund or offer store credit."
        decision: "ALLOW"
      outside_policy:
        variants:
          - "I understand your request, but per our policy this falls outside the allowable timeframe. I can escalate this to management if needed."
        decision: "DENY"
```

### Implementation Changes for Golden Dataset

**Backend Changes (`app/models.py`):**
```python
class GoldenTurnExpectation(BaseModel):
    turn_index: int
    expected: Dict[str, List[str]]  # {"variants": ["response1", "response2"]}

class GoldenEntry(BaseModel):
    conversation_id: str
    turns: List[GoldenTurnExpectation]
    final_outcome: Dict[str, str]  # {"decision": "ALLOW"}
    constraints: Dict[str, Any]  # {"respect_policy": true}

class GoldenDataset(BaseModel):
    dataset_id: str
    version: str
    entries: List[GoldenEntry]
```

**Backend Changes (`app/dataset_builder.py`):**
```python
def build_golden_dataset(
    plans: Sequence[ConversationPlan],
    template_engine: TemplateEngine,
    config: Dict[str, Any],
) -> GoldenDataset:
    """Build golden dataset with evaluation expectations."""
    entries = []
    
    for plan in plans:
        # Determine which turn to evaluate (typically last assistant turn)
        num_turns = len(plan.turn_plan)
        eval_turn_index = num_turns - 1  # Last turn
        
        # Get expected response variants based on policy_boundary
        policy_boundary = plan.axes.get("policy_boundary", "within_policy")
        expected_responses = _get_expected_responses(
            plan.workflow, 
            policy_boundary, 
            config
        )
        
        # Determine outcome based on policy_boundary
        decision = "DENY" if "outside" in policy_boundary else "ALLOW"
        
        entry = GoldenEntry(
            conversation_id=plan.scenario_id,
            turns=[
                GoldenTurnExpectation(
                    turn_index=eval_turn_index,
                    expected={"variants": expected_responses}
                )
            ],
            final_outcome={"decision": decision},
            constraints={"respect_policy": True}
        )
        entries.append(entry)
    
    return GoldenDataset(
        dataset_id=f"{plans[0].vertical.value}-combined-1.0.0",
        version="1.0.0",
        entries=entries
    )
```

**Backend Changes (`app/main.py`):**
```python
@app.post("/generate-dataset")
async def generate_dataset(
    config: str = Form(...),
  domain_schema: UploadFile | None = File(None),
  behaviour_schema: UploadFile | None = File(None),
  axes_schema: UploadFile | None = File(None),
) -> StreamingResponse:
  # ... existing code ...

  dataset_json = {
    "dataset_id": dataset_id,
    "version": "1.0.0",
    "metadata": {"domain": request.vertical.value, "difficulty": "mixed", "tags": ["combined"]},
    "conversations": eval_entries,
  }

  zip_buffer = io.BytesIO()
  with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
    zip_file.writestr(f"{dataset_id}.dataset.json", json.dumps(dataset_json, ensure_ascii=False, indent=2))
    zip_file.writestr(f"{dataset_id}.golden.json", json.dumps(golden_dataset_obj.model_dump(), ensure_ascii=False, indent=2))
    zip_file.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
  # ... return ZIP ...
```

End of document.





















