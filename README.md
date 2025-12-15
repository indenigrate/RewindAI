# RewindAI: Version-Controlled Conversational AI

RewindAI is a cutting-edge system designed to bring version control capabilities to conversational AI. Inspired by Git, it allows for deterministic replay, branching of conversation timelines, resuming from specific checkpoints, and comprehensive history inspection. This project provides both an interactive Command Line Interface (CLI) and a robust API for integrating AI conversations into other applications.

---

## ✨ Why RewindAI is Useful

In the rapidly evolving field of AI, reproducibility and traceability are paramount. RewindAI addresses these challenges by offering:

-   **Deterministic Replay:** Every AI response can be precisely reproduced, enabling thorough debugging and analysis.
-   **Conversation Branching:** Explore alternative conversational paths by forking a thread from any past AI message.
-   **Checkpoint-based Resumption:** Easily resume conversations from any saved checkpoint, providing flexibility and robust recovery.
-   **Transparent History:** Inspect the full history of any conversation, understanding its evolution and the decisions made at each step.
-   **Interactive & Asynchronous Modes:** Engage with the AI directly via a CLI or integrate it into your services using a powerful API with background workers.

RewindAI transforms AI conversations from ephemeral interactions into auditable, debuggable, and extensible timelines.

---

## 🚀 Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

*   Python 3.10+
*   Docker and Docker Compose (for PostgreSQL database)
*   `pip` (Python package installer)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/rewindai.git
cd rewindai
```

### 2. Set up your environment variables

Copy the example environment file and fill in your details, especially your `GOOGLE_API_KEY` (required for LLM interactions).

```bash
cp .env.example .env
# Open .env and add your GOOGLE_API_KEY
```

### 3. Start the PostgreSQL Database

RewindAI uses PostgreSQL for its event store and projection tables. Docker Compose provides an easy way to set this up.

```bash
docker-compose up -d postgres
```

### 4. Create a Python Virtual Environment and Install Dependencies

It's recommended to use a virtual environment to manage project dependencies.

```bash
python3 -m venv my_venv
source my_venv/bin/activate
pip install -r requirements.txt
```

### 5. Initialize the Database

The project uses event sourcing, which requires specific tables for the event store and projections. Run the initialization scripts:

```bash
PYTHONPATH=. ./my_venv/bin/python3 scripts/postgres_init_event_store.py
PYTHONPATH=. ./my_venv/bin/python3 app/projections/worker.py # This will create projection tables on first run
```

### 6. Run the Projection Worker

The projection worker consumes events and builds the read models used by the API. This should run continuously in the background.

```bash
PYTHONPATH=. ./my_venv/bin/python3 app/projections/worker.py &
```

### 7. Run the API Server

The FastAPI server exposes the command and read endpoints.

```bash
PYTHONPATH=. ./my_venv/bin/uvicorn app.api.main:app --host 0.0.0.0 --port 8000 &
```
The API documentation is available at `http://localhost:8000/docs`.

### 8. Use the CLI (REPL)

Engage with the AI directly via the interactive CLI.

```bash
PYTHONPATH=. ./my_venv/bin/python3 app/cli/repl.py
```

---

## 📖 Usage Examples

### CLI Interaction

Once the CLI is running, you can create new threads, send messages, inspect history, and fork conversations interactively.

```
(REWIND_AI) > new thread
# ... AI output ...
(REWIND_AI) > send "Hello there!"
# ... AI output ...
(REWIND_AI) > fork from 1
# ... AI creates a new branch ...
```

### API Interaction

The API provides programmatic access to all core functionalities. Detailed API documentation, including request/response schemas and `curl` examples, is available in [API.md](API.md).

---

## 🤝 Contribution

We welcome contributions! If you're interested in improving RewindAI, please refer to our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on setting up your development environment, submitting pull requests, and coding standards.

---

## ❓ Getting Help

If you encounter any issues or have questions, please check:

*   The [API Documentation](API.md) for endpoint details.
*   Existing [GitHub Issues](https://github.com/your-username/rewindai/issues) for similar problems.
*   Open a new [GitHub Issue](https://github.com/your-username/rewindai/issues/new) if you can't find a solution.

---

## 🧑‍💻 Maintainers

*   **[Devansh]** - Initial development and core maintenance.
    *   GitHub: [\@indenigrate](https://github.com/indenigrate)

---