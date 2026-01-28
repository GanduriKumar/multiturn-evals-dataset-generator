# User Guide – Vertical-Agnostic Eval Dataset Generator

Welcome! 👋  
This guide is designed to help **anyone**, even complete beginners, understand and use the **Eval Dataset Generator**. No technical background is required. If you can point-and-click, you can use this tool. 🙌

This version of the tool is **generic**: it works for **any supported industry vertical**, such as commerce, banking, insurance, healthcare, etc.

---

## 🌟 What This Tool Does (In Simple Words)
Think of this tool as a **conversation generator** and **exam creator** for testing AI systems.

It helps you:
- Create **realistic user conversations** (Eval dataset) for a chosen vertical, like commerce or banking.
- Create **correct expected answers** (Golden dataset) that show how the AI *should* respond.
- Compare your AI’s answers against the expected answers and see where it passes or fails.

You choose:
1. **Which vertical** you care about (e.g., Commerce vs Banking).
2. **Which workflows** inside that vertical (e.g., Returns & Refunds, Lost Card).
3. **How users behave** (friendly, confused, tricky, etc.).
4. **What conditions apply** (e.g., item out of stock, policy not allowed, high risk).

The tool does the rest.

---

## 🧩 What You Will Need
Only two things:
- A web browser (Chrome, Edge, Firefox)
- The tool’s URL (shared by your team)

Optional (for scoring):
- AI model outputs file (provided by your AI/engineering team)

Optional (advanced users):
- Custom config/template files per vertical

---

## 🎯 What You Can Do With This Tool

### 1. Generate Evaluation Datasets
You can generate:
- **Eval dataset** → What the AI will see (just the user side of the conversation).
- **Golden dataset** → The ideal full conversation, including how the AI *should* respond and how we’ll score it.

### 2. Score Your AI’s Performance
If your AI or LLM has answered the eval dataset, you can:
- Upload its answers
- Let the tool compare them with the golden dataset
- Get a **scored results file** to see:
  - Which conversations passed or failed
  - Where the AI broke policy
  - How good it is at following the workflow

---

# 🖥️ How To Use The Web App

## Step 1: Open the Web App
Open the tool’s URL in your browser.

You’ll see a simple page with:
- A dropdown for **Vertical**
- Controls for workflows, behaviours, and axes (which change based on the vertical you pick)
- File upload options
- Buttons to **Generate Dataset** and **Score Run**

---

## Step 2: Select a Vertical
At the top, choose which **industry vertical** you want to work with.

Examples:
- `Commerce`
- `Banking`
- `Insurance`
- `Healthcare`

When you select a vertical, the app will **automatically load** the workflows, user behaviours, and axes that belong to that vertical.

> 💡 Tip: Start with a vertical you know best (for you, probably *Commerce* to begin with).

---

## Step 3: Choose Workflows (What You Want To Test)
Workflows are the **business processes** you care about.

Examples:
- In **Commerce**:
  - Product Discovery & Search
  - Checkout & Payments
  - Returns, Refunds & Exchanges
  - Trust, Safety & Fraud
- In **Banking**:
  - Lost or Stolen Card
  - Loan Eligibility Check
  - Transaction Dispute

The app will show you a list of workflows for the selected vertical.  
You can pick **one or more**.

---

## Step 4: Choose User Behaviours
User behaviours describe the **style and mood** of the user. These are defined **per vertical**, but usually cover things like:

- **Happy Path** – user is clear and cooperative
- **Constraint-heavy** – user has strict demands (budget, policy, etc.)
- **Ambiguous** – user is unclear or vague
- **Multi-turn** – user gives information bit by bit
- **Corrections** – user changes their mind or corrects earlier info
- **Adversarial / Trap** – user tries to trick the system or bypass policy

You can toggle **any combination** of these behaviours.  
The more you enable, the more complex the conversations become.

> 💡 Tip: Start with *Happy Path* only, then add others later.

---

## Step 5: Choose Scenario Conditions (Axes)
Axes represent **scenario conditions** that affect the conversation. They are **vertical-specific**.

Examples for **Commerce**:
- **Price sensitivity** → HIGH / MED / LOW
- **Brand preference** → NONE / MED / HIGH
- **Availability** → AVAILABLE / LOW STOCK / OUT OF STOCK
- **Policy boundary** → ALLOWED / PARTIAL / NOT ALLOWED

Examples for **Banking** (if configured):
- **Risk level** → LOW / MED / HIGH
- **KYC status** → COMPLETE / PARTIAL

The app will show dropdowns for each axis for your vertical.  
Choose one option for each axis.

---

## Step 6: Set Number of Conversations
Enter how many conversations you want the tool to generate **per combination**.

For example, if you set:
- 1 vertical (Commerce)
- 2 workflows
- Some behaviours
- A set of axes
- `num_samples_per_combo = 10`

The tool will generate **10 conversations for each workflow/behaviour/axes combination**.

For getting started, try `5` or `10`.

---

## Step 7: (Optional) Upload Custom Schema Files
Most users can **ignore this section**.

Advanced users can upload:
- Custom workflow definitions
- Custom behaviours
- Custom axes

If you’re not sure what these are, you don’t need them. The default configuration is enough to start.

---

## Step 8: Click **Generate Dataset**
When you click the button, the tool will:
- Build all the conversations for your chosen vertical + workflows + behaviours + axes
- Package them into a ZIP file containing:
  - `eval_dataset.jsonl`
  - `golden_dataset.jsonl`
  - `manifest.json`

Your browser will download the ZIP automatically.

🎉 **You’ve just generated your evaluation datasets!**

---

# 📊 How To Score Your AI’s Responses
After your AI/LLM (or agent) has answered the **eval dataset**, your engineering team can give you a file called `model_outputs.jsonl`.

You can then use the **Scoring** part of the tool.

You’ll need:
- `golden_dataset.jsonl` (from your ZIP)
- `model_outputs.jsonl` (from the AI run)
- A name for your model (e.g., "my-model-v1")

---

## Step 1: Go to the Scoring Section
Find the section or tab labeled something like **"Score Run"**.

It will ask for:
1. Golden dataset file (`golden_dataset.jsonl`)
2. Model outputs file (`model_outputs.jsonl`)
3. Model name / ID

---

## Step 2: Upload Files + Enter Model Name
- Upload `golden_dataset.jsonl`
- Upload `model_outputs.jsonl`
- Type the model name/ID (any string to identify the model)

---

## Step 3: Click **Score Run**
The tool will:
- Compare each model answer with the golden expected answer
- Check:
  - Did the model perform the right actions?
  - Did it give the right facts (status, amount, ETA, etc.)?
  - Did it respect policy (no disallowed promises)?

You’ll get a new file:
- `scored_results.jsonl`

This file tells you, for each conversation:
- ✔ How well the model followed the workflow
- ❌ Where it made mistakes
- ❗ Whether it broke any policy rule
- 👍 An overall score

Your data science or QA team can also turn this into dashboards.

---

# 🗂️ What The Files Mean

### `eval_dataset.jsonl`
- One line per conversation example (user side only).
- Used as **input** to your AI.

### `golden_dataset.jsonl`
- Full ideal conversation (user + expected agent responses).
- Also includes:
  - `expected_actions`
  - `key_facts`
  - `scoring_rules`

### `model_outputs.jsonl`
- Actual responses from your AI or agent.
- Produced **outside** this tool.

### `scored_results.jsonl`
- Per-conversation scores from comparing model outputs to golden.

### `manifest.json`
- Metadata about how the dataset was generated (vertical, workflows, behaviours, axes, counts, etc.).

---

# 💡 Tips For Beginners

- Start with:
  - One **vertical** (e.g., Commerce)
  - One **workflow** (e.g., Returns & Refunds)
  - Just **Happy Path** behaviour
  - Simple axes (e.g., ALLOWED policy, AVAILABLE stock)
- Generate only **5** conversations at first.
- Open the JSONL files in VSCode or another text editor to get a feel.
- Work with your AI/engineering partner to run the eval dataset.
- Use scoring to see where the model is weak.
- Slowly add more behaviours and harder axes (like Adversarial + NOT ALLOWED policy) to stress-test your AI.

---

# 🧯 Troubleshooting

### ❓ I don't understand JSONL. What is it?
It’s just a text file where **each line is a separate JSON object**.
- You can open it in:
  - VSCode
  - Notepad
  - Any text editor

### ❓ The AI is failing everything!
Try making scenarios easier:
- Use **Happy Path** behaviour only.
- Choose policy axes like **ALLOWED** instead of NOT ALLOWED.
- Use **AVAILABLE** instead of OUT OF STOCK.

### ❓ Can I use my own conversation templates and rules?
Yes. The app supports **custom schema/config uploads** per vertical.  
This is an advanced feature – ask your engineering partner to help configure it.

### ❓ The download isn't working.
Check:
- Browser pop-up or download permissions
- Network/firewall rules
- That the request didn’t fail with an error (ask engineering to check logs if needed)

---

# 🎉 You’re Ready!
With this guide, you can now:
- ✔ generate datasets for different verticals   
- ✔ simulate real-world business scenarios   
- ✔ score your AI’s performance   
- ✔ help your org deploy safer, smarter AI

If you ever feel stuck, revisit this guide or reach out to your engineering/data science partner.

Happy testing! 🚀
