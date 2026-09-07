 # Frost‑Edge‑System

   **Detect frost risk on the edge** – a tiny Python service that reads
 temperature/humidity data, runs a lightweight ML model, and sends
 real‑time alerts (Telegram, SMS, console) while exposing a simple
 dashboard.

   ---

   ## Overview

   | Layer | What it does | Main module |
   |-------|--------------|-------------|
   | **Sensors** | Reads temperature & humidity (mock or real) |
 `sensors/poller.py` |
   | **Inference** | Predicts minimum temperature for the next few hours
 and returns a risk score (0 – 1) | `inference/__init__.py` |
   | **Alerts** | Applies a policy (threshold, hysteresis, cooldown) and
 dispatches the alert through configured channels |
 `alerts/dispatcher.py` |
   | **Dashboard** | Flask/fastapi UI that shows recent readings, predictions and
 sent alerts | `dashboard/app.py` |

   All data are persisted in a single SQLite file (`frost_edge.db`).
 Each layer talks only through this DB, so they can be started/stopped
 independently.

   ---

   ## Simple flowchart

 ```

 ┌─────────────────────┐      ┌─────────────────────┐
 │  sensors/poller.py  │─────►│  inference/run()     │
 │ (read raw sensor)   │      │ (predict frost)    │
 └─────────────────────┘      └───────┬─────────────┘
                                       │
                                       ▼
                            ┌─────────────────────┐
                            │  storage/frost_edge │
                            │  .db (raw, predict,│
                            │   alerts_sent)     │
                            └───────▲─────▲───────┘
                                    │     │
                  ┌─────────────────┘     └─────────────────┐
                  ▼                                         ▼
    ┌─────────────────────┐                     ┌─────────────────────┐
    │ alerts/dispatcher   │◄────────────────────│ dashboard/app.py   │
    │ (policy + channels) │   (reads DB)        │ (web UI + API)    │
    └─────────────────────┘                     └─────────────────────┘

 ```

   ---

   ## Repository layout

 ```

 frost-edge-system/
 │
 ├─ alerts/                # Notification subsystem
 │   ├─ init.py
 │   ├─ alert_policy.py    # Decision logic (threshold, hysteresis,
 cooldown)
 │   ├─ base.py           # Abstract AlertChannel + AlertSendError
 │   ├─ console_channel.py   # Simple stdout channel
 │   ├─ dispatcher.py         # Build channels, evaluate policy, log to
 DB
 │   ├─ sms_gateway.py        # Generic HTTP‑SMS channel (stub)
 │   └─ telegram_bot.py      # Telegram Bot API implementation
 │
 ├─ config/                # Runtime configuration
 │   ├─ init.py
 │   ├─ config.example.yaml # Template (git‑ignored when renamed to
 config.yaml)
 │   └─ loader.py            # Loads YAML + validates required keys
 │
 ├─ dashboard/             # Flask UI
 │   ├─ init.py
 │   ├─ app.py                 # Flask app, API endpoints, HTML rendering
 │   ├─ static/
 │   │   ├─ script.js
 │   │   └─ style.css
 │   └─ templates/
 │       └─ index.html
 │
 ├─ inference/            # Model‑inference wrapper
 │   ├─ init.py            # run_inference(reading) → prediction dict
 │   └─ model_artifact/        # Frozen model file(s)
 │
 ├─ sensors/              # Sensor abstraction & poller
 │   ├─ init.py
 │   ├─ base.py                # Abstract SensorReader
 │   ├─ mock_sensor.py         # Generates synthetic data or reads CSV
 │   └─ poller.py              # Periodic reader → stores raw data →
 calls inference
 │
 ├─ storage/               # SQLite helper and schema
 │   ├─ db.py                  # CRUD helpers (insert/read raw,
 predictions, alerts)
 │   └─ schema.sql             # CREATE TABLE statements
 │
 ├─ tests/                 # Pytest suite (37 tests)
 │   ├─ test_alert_policy.py
 │   ├─ test_dashboard.py
 │   ├─ test_db.py
 │   ├─ test_dispatcher.py
 │   ├─ test_poller.py
 │   └─ test_sensor_interface.py
 │
 ├─ pyproject.toml         # Poetry/UV project metadata & dependencies
 ├─ uv.lock                # Locked versions for deterministic installs
 └─ README.md              # ← you are reading this file

 ```

 ## Quick start (local development)

   > **Prerequisites** – Python 3.11 or 3.12, `uv` (or `pip`/`venv`).

   ```bash
   # 1️⃣ Clone the repo and cd into it
   git clone https://github.com/your-org/frost-edge-system.git
   cd frost-edge-system

   # 2️⃣ Create a virtual environment and install dependencies
   uv venv               # creates .venv
   source .venv/bin/activate
   uv sync               # installs from pyproject.toml

   # 3️⃣ (Optional) Create a .env file for secrets
   cat > .env <<EOF
   TELEGRAM_BOT_TOKEN=123456789:AAAbCdEfGhIjKlMnOpQrStUvWxYz1234567
   TELEGRAM_CHAT_ID=987654321
   EOF

   # 4️⃣ Copy the example config and edit if needed
   cp config/config.example.yaml config/config.yaml
   # Edit config/config.yaml – e.g., change poll_interval_seconds or DB path


```
## Testing

* for now there are 37 test , later on adding more test for the api's.

 ```bash
   uv run pytest tests/
 ```

## Code quality (ruff)

 Before committing, run the linter and automatically fix what it can:

 ```bash
   uv run ruff check . 
   # if there is any issue then run below --fix command
   uv run ruff check . --fix  
   git add .
 ```



