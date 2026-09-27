# Simple Chat

Chat app built with React, Vite, Tailwind CSS, and FastAPI. Conversation history is stored in React state and cleared on refresh.

## Provider contract

`backend/llm_provider.py` exposes the synchronous interface used by the chat route:

```python
def generate_response(message: str, history: list[dict]) -> str:
    ...
```

History contains prior `{ "role": "user" | "assistant", "content": "..." }` turns in order, excluding the current message. The provider appends the current message and returns the response text without modifying history.

The provider uses the official Anthropic Python SDK with `claude-sonnet-4-5`, non-streaming responses, and `max_tokens=1024`. A local provider can implement the same interface without changes to the route or frontend.

## Anthropic API key

1. Sign in or create an account at the [Anthropic Console](https://console.anthropic.com/). Set up API billing/credits for your account.
2. Open **Settings > API keys**, select **Create key**, and copy the key. See the [official authentication guide](https://platform.claude.com/docs/en/manage-claude/authentication).
3. Copy `backend/.env.example` to `backend/.env` (PowerShell: `Copy-Item backend/.env.example backend/.env`; macOS/Linux: `cp backend/.env.example backend/.env`). If `.env` already exists, edit it rather than overwrite it.
4. Replace the placeholder in `backend/.env`:

```dotenv
ANTHROPIC_API_KEY=your-api-key-here
```

Restart the backend after setting the key. The provider loads this file regardless of the working directory; an existing environment variable takes precedence. `.env` is ignored by Git. Never put the key in frontend code or a `VITE_` variable.

This version requires internet access and incurs API usage costs. Full conversation history is sent with each request and contributes to input usage. Check [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing) for current rates. Missing or invalid credentials produce a clean generation error through the shared route.

The route runs in FastAPI's thread pool. Provider timeouts return HTTP 504; other generation failures return HTTP 502. The SDK timeout is 60 seconds with automatic retries disabled. The frontend waits up to 75 seconds; a browser timeout does not cancel an already-running generation.

## Local setup

Requires Node.js 22+ and Python 3.10+.

Backend, from the project root in PowerShell:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

On macOS/Linux, use `python3 -m venv .venv` and `.venv/bin/python` for pip and uvicorn. Set the API key as described above before sending messages.

Frontend, in a second terminal from the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. If PowerShell blocks `npm.ps1`, use `npm.cmd`. CORS allows localhost and 127.0.0.1 on port 5173. Optionally set `VITE_API_URL` in `frontend/.env` to change the backend URL, then restart Vite.

Enter sends; Shift+Enter adds a newline. Failed requests restore the draft for retry. The UI includes Markdown replies and a loading indicator.

`POST /chat` accepts `{ "message": "Hello", "history": [] }`, returns `{ "response": "..." }`, and uses `{ "detail": "..." }` for generation errors. API docs: http://localhost:8000/docs.

## Verification

Frontend: run `npm run build` inside `frontend`.

Backend contract tests substitute the provider without API calls or a local model:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

After configuring your API key, send "My name is Sam", then "What is my name?" to verify conversation context. This live check incurs API usage costs.
