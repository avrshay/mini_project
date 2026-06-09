# PhishGuard Architecture

## Module 1 - Domain Verification Engine and Blacklists

| | |
|---|---|
| **Input** | `list[str]` URLs extracted in pre-processing (`phishguard/preprocess.py`) |
| **Output** | `blocking_score` in `{0, 100}` (`phishguard/domain_verification.py`) |
| **Mapping** | Deterministic: at least one malicious URL -> `100`; otherwise -> `0` |
| **Method** | Async HTTP POST to Google Safe Browsing Lookup API v4 (`threatMatches:find`) |
| **Hard override** | If score is `100`, Module 2 is skipped and final risk is forced to `100` / `מסוכן` |

Implementation file: `phishguard/domain_verification.py`

## Module 2 - Rules-Based Semantic Analysis Engine (LLM Agent)

| | |
|---|---|
| **Input** | Raw Hebrew SMS/WhatsApp text (`str`) |
| **Output** | Structured JSON: `S_AI` in `[0,100]`, `explanation_he`, `analysis_steps` |
| **Method** | LLM agent with prompt engineering (`phishguard/semantic_agent.py`) |
| **Prompt rules** | Impersonation, urgency, CTA, sensitive info, financial/winning scams |
| **Techniques** | Few-shot examples, Chain-of-Thought (`analysis_steps`), strict JSON schema |
| **Fallback** | If `OPENAI_API_KEY` is missing, baseline ML outputs same JSON fields |

Prompt file: `phishguard/prompts/semantic_agent_system.txt`

## Orchestration

`phishguard/agent.py`:

1. Extract URLs
2. Run Module 1
3. If `blocking_score == 100` -> hard override (stop)
4. Else run Module 2 and map `S_AI` to final score/tier

## Output Mapping (Client)

`phishguard/risk.py`:

- Green `0-39` -> `בטוח`
- Orange `40-79` -> `חשוד`
- Red `80-100` -> `מסוכן`

## Environment Variables

```powershell
$env:SAFE_BROWSING_API_KEY="..."
$env:OPENAI_API_KEY="..."   # optional, enables full Module 2 LLM
$env:OPENAI_MODEL="gpt-4o-mini"
```

References:

- [Safe Browsing v4 Get Started](https://developers.google.com/safe-browsing/v4/get-started)
- [Safe Browsing Local Databases](https://developers.google.com/safe-browsing/v4/local-databases#database-setup)
