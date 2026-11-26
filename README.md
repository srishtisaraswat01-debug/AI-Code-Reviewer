# AI Code Reviewer Pro

A Streamlit app for reviewing Python snippets with static checks and AI feedback.

## Features
- Python syntax parsing with `ast`
- Optional Pyflakes static analysis
- A narrow pass/fail logic heuristic
- AI review with suggested corrected code (when Ollama is reachable)
- Syntax validation of suggested code
- JSON review report download

## Run locally
1. Install Python 3.11 or newer.
2. In this folder run: `python -m pip install -r requirements.txt`
3. Install and start Ollama, then pull a model: `ollama pull llama3.2`
4. Run: `python -m streamlit run app.py`

The current app uses local Ollama at `http://localhost:11434/api/generate`. On Render, `localhost` refers to the Render service, not your laptop. Therefore the AI review will not connect to your laptop's Ollama from Render without a separately hosted inference endpoint and code changes. Static checks and the Streamlit interface can still deploy.

The app does not execute submitted code. AI suggestions are not guaranteed to be correct; review and test them before use.
