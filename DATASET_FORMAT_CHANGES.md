# Dataset Format Changes Required

## Overview

This document outlines the required changes to support **TWO** output formats:
1. **Dataset Format** - Full conversation data with all turns (eval_dataset.json)
2. **Golden Format** - Evaluation expectations with specific turn indices (golden_dataset.json)

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

### Current Format (JSONL - Line Delimited)

```json
{
  "conversation_id": "commerce-refund-0001",
  "scenario_id": "commerce-refund-0001",
  "vertical": "commerce",
  "workflow": "refund",
  "behaviours": ["HappyPath"],
  "axes": {"price_sensitivity": "low"},
  "turns": [
    {
      "turn_index": 0,
      "speaker": "user",
      "role": "customer",
      "text": "I need help..."
    }
  ]
}
```

## Key Differences & Required Changes

### 1. **Root Structure** (NEW)
- **Current**: JSONL format (one conversation per line)
- **Target**: Single JSON object with top-level metadata and conversations array
- **Changes Needed**:
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

**Changes Needed**:
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

**Changes Needed**:
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

**Changes Needed**:
- Extract behavior name from workflow mapping
- Build axes string from axis values
- Generate 8-10 character hash from combination
- Use URL-safe formatting (hyphens for spaces)

### 6. **Export Format** (NEW)
**Current**: Single file per request (JSONL)
**Target**: Single JSON file containing:
- Root metadata
- All conversations in array

**Changes Needed**:
- Change `/generate-dataset` endpoint to return single JSON instead of multiple files
- Aggregate conversation plans into single structure
- Compress to ZIP if needed for large datasets

---

## Implementation Checklist

### Backend Changes (`app/models.py`)
- [ ] Add `domain_label` field to ConversationPlan
- [ ] Add `policy_excerpt` field to ConversationPlan
- [ ] Add `facts_bullets` field to ConversationPlan
- [ ] Add `behavior_label` field to ConversationPlan
- [ ] Update turn model to use `role` instead of `speaker`
- [ ] Remove `turn_index` from turn model
- [ ] Add dataset metadata model with `dataset_id`, `version`, `metadata`, `conversations`

### Backend Changes (`app/generation.py`)
- [ ] Update conversation_id generation to include behavior and axes in URL format
- [ ] Add behavior-label lookup from config
- [ ] Add policy excerpt lookup from config
- [ ] Add facts generation from template (using axes values)
- [ ] Generate hash for conversation_id tail

### Backend Changes (`app/dataset_builder.py`)
- [ ] Update turn structure (remove `turn_index`, rename `speaker` to `role`)
- [ ] Move conversation metadata into nested `metadata` object
- [ ] Update payload structure to match target format

### Backend Changes (`app/main.py` - `/generate-dataset` endpoint)
- [ ] Update response to return single JSON document instead of JSONL
- [ ] Include root-level dataset metadata
- [ ] Wrap conversations array
- [ ] Generate dataset_id and version

### Configuration Files
- [ ] Add `policy_excerpt` to each workflow in YAML files
- [ ] Add `domain_label` mapping (commerce → "Coverage/Promotions/Pricing", etc.)
- [ ] Add `facts_template` to behaviors for dynamic bullet generation
- [ ] Map workflows to behavior labels

### Tests
- [ ] Update test expectations for new format
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

---

## Summary of Changes by File

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
    format: str = Form("both"),  # "dataset", "golden", or "both"
    # ... other parameters
) -> StreamingResponse:
    # ... existing code ...
    
    # Generate both formats
    dataset_json = build_dataset_json(plans, template_engine, request)
    golden_json = build_golden_dataset(plans, template_engine, vertical_config)
    
    # Create ZIP with both files
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        if format in ("dataset", "both"):
            dataset_bytes = json.dumps(dataset_json, ensure_ascii=False, indent=2).encode("utf-8")
            zip_file.writestr(f"{dataset_id}.dataset.json", dataset_bytes)
        
        if format in ("golden", "both"):
            golden_bytes = json.dumps(golden_json.dict(), ensure_ascii=False, indent=2).encode("utf-8")
            zip_file.writestr(f"{dataset_id}.golden.json", golden_bytes)
    
    # ... return zip ...
```

---

## Summary of Changes by File

