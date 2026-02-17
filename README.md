# RewindAI

A conversational AI application that maintains persistent conversation threads with checkpoint and branching capabilities. Built with LangGraph and Google Generative AI, RewindAI allows you to have multi-turn conversations, save conversation states, and branch conversations from previous checkpoints.

## Features

- Interactive conversational AI powered by Google Generative AI (Gemini)
- Persistent conversation threads stored in PostgreSQL
- Conversation checkpointing for state management
- Branch conversations from previous messages in a conversation
- Multi-turn conversation support with message history
- Thread-based conversation isolation

## Prerequisites

- Python 3.11.5 or higher
- PostgreSQL 16 (can be run via Docker)
- UV package manager
- Google Generative AI API key

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/indenigrate/RewindAI.git
cd RewindAI
git checkout MVP
```

### 2. Quick Setup (Optional)

If you want to automate the entire setup process, run the provided setup script:

```bash
./setup.sh
```

This script will:
- Check for required dependencies (UV, Docker, Docker Compose)
- Install Python dependencies
- Create the `.env` file
- Start PostgreSQL container
- Initialize the database

Skip to the "Next Steps" section if you use this method.

### 3. Manual Installation

#### 3.1 Install Python Dependencies

Install dependencies using UV:

```bash
uv sync
```

This will install all required packages specified in `pyproject.toml`:

- langchain and langchain-core
- langgraph with PostgreSQL checkpoint support
- google-generativeai
- psycopg for PostgreSQL database connectivity
- python-dotenv for environment variable management

### 3. Set Up PostgreSQL Database

#### Option A: Using Docker Compose (Recommended)

Start PostgreSQL using Docker Compose:

```bash
docker-compose up -d
```

This will start a PostgreSQL 16 container with the configuration specified in `docker-compose.yml`.

#### Option B: Manual PostgreSQL Setup

If you prefer to set up PostgreSQL manually:

1. Create a database named `rewindAI_DB`
2. Create a user `rewindAI_admin` with password `rewindAI_admin_password`
3. Grant all privileges on the database to the user

### 4. Initialize Database Tables

Run the database initialization script to create necessary tables:

```bash
uv run scripts/postgres_init.py
uv run scripts/postgres_init_langgraph.py
```

These scripts will set up the database schema for:

- AI message checkpoints
- LangGraph state management tables

### 5. Configure Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` and add your configuration:

```
GOOGLE_API_KEY=your-google-api-key-here

DB_HOST=localhost
DB_PORT=5432
DB_NAME=rewindAI_DB
DB_USER=rewindAI_admin
DB_PASSWORD=rewindAI_admin_password
DB_SSLMODE=disable
```

Replace `your-google-api-key-here` with your actual Google API key. You can get one at https://ai.google.dev/

## Usage

### Starting the Application

Run the interactive REPL (Read-Eval-Print Loop):

```bash
uv run -m app.main
```

### Interactive Mode

Once the application starts, you will see prompts:

```
Source thread_id (Enter for default):
Checkpoint ID (Enter for latest):

Active thread: default

You:
```

#### Creating a New Conversation

- Press Enter at the `Source thread_id` prompt to use the default thread, or enter a custom thread ID
- Press Enter at the `Checkpoint ID` prompt to start fresh without branching
- Type your message and press Enter
- The AI will respond and save a checkpoint automatically

#### Branching from a Previous Message

- Enter the source thread ID you want to branch from
- Enter the checkpoint ID of the message you want to branch from
- Continue the conversation from that point in a new thread
- The application will preserve the relationship to the parent conversation

#### Example Conversation

```
Source thread_id (Enter for default):
Checkpoint ID (Enter for latest):

Active thread: default

You: hello
Bot: Hello Devansh! It's good to hear from you again. How can I help you today?

You: tell me a joke
Bot: Why don't scientists trust atoms? Because they make up everything!

You: that was funny
Bot: I'm glad you enjoyed it! Do you want to hear another one?

You: exit
```

### Exiting the Application

Type one of these commands and press Enter:

- `exit`
- `quit`
- `stop`

## Project Structure

```
RewindAI/
├── app/
│   ├── cli/                    # Command-line interface
│   │   └── repl.py            # Interactive conversation loop
│   ├── config/                # Configuration management
│   │   └── settings.py        # Environment and settings
│   ├── db/                    # Database connections
│   │   ├── langgraph.py       # LangGraph checkpoint setup
│   │   └── postgres.py        # PostgreSQL connection
│   ├── graph/                 # LangGraph workflow
│   │   ├── builder.py         # Graph construction
│   │   ├── nodes.py           # Graph nodes (AI interaction)
│   │   └── state.py           # Graph state definition
│   ├── models/                # LLM configuration
│   │   └── llm.py            # Google Generative AI setup
│   ├── services/              # Business logic
│   │   ├── branching.py       # Conversation branching logic
│   │   └── checkpoints.py     # Checkpoint management
│   └── main.py               # Application entry point
├── scripts/                   # Database initialization scripts
├── pyproject.toml            # Project dependencies
├── docker-compose.yml        # PostgreSQL Docker configuration
├── .env.example              # Example environment variables
└── README.md                 # This file
```

## How It Works

### Conversation Flow

1. User starts the application and provides a thread ID and optional checkpoint ID
2. If a checkpoint is specified, the conversation branches from that point
3. User input is converted to a HumanMessage and passed to the LangGraph workflow
4. The workflow invokes the Google Generative AI model with message history
5. The AI response is stored as an AIMessage
6. A checkpoint is automatically created after each AI response
7. Checkpoint metadata is stored in PostgreSQL for future branching

### Graph Architecture

The LangGraph workflow is simple and linear:

```
START -> google_model -> END
```

- START: Initial trigger
- google_model: Invokes Google Generative AI with conversation history
- END: Conversation continues or waits for new input

### State Management

Conversation state includes:

- Message history (all user and assistant messages)
- Thread ID (isolates different conversations)
- Checkpoint ID (marks a specific point in conversation history)

## Troubleshooting

### PostgreSQL Connection Error

If you get a connection error, verify:

1. PostgreSQL is running: `docker-compose ps` (if using Docker)
2. Database credentials in `.env` match your PostgreSQL setup
3. The database and user have been created

### Google API Key Error

Ensure your `GOOGLE_API_KEY` is valid and has:

- Access to Google Generative AI APIs
- The model `gemini-2.5-flash-lite` enabled

### Database Tables Not Found

Run the initialization scripts again:

```bash
uv run scripts/postgres_init.py
uv run scripts/postgres_init_langgraph.py
```

## Configuration

### Environment Variables

- `GOOGLE_API_KEY`: Your Google Generative AI API key (required)
- `DB_HOST`: PostgreSQL host (default: localhost)
- `DB_PORT`: PostgreSQL port (default: 5432)
- `DB_NAME`: Database name (default: rewindAI_DB)
- `DB_USER`: Database user (default: rewindAI_admin)
- `DB_PASSWORD`: Database password (default: rewindAI_admin_password)
- `DB_SSLMODE`: SSL mode for database connection (default: disable)

### Model Configuration

The default model is `gemini-2.5-flash-lite`. To change it, edit `app/config/settings.py`:

```python
MODEL_NAME = "gemini-2.5-flash-lite"  # Change this to another available model
```

## Development

### Code Organization

- Database operations: `app/db/`
- Conversation logic: `app/cli/` and `app/services/`
- AI model interaction: `app/graph/` and `app/models/`
- Configuration: `app/config/`
