# PhishGuard

Copy-and-analyze phishing checker for Hebrew SMS/WhatsApp messages.

## Architecture (matches project spec)

See `ARCHITECTURE.md` for full module details.

- **Module 1** (`phishguard/domain_verification.py`): Safe Browsing URL check -> `blocking_score` `0` or `100`, hard override on `100`.
- **Module 2** (`phishguard/semantic_agent.py`): LLM semantic agent -> `S_AI` `[0,100]` + Hebrew explanation JSON.
- **Orchestrator** (`phishguard/agent.py`): runs Module 1 first; skips Module 2 on hard block.
- **UI** (`web/index.html` + `scripts/run_ui_server.py`): paste message -> `POST /analyze`.

## Setup

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -3 -m pip install -r requirements.txt
py -3 scripts/train_model.py
```

## API keys

```powershell
$env:SAFE_BROWSING_API_KEY="YOUR_KEY"
$env:OPENAI_API_KEY="YOUR_KEY"   # optional, full Module 2 LLM
```

Safe Browsing setup: [Get started](https://developers.google.com/safe-browsing/v4/get-started)

## Run

```powershell
py -3 scripts/run_ui_server.py
```

Open: http://127.0.0.1:8000

## Response fields

- `module1_blocking_score`: `0` or `100`
- `module2_s_ai`: `0-100` (null when Module 2 skipped)
- `skipped_module2`: `true` when Safe Browsing hard override triggered
- `final_score`, `tier`, `explanation`, `reasons`
