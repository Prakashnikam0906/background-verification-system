# Background Verification System

A production-grade Background Verification System built with **Python + FastAPI** that orchestrates **16 verification agents** in parallel, generates intelligent smart reports, and supports selective re-execution based on user feedback.

---

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Project Structure](#project-structure)
3. [Tech Stack](#tech-stack)
4. [Setup & Run](#setup--run)
5. [API Documentation](#api-documentation)
6. [Execution Flow](#execution-flow)
7. [State Management](#state-management)
8. [Selective Re-execution Logic](#selective-re-execution-logic)
9. [Smart Report Structure](#smart-report-structure)
10. [Execution States](#execution-states)
11. [Testing](#testing)

---

## System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    FastAPI REST Layer                      │
│         POST /verify  ·  POST /feedback                   │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│                     Orchestrator                          │
│   asyncio.gather([agent1, agent2, ... agent16])           │
│   Selective re-execution via keyword routing              │
└──────────┬──────────────────────────┬────────────────────┘
           │                          │
  ┌────────▼────────┐      ┌──────────▼──────────┐
  │  Agent Registry  │      │   Feedback Handler   │
  │  16 agents       │      │  keyword → agents    │
  └────────┬────────┘      └─────────────────────┘
           │
  ┌────────▼────────┐
  │  State Manager  │  ← in-memory, per verification
  │  audit trail    │
  │  version history│
  └────────┬────────┘
           │
  ┌────────▼────────┐
  │  Report Engine  │
  │  risk scores    │
  │  CACHED/FRESH   │
  └─────────────────┘
```

---

## Project Structure

```
bgv-system/
├── app/
│   ├── agents/
│   │   ├── base_agent.py         # Abstract base — mock + real API
│   │   ├── identity_agents.py    # 5 identity agents
│   │   ├── criminal_agents.py    # 5 criminal agents
│   │   ├── financial_agents.py   # 6 financial agents
│   │   └── registry.py           # Central registry + feedback routing
│   ├── orchestrator/
│   │   └── orchestrator.py       # Parallel execution engine
│   ├── state/
│   │   └── state_manager.py      # Execution state + audit trail
│   ├── reports/
│   │   └── report_engine.py      # Smart report generator
│   ├── feedback/
│   │   └── feedback_handler.py   # Feedback parser
│   ├── api/
│   │   ├── schemas.py            # Pydantic request/response models
│   │   └── routes/
│   │       └── verification.py   # API endpoints
│   ├── config/
│   │   └── settings.py           # App configuration
│   ├── utils/
│   │   ├── enums.py              # Enums and constants
│   │   └── helpers.py            # Utility functions
│   └── main.py                   # FastAPI app
├── tests/
│   └── test_full_flow.py         # End-to-end test
├── run.py                        # Entry point
├── requirements.txt
├── .env.example
└── README.md
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| API Framework | FastAPI |
| Async Runtime | asyncio (Python built-in) |
| AI Integration | OpenAI SDK (UltraSafe compatible) |
| Data Validation | Pydantic v2 |
| Server | Uvicorn |
| Language | Python 3.10+ |

---

## Setup & Run

### 1. Clone and install

```bash
git clone <your-repo-url>
cd bgv-system
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
ULTRASAFE_API_KEY=akmateiy-d219a1f5-f2678c0d-087ea8bb
ULTRASAFE_BASE_URL=https://api.ultrasafe.ai/v1
ULTRASAFE_MODEL=gpt-4o
USE_REAL_API=true    # set false for mock simulation
```

### 3. Run the server

```bash
python run.py
```

Server starts at: `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`

---

## API Documentation

### `POST /api/v1/verify`
Start a full background verification. All 16 agents run in parallel.

**Request:**
```json
{
  "subjectData": {
    "firstName": "Prakash",
    "lastName": "Kumar",
    "dateOfBirth": "1990-05-15",
    "address": "123 Main Street",
    "city": "Austin",
    "state": "TX",
    "zip": "78701",
    "govtIdType": "Passport",
    "govtIdNumber": "P1234567"
  }
}
```

**Response:** Complete smart report with `verificationId`

---

### `POST /api/v1/verify/{id}/feedback`
Submit feedback for selective re-execution.

**Request:**
```json
{
  "feedback": "The address information is outdated.",
  "subjectData": {
    "address": "456 Oak Avenue",
    "city": "Dallas",
    ...
  }
}
```

**Response:** Updated report with FRESH/CACHED indicators per agent.

---

### `GET /api/v1/verify/{id}/report`
Get the latest smart report.

### `GET /api/v1/verify/{id}/state`
Get raw execution state with full audit trail.

### `POST /api/v1/verify/{id}/feedback/preview`
Dry-run — see which agents would re-run for a feedback string.

### `GET /api/v1/verifications`
List all verification runs.

---

## Execution Flow

### Initial Verification
```
POST /verify
  └── Orchestrator.run_all()
       └── asyncio.gather([16 agents simultaneously])
            ├── Each agent executes independently
            ├── state_manager.mark_completed() as each finishes
            └── Overall status recalculated after each agent
  └── report_engine.generate(final_state)
  └── Return complete smart report
```

### Selective Re-execution
```
POST /verify/{id}/feedback  { feedback: "address is outdated" }
  └── feedback_handler.parse_feedback()
       └── keyword "address" → [AddressVerificationAgent, AddressHistoryAgent]
  └── state_manager.snapshot_and_bump()     ← version history saved
  └── state_manager.mark_cached(14 agents)  ← preserve their results
  └── orchestrator re-runs 2 agents in parallel
  └── report_engine.generate() → FRESH/CACHED labels in report
```

---

## State Management

Full state stored per verification:

```json
{
  "verificationId": "uuid",
  "subjectId": "SUB-PRAKASH-KUMAR",
  "version": 2,
  "overallStatus": "COMPLETED",
  "agentStates": {
    "AddressVerificationAgent": {
      "status": "FRESH",
      "result": { "status": "PASS", "riskScore": 8 },
      "executionType": "RE_EXECUTED",
      "dataHash": "abc123...",
      "completedAt": "2026-06-19T..."
    },
    "FederalCriminalCheckAgent": {
      "status": "CACHED",
      "result": { "status": "PASS", "riskScore": 2 },
      "executionType": "INITIAL"
    }
  },
  "auditTrail": [ ... ],
  "history": [ { "version": 1, "feedback": "...", "agentStates": {...} } ]
}
```

---

## Selective Re-execution Logic

Keyword to agent mapping (in `app/agents/registry.py`):

| Feedback keyword | Agents re-run |
|-----------------|---------------|
| "address" | AddressVerificationAgent, AddressHistoryAgent |
| "criminal" | All 5 criminal agents |
| "credit" | CreditVerificationAgent |
| "sanctions" | SanctionsScreeningAgent |
| "identity" | All 5 identity agents |
| "financial" | All 6 financial agents |
| ... | ... |

---

## Smart Report Structure

```
SmartReport
├── reportId
├── overallRiskScore        (weighted: criminal×2.0, financial×1.5, identity×1.0)
├── overallRiskLevel        (LOW | MEDIUM | HIGH | CRITICAL)
├── executiveSummary
│   ├── recommendation      (APPROVED | CAUTION | DO NOT PROCEED)
│   ├── passed/failed/warnings count
│   └── categorySummary
├── categoryReports
│   ├── identity  { status, riskScore, agentResults[] }
│   ├── criminal  { status, riskScore, agentResults[] }
│   └── financial { status, riskScore, agentResults[] }
├── flagsAndAlerts          (sorted by severity: CRITICAL → LOW)
├── auditTrail              (every event timestamped)
└── executionHistory        (snapshots of prior versions)
```

---

## Execution States

| State | Meaning |
|-------|---------|
| `RUNNING` | Agent currently executing |
| `COMPLETED` | Finished on initial run |
| `FRESH` | Re-executed after feedback |
| `CACHED` | Preserved from prior run |
| `FAILED` | Execution error |

**Overall states:** `RUNNING` → `COMPLETED` | `PARTIAL` | `FAILED`

---

## Testing

```bash
# Run full end-to-end test
python tests/test_full_flow.py
```

Demonstrates all 8 scenarios:
1. 16 agents in parallel
2. Smart report generation
3. Feedback preview (dry-run)
4. Selective re-execution
5. CACHED vs FRESH indicators
6. Updated report
7. Audit trail (23 events)
8. Version history with snapshots

---

## UltraSafe API Integration

The system uses the **OpenAI-compatible client** to call UltraSafe:

```python
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key=ULTRASAFE_API_KEY,
    base_url=ULTRASAFE_BASE_URL,  # https://api.ultrasafe.ai/v1
)

response = await client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": agent_system_prompt},
        {"role": "user",   "content": subject_data_prompt},
    ]
)
```

Each agent has a specialized system prompt for its verification domain.
Set `USE_REAL_API=true` in `.env` to switch from mock to real API.
