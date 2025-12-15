# RewindAI

RewindAI is a stateful, command-based AI application framework powered by LangGraph and Google Gemini. It provides a foundation for building complex, multi-actor AI systems that can remember and process sequences of commands.

## Key Features

*   **Stateful AI:** Built on LangGraph to enable stateful and complex AI workflows.
*   **Command-based:** Interact with the AI through a simple command-based interface.
*   **LLM Powered:** Utilizes Google Gemini for natural language understanding and generation.
*   **Dual Interfaces:** Accessible through both a REST API and a command-line REPL.
*   **Persistent State:** Uses a PostgreSQL database to store event history and checkpoints.
*   **Dockerized:** Comes with a Docker-Compose setup for easy local development.

## Getting Started

Follow these instructions to get RewindAI up and running on your local machine.

### Prerequisites

*   Python 3.9+
*   Docker and Docker Compose
*   `git`

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd rewindai
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv my_venv
    source my_venv/bin/activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Copy the example `.env` file and fill in your database credentials.
    ```bash
    cp .env.example .env
    ```

5.  **Start the PostgreSQL database:**
    ```bash
    docker-compose up -d
    ```

6.  **Initialize the database:**
    Run the following scripts to set up the database tables:
    ```bash
    python scripts/postgres_init_event_store.py
    python scripts/postgres_init_langgraph.py
    ```

## Usage

You can interact with RewindAI through the REST API or the command-line REPL.

### REST API

To run the API server:

```bash
uvicorn app.api.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. You can find the API documentation at `http://127.0.0.1:8000/docs`.

### Command-Line REPL

To use the interactive REPL:

```bash
python app/main.py
```

## Contributing

Contributions are welcome! Please feel free to open an issue or submit a pull request.

## Maintainers

This project is currently maintained by Devansh Soni (indenigrate).
