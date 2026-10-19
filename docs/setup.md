# Setup and operation

## Requirements

- Python 3.10 or newer
- A virtual environment
- Google AI Studio API key only when using the Gemini provider

## Install

```powershell
cd D:\Projects\FuseMachine\Week18\admissions_guardrails
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r ui\requirements.txt
Copy-Item .env.example .env
```

The `.env` file is ignored by Git. Never commit a real API key.

## Providers

The default provider is deterministic `mock`:

```env
ADMISSIONS_MODEL=mock
```

To use Google AI Studio Gemini:

```env
ADMISSIONS_MODEL=gemini
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-2.5-flash
```

Create keys at [Google AI Studio](https://aistudio.google.com/apikey).

## Run the Streamlit UI

```powershell
python -m streamlit run ui\app.py --server.port 8501
```

The UI provides an assistant request view, evaluation dashboard, test-case
explorer, and requirements checklist.

## Run the checks

```powershell
python -m pytest tests -q
python run_evaluation.py
python run_after_fix.py
python run_tradeoff.py
```

Use the mock provider for repeatable tests. Gemini calls are network-dependent
and should not be used as the sole source of regression results.
