# KYNYKOS AI Agent 🤖

A multi-provider AI assistant deployed on Render. Features a Telegram bot, a web dashboard, MCP server integration, S3 backups, and an **LLM multi-provider router** that uses Ollama locally and falls back through cloud providers automatically.

## Architecture

```
Telegram Bot (polling) → FastAPI app (8000) → LLM Router
                      ↓                            ↓
                Dashboard (web UI)        Ollama (primary, local)
                MCP Server (CLI)          Anthropic / Groq / OpenAI (fallbacks)
                S3 Backups (scheduled)
```

## Quick Start - Local Development

### Prerequisites
- Python 3.11+
- Poetry
- Docker + Docker Compose (optional)

### Setup

1. **Clone and prepare:**
   ```bash
   git clone https://github.com/JULIANJUAREZMX01/KYNYKOS_AI_Agent.git
   cd KYNYKOS_AI_Agent
   cp .env.example .env
   ```

2. **Install dependencies:**
   ```bash
   poetry install
   ```

3. **Run locally:**
   ```bash
   poetry run python -m uvicorn app.main:app --reload
   ```

   Or with Docker:
   ```bash
   docker-compose up -d
   ```

4. **Access:**
   - Dashboard: http://localhost:8000
   - API: http://localhost:8000/api/status

## Cloud Deployment - Render

### 1. Connect Repository
```bash
git push origin main
```

### 2. Create Render Service
1. Go to https://render.com
2. Create new Web Service
3. Connect this repository
4. Build command: `pip install poetry && poetry install`
5. Start command: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`

### 3. Configure Environment Variables
In Render dashboard, set:
- `TELEGRAM_TOKEN` - Telegram bot token
- `TELEGRAM_USER_ID` - Your Telegram user ID
- `OLLAMA_URL` - Ollama endpoint (e.g. `http://localhost:11434`; omit if not used on Render)
- `ANTHROPIC_API_KEY` - Anthropic API key
- `GROQ_API_KEY` - Groq API key
- `OPENAI_API_KEY` - OpenAI API key
- `LLM_CONFIG_PATH` - Path to `app/config/llm_config.yaml`
- `LLM_ROTATION_STRATEGY` - `round_robin` (default)
- `AWS_ACCESS_KEY_ID` - (optional) For S3 backups
- `AWS_SECRET_ACCESS_KEY` - (optional) For S3 backups
- `S3_BUCKET` - (optional) S3 bucket name
- `ENVIRONMENT` - Set to `production`

### 4. Deploy
Push changes to main branch:
```bash
git push origin main
```

## File Structure

```
KYNYKOS_AI_Agent/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── core/                # Agent loop & context
│   ├── cloud/               # Telegram, dashboard, MCP, backups
│   ├── config/
│   │   ├── llm_config.yaml  # LLM provider configuration
│   │   └── schema.py        # Settings & schemas
│   ├── services/
│   │   ├── llm_router.py    # Multi-provider LLM router
│   │   └── token_tracker.py # Per-provider token usage tracking
│   └── utils/               # Logging, helpers
├── docs/
│   └── LLM_ROUTER_SETUP.md  # LLM router setup guide
├── web/                     # Dashboard UI (HTML + JS)
├── infrastructure/          # Docker, Render config
├── config/                  # YAML configuration templates
├── workspace/               # Workspace templates (SOUL, USER, AGENTS, MEMORY)
├── scripts/                 # Utility scripts
├── tests/                   # Test suite
├── .github/workflows/       # CI/CD workflows
├── .env.example             # Environment variable template
├── pyproject.toml           # Python dependencies
├── Dockerfile               # Docker image
├── docker-compose.yml       # Local development
└── render.yaml              # Render deployment config
```

## LLM Router

The agent uses a multi-provider LLM router (`app/services/llm_router.py`) with **Ollama as the primary provider** and automatic fallback to cloud providers.

### Supported Providers

| Provider  | Priority | Rate Limit     | Notes                   |
|-----------|----------|----------------|-------------------------|
| Ollama    | 1        | ∞ (local)      | Requires local instance |
| Anthropic | 2        | 60 req/min     | `ANTHROPIC_API_KEY`     |
| Groq      | 3        | 30 req/min     | `GROQ_API_KEY`          |
| OpenAI    | 4        | 60 req/min     | `OPENAI_API_KEY`        |

### How Routing Works

1. Each incoming request is sent to the highest-priority available provider (Ollama first).
2. The token tracker monitors usage per provider. When a provider reaches ~90% of its rate limit, the router marks it as saturated and falls back to the next in priority order.
3. Ollama has an infinite/local limit — it is always preferred when running.
4. The rotation strategy (default: `round_robin`) and fallback delay are configured in `app/config/llm_config.yaml`.

### Configuration

- **YAML config**: `app/config/llm_config.yaml` — provider URLs, models, rate limits, and rotation strategy.
- **Environment variables**: copy `.env.example` to `.env` and fill in the relevant keys (see [Environment Variables](#configuration) section below).

See [`docs/LLM_ROUTER_SETUP.md`](docs/LLM_ROUTER_SETUP.md) for full setup instructions, including running Ollama locally via Docker.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Dashboard (HTML) |
| GET | `/api/status` | Health check |
| GET | `/api/sessions` | List sessions |
| GET | `/api/memory` | Get MEMORY.md |
| POST | `/api/memory` | Update MEMORY.md |
| GET | `/api/skills` | List skills |
| GET | `/api/logs` | Recent logs |

## Telegram Bot Commands

- `/start` - Initialize conversation
- Send message → Agent responds

## CI/CD Workflows

### deploy.yml
Auto-deploys to Render on push to `main`

### test.yml
Runs pytest, black, ruff on every push

### backup.yml
Scheduled backup to S3 every 6 hours

## MCP Server Integration

Access Nanobot from Claude Code CLI:

```bash
mcp connect app/cloud/mcp_server.py
```

### Available Tools
- `read_nanobot_memory(key)` - Read memory
- `add_nanobot_skill(name, content)` - Create skill
- `list_sessions()` - List conversations
- `get_nanobot_status()` - Health check

## Configuration

### Environment Variables (`.env`)

Copy `.env.example` to `.env` and fill in your values. Key variables:

```
# Telegram
TELEGRAM_TOKEN=your_token_here
TELEGRAM_USER_ID=your_user_id

# LLM Router
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-opus-4-6
GROQ_API_KEY=gsk-...
GROQ_MODEL=mixtral-8x7b
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
LLM_CONFIG_PATH=app/config/llm_config.yaml
LLM_ROTATION_STRATEGY=round_robin

# AWS S3 (optional, for backups)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
S3_BUCKET=

# App
ENVIRONMENT=development
LOG_LEVEL=INFO
```

> See `.env.example` for the complete list of variables with inline documentation.

### Workspace Files
- `workspace/SOUL.md` - Agent identity & personality
- `workspace/USER.md` - User profile & preferences
- `workspace/AGENTS.md` - Operating instructions
- `workspace/MEMORY.md` - Persistent memory
- `workspace/skills/` - Custom skills

## Development

### Run Tests
```bash
poetry run pytest tests/ -v
```

### Format Code
```bash
poetry run black app/
```

### Lint
```bash
poetry run ruff check app/
```

## Troubleshooting

### Telegram Bot Not Responding
1. Verify `TELEGRAM_TOKEN` in `.env`
2. Check logs: `docker logs nanobot-cloud`
3. Ensure Telegram channel is enabled in config

### Dashboard Not Loading
1. Check port 8000 is accessible
2. Verify web files in `./web/`
3. Check browser console for errors

### S3 Backups Failing
1. Verify AWS credentials in Render dashboard
2. Ensure S3 bucket exists and is writable
3. Check backup logs: `docker logs nanobot-cloud`

## Contributing

1. Create feature branch: `git checkout -b feature/name`
2. Make changes
3. Run tests: `poetry run pytest`
4. Commit: `git commit -am "message"`
5. Push: `git push origin feature/name`
6. Open PR

## Security

- Telegram token and API keys are environment secrets (never in repo)
- S3 credentials use IAM roles (when possible)
- HTTPS enforced on Render
- Sessions stored locally (not exposed)

## License

MIT - See LICENSE file

## Author

Julian Juarez (QUINTANA)

---

**Status**: 🟢 Production Ready
