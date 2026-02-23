# LLM Router Setup Guide

## Ollama Local Installation (Windows)

### Option A: Docker Desktop

1. Install Docker Desktop from https://www.docker.com/products/docker-desktop
2. Start Docker Desktop
3. Run setup script (PowerShell Admin):
   ```bat
   scripts\setup-ollama.bat
   ```
   Or manually:
   ```bash
   docker run -d -p 11434:11434 -v ollama:/root/.ollama ollama/ollama:latest
   ```
4. Pull Llama2 model:
   ```bash
   docker exec ollama-nanobot ollama pull llama2
   ```
5. Verify it's running:
   ```bash
   curl http://localhost:11434/api/tags
   ```

### Configuration

Edit `app/config/llm_config.yaml`:
- Ollama URL: `http://localhost:11434`
- Set API keys in `.env`:
  ```
  ANTHROPIC_API_KEY=sk-ant-...
  GROQ_API_KEY=gsk-...
  OPENAI_API_KEY=sk-...
  ```

## Provider Priority & Limits

| Provider  | Priority | Tokens/Min | Latency |
|-----------|----------|------------|---------|
| Ollama    | 1        | ∞          | ~0ms    |
| Anthropic | 2        | 50k        | ~500ms  |
| Groq      | 3        | 30k        | ~200ms  |
| OpenAI    | 4        | 90k        | ~800ms  |

## Testing the Router

```python
import asyncio
from app.services.llm_router import LLMRouter

async def test():
    router = LLMRouter()
    await router.initialize()
    response = await router.call_llm("Hello, world!")
    print(response)

asyncio.run(test())
```

## Router Behavior

- Automatically selects Ollama first (local, infinite tokens)
- Falls back to Anthropic if Ollama unavailable
- Monitors token usage per provider
- Switches provider when 90% of rate limit is reached
- Logs all routing decisions via loguru

## Monitoring

Check active provider:
```python
router.current_provider  # Returns "ollama", "anthropic", etc.
```

Check token status:
```python
from app.services.token_tracker import TokenTracker
tracker = TokenTracker()
remaining = tracker.get_remaining("anthropic")
print(f"Remaining tokens: {remaining}")
```

## Running Tests

```bash
pytest tests/test_llm_router.py tests/test_token_tracker.py tests/test_integration_llm_router.py -v
```

Expected: 7 passed
