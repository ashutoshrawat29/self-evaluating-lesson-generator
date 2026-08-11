# Self-Evaluating Lesson Generator

An agentic educational content generation system that generates beginner-friendly lessons, evaluates them against a strict rubric, automatically regenerates failed lessons, and persists failure/success information as memory for future runs.

The system is built using **Python, LangGraph, Gemini API, FastAPI, Streamlit, SQLite, and Pydantic**.

---

## 1. Project Overview

The application accepts a topic from the user and generates a complete beginner-friendly lesson.

Instead of blindly returning the first LLM-generated response, the system follows an evaluation loop:

```text
User
  |
  v
Streamlit Frontend
  |
  | HTTP POST
  v
FastAPI
  |
  v
LangGraph Workflow
  |
  +--> Load Memory
  |
  +--> Generate Lesson -----> Gemini
  |
  +--> Deterministic Pre-checks
  |
  +--> Evaluate Lesson -----> Gemini
  |
  +---- PASS ----------------------+
  |                                |
  |                                v
  |                             Finalize
  |                                |
  |                                v
  |                               END
  |
  +---- FAIL
          |
          v
      Log Failure
          |
          v
        SQLite
          |
          v
      Regenerate -------> Gemini
          |
          v
      Pre-check
          |
          v
      Evaluate
          |
          +---- PASS --> Finalize --> END
          |
          +---- FAIL --> Retry if limit remains
```

The system uses bounded retries to prevent infinite regeneration loops.

---

# 2. Main Features

* Beginner-friendly lesson generation
* Gemini LLM integration
* LangGraph-based workflow orchestration
* Independent LLM evaluator
* Deterministic pre-checks
* Automatic regeneration after evaluation failure
* Bounded retry mechanism
* Persistent SQLite memory
* Failure/rejection logging
* Successful-fix memory
* FastAPI REST API
* Interactive Streamlit frontend
* Swagger/OpenAPI documentation
* Deliberate failure mode for demonstrating the self-evaluation loop

---

# 3. Architecture

The application is divided into several layers.

```text
                    +----------------+
                    |    User        |
                    +-------+--------+
                            |
                            v
                    +---------------+
                    |   Streamlit   |
                    |   Frontend    |
                    +-------+-------+
                            |
                       HTTP POST
                            |
                            v
                    +---------------+
                    |    FastAPI    |
                    |     API       |
                    +-------+-------+
                            |
                            v
                    +---------------+
                    |   LangGraph   |
                    |  Orchestrator |
                    +-------+-------+
                            |
              +-------------+-------------+
              |             |             |
              v             v             v
         Generator      Evaluator    Regenerator
              |             |             |
              +-------------+-------------+
                            |
                            v
                       Gemini API
                            |
                            v
                         SQLite
                         Memory
```

---

# 4. Workflow

## Step 1 — User enters a topic

Example:

```text
Introduction to RAG
```

The Streamlit frontend sends:

```http
POST /api/v1/lessons/generate
```

with:

```json
{
  "topic": "Introduction to RAG"
}
```

---

## Step 2 — FastAPI validates the request

FastAPI validates the request using Pydantic.

It checks:

* Topic exists
* Topic is a string
* Minimum length
* Maximum length

If validation succeeds, FastAPI calls the LangGraph workflow.

---

## Step 3 — LangGraph initializes state

The workflow creates a `LessonState` containing:

```text
topic
lesson
evaluation
rejection_log
retry_count
max_retries
memory
precheck_results
status
```

This state is passed between LangGraph nodes.

---

## Step 4 — Load Memory

The workflow queries SQLite for previous failures and successful fixes for the requested topic.

Example:

```text
Previous failure:
- Embedding was not explained.

Required change:
- Explain embedding simply.

Previous successful correction:
- Added a simple embedding explanation.
```

This information is passed to the generator.

---

## Step 5 — Generate Lesson

The Generator sends the topic and previous memory to Gemini.

Gemini produces a complete beginner-friendly lesson.

The generated lesson is stored in the LangGraph state.

---

## Step 6 — Deterministic Pre-check

Before using the LLM evaluator, simple Python checks are performed.

Examples:

* Lesson is not empty
* Lesson has reasonable length
* "What" is covered
* "Why" is covered
* "How" is covered
* At least one example exists

These checks provide a cheap first layer of validation.

---

## Step 7 — Evaluate Lesson

The Evaluator sends the lesson and rubric to Gemini.

The evaluator returns structured output.

Example:

```json
{
  "overall_pass": false,
  "checks": [
    {
      "criterion": "accuracy",
      "passed": true,
      "reason": "The technical explanation is accurate."
    },
    {
      "criterion": "beginner_friendly",
      "passed": false,
      "reason": "Some technical concepts are not explained."
    }
  ],
  "summary": "The lesson needs revision."
}
```

The evaluator follows a strict pass/fail approach.

If any required criterion fails, the lesson fails evaluation.

---

# 8. Conditional Routing

LangGraph decides what happens next.

If:

```text
overall_pass = true
```

the workflow goes:

```text
Evaluate
   |
   v
Finalize
   |
   v
END
```

If:

```text
overall_pass = false
```

and retries are available:

```text
Evaluate
   |
   v
Log Failure
   |
   v
Regenerate
   |
   v
Pre-check
   |
   v
Evaluate
```

This creates the self-evaluation loop.

---

# 9. Failure Logging

When a lesson fails, the system stores the failure in SQLite.

The stored information includes:

* Topic
* Attempt number
* Failed criteria
* Failure reasons
* Required changes
* Timestamp

Example:

```text
Topic:
Introduction to RAG

Attempt:
1

Failed:
beginner_friendly

Reason:
Embedding was not explained.

Required change:
Explain embedding simply.
```

---

# 10. Regeneration

The Regenerator receives:

```text
Original lesson
+
Evaluator feedback
+
Previous memory
```

It sends this information to Gemini and asks Gemini to rewrite the complete lesson while fixing the identified problems.

The retry counter is incremented.

---

# 11. Bounded Retries

The workflow prevents infinite regeneration.

Example:

```text
MAX_RETRIES=2
```

The workflow can therefore perform a limited number of corrections.

If the lesson continues to fail after the retry limit, the workflow terminates with:

```text
FAILED_AFTER_MAX_RETRIES
```

This protects the system from infinite loops and unnecessary LLM/API usage.

---

# 12. Persistent Memory

SQLite is used as persistent memory.

Two tables are created:

```text
failures
successful_fixes
```

### failures

Stores lessons that failed evaluation.

### successful_fixes

Stores corrections that successfully resulted in a passing lesson.

This allows future runs to use previous feedback.

Example:

```text
Run 1
  |
  v
Lesson fails
  |
  v
Failure stored
  |
  v
Lesson regenerated
  |
  v
Lesson passes
  |
  v
Successful correction stored
```

On a future run for the same topic:

```text
SQLite
   |
   v
Previous feedback
   |
   v
Generator
   |
   v
Better initial lesson
```

---

# 13. Project Structure

```text
self-evaluating-lesson-generator/
│
├── app/
│   ├── __init__.py
│   │
│   ├── config.py
│   │
│   ├── main.py
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── generator.py
│   │   ├── evaluator.py
│   │   └── regenerator.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── lessons.py
│   │
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── rubric.py
│   │   └── schemas.py
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   └── database.py
│   │
│   └── workflow/
│       ├── __init__.py
│       ├── state.py
│       └── graph.py
│
├── frontend/
│   └── streamlit_app.py
│
├── data/
│   └── memory.db
│
├── tests/
│   └── ...
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

# 14. Prerequisites

Make sure you have:

* Python 3.10+
* Git
* Gemini API key
* Internet connection

---

# 15. Create Virtual Environment

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

---

# 16. Install Dependencies

Run:

```bash
pip install -r requirements.txt
```

---

# 17. Configure Gemini API

Create a `.env` file in the project root.

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=your_gemini_model_here

MAX_RETRIES=2

DATABASE_PATH=data/memory.db

DEMO_FAILURE=false
```

Get the API key from Google AI Studio.

Do not commit `.env` to GitHub.

---

# 18. Initialize Database

The application automatically creates the SQLite tables when FastAPI starts.

You can also initialize it through Python:

```bash
python -c "from app.memory.database import initialize_database; initialize_database()"
```

The database will be created at:

```text
data/memory.db
```

---

# 19. Run the Backend

Start FastAPI:

```bash
uvicorn app.main:app --reload
```

The backend will run at:

```text
http://localhost:8000
```

Health check:

```text
GET /health
```

---

# 20. Test API Using Swagger

Open:

```text
http://localhost:8000/docs
```

Find:

```text
POST /api/v1/lessons/generate
```

Click "Try it out".

Use:

```json
{
  "topic": "Introduction to RAG"
}
```

Click "Execute".

The API returns:

* Final lesson
* Evaluation
* Number of attempts
* Rejection log
* Final status

---

# 21. Run Streamlit

Open another terminal.

Activate the virtual environment and run:

```bash
streamlit run frontend/streamlit_app.py
```

Streamlit will provide a local URL, normally:

```text
http://localhost:8501
```

Open it in your browser.

Enter a topic and click:

```text
Generate Lesson
```

---

# 22. Testing the Failure Loop

The application contains a deliberate failure mode for demonstrating the self-evaluation workflow.

In `.env`:

```env
DEMO_FAILURE=true
```

Restart FastAPI if required.

Generate a lesson.

The first generated lesson will contain a deliberately incorrect statement.

Expected workflow:

```text
Generate
   |
   v
Deliberate Error
   |
   v
Evaluate
   |
   v
FAIL
   |
   v
Log Failure
   |
   v
Regenerate
   |
   v
Evaluate
   |
   v
PASS
```

The Streamlit UI should show approximately:

```text
Attempts: 2
```

and display the rejection log.

After testing, change:

```env
DEMO_FAILURE=false
```

---

# 23. Checking SQLite Memory

Open the database:

```bash
sqlite3 data/memory.db
```

List tables:

```sql
.tables
```

Expected:

```text
failures
successful_fixes
```

Check failures:

```sql
SELECT * FROM failures;
```

Check successful fixes:

```sql
SELECT * FROM successful_fixes;
```

For readable output:

```sql
.headers on
.mode column

SELECT * FROM failures;
SELECT * FROM successful_fixes;
```

Exit:

```sql
.quit
```

---

# 24. API Request Flow

A complete request follows:

```text
User
 |
 | Enter topic
 v
Streamlit
 |
 | POST /api/v1/lessons/generate
 v
FastAPI
 |
 | Validate request
 v
LangGraph
 |
 +--> Load Memory
 |
 +--> Generate
 |       |
 |       v
 |     Gemini
 |
 +--> Pre-check
 |
 +--> Evaluate
 |       |
 |       v
 |     Gemini
 |
 +--> PASS
 |       |
 |       v
 |     Finalize
 |
 +--> FAIL
         |
         v
      Log Failure
         |
         v
       SQLite
         |
         v
      Regenerate
         |
         v
       Gemini
         |
         v
      Evaluate Again
         |
         v
      Finalize
         |
         v
       FastAPI
         |
         v
      Streamlit
         |
         v
        User
```

---

# 25. Technology Stack

| Technology       | Purpose                                        |
| ---------------- | ---------------------------------------------- |
| Python           | Core application                               |
| LangGraph        | Agent workflow/orchestration                   |
| Gemini API       | Lesson generation, evaluation and regeneration |
| Google GenAI SDK | Gemini API integration                         |
| FastAPI          | REST API                                       |
| Streamlit        | Frontend                                       |
| SQLite           | Persistent memory                              |
| Pydantic         | Data validation and structured output          |
| Uvicorn          | ASGI server                                    |
| python-dotenv    | Environment configuration                      |

---

# 26. Important Design Decisions

### Why LangGraph?

The workflow contains:

* Multiple nodes
* Shared state
* Conditional routing
* Regeneration loop
* Bounded retries

LangGraph provides a clean way to model this stateful workflow.

### Why FastAPI?

FastAPI handles:

* HTTP requests
* Request validation
* API responses
* API documentation
* Separation between frontend and workflow

### Why SQLite?

The memory requirements are relatively small for this project.

SQLite provides:

* Persistence
* Zero additional database server
* Simple local setup
* Easy inspection
* Good fit for a take-home assignment

### Why Gemini?

Gemini provides the LLM capabilities required for:

* Lesson generation
* Structured evaluation
* Lesson regeneration

### Why deterministic pre-checks?

Not every validation needs an LLM.

Simple checks such as:

* Empty content
* Lesson length
* Presence of examples
* Presence of required sections

can be performed cheaply with Python before invoking the evaluator.

---

# 27. Security

Never commit the Gemini API key.

The `.env` file should be ignored by Git.

Example:

```text
.env
.venv/
__pycache__/
*.pyc
```

---

# 28. Future Improvements

Possible improvements include:

* PostgreSQL instead of SQLite
* Vector-based memory retrieval
* Better memory ranking
* LangGraph checkpointing
* Authentication
* Streaming responses
* Background task execution
* Evaluation metrics
* Token/cost tracking
* More sophisticated deterministic validators
* Automated tests
* Docker deployment
* Production logging and observability

---

# 29. Demo Scenario

For demonstrating the system:

### Normal run

```text
Topic:
Introduction to RAG

Result:
PASS

Attempts:
1
```

### Deliberate failure

```text
DEMO_FAILURE=true

Result:
FAIL
   ↓
Log
   ↓
Regenerate
   ↓
PASS

Attempts:
2
```

### Persistent memory

Run the same topic again and show that previous failure information exists in SQLite and can be provided to the generator.

---

# 30. Summary

The application implements a self-evaluating content generation loop:

```text
Generate
   ↓
Evaluate
   ↓
PASS ───────────────> Ship
   |
   FAIL
   ↓
Log Failure
   ↓
Remember
   ↓
Regenerate
   ↓
Evaluate Again
   ↓
PASS ───────────────> Ship
```

The key architectural separation is:

```text
Streamlit  → UI
FastAPI    → API
LangGraph  → Workflow
Gemini     → Intelligence
SQLite     → Memory
Pydantic   → Structured Data
```

This allows the system to generate content, critically evaluate it, correct failures, remember previous feedback, and terminate safely using bounded retries.
