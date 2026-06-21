# Travel Itinerary Agent

A Python CLI that generates travel itineraries using the [Groq API](https://console.groq.com/) with structured JSON outputs and [Pydantic](https://docs.pydantic.dev/) validation. The agent makes one API call per destination city and prints a validated itinerary for each.

## Prerequisites

- Python 3.9 or later
- A [Groq API key](https://console.groq.com/keys)

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd travel-itinerary-agent
```

### 2. Create a virtual environment

Create an isolated Python environment in the project directory:

```bash
python3 -m venv .venv
```

Activate it:

**macOS / Linux**

```bash
source .venv/bin/activate
```

**Windows**

```bash
.venv\Scripts\activate
```

When the virtual environment is active, your shell prompt will usually show `(.venv)`.

### 3. Install dependencies

With the virtual environment activated, install the packages listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

This installs:

- `groq` — Groq Python SDK
- `pydantic` — schema validation
- `python-dotenv` — read configuration from `.env`

### 4. Configure your API key

Copy the example env file and add your Groq API key:

```bash
cp .env.example .env
```

Edit `.env`:

```env
GROQ_API_KEY=your_key_here
```

The app reads `GROQ_API_KEY` from the `.env` file in the project root only. You do not need to export the key in your shell.

> **Note:** Do not commit `.env` to version control. It contains secrets.

## Usage

Run the CLI from the project root with the virtual environment activated:

```bash
python main.py \
  --source "New York" \
  --dest "Paris" --dest "Rome" \
  --days 5 \
  --budget moderate
```

### Arguments

| Flag | Required | Description |
|------|----------|-------------|
| `--source` | Yes | Departure city |
| `--dest` | Yes (repeatable) | Destination city; pass once per city |
| `--days` | Yes | Trip duration in days (must be > 0) |
| `--budget` | Yes | One of: `budget`, `moderate`, `luxury` |

View all options:

```bash
python main.py --help
```

### Example output

The app prints one validated JSON object per destination, separated by a blank line:

```json
{
  "destination": "Paris",
  "trip_duration_days": 5,
  "budget_category": "moderate",
  "top_attractions": ["Eiffel Tower", "Louvre", "..."],
  "daily_plan": [
    {"day": 1, "activities": ["...", "..."]},
    {"day": 2, "activities": ["...", "..."]}
  ]
}
```

## Project structure

| File | Purpose |
|------|---------|
| `main.py` | CLI entry point |
| `agent.py` | Groq client, prompts, and API calls |
| `schemas.py` | Pydantic models and validation |
| `requirements.txt` | Python dependencies |
| `.env.example` | Example environment configuration |

## Deactivating the virtual environment

When you are done working on the project:

```bash
deactivate
```
