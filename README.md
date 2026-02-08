## Setup (venv)

### Windows (PowerShell)
```ps1
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Linux / macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Alternative: Modern PEP 517 Installation
After activating venv:
```bash
pip install -e .[dev]  # Install with dev tools (mypy, pylint, pytest)
pip install -e .       # Install production only
```

## Run
```bash
uvicorn app.main:app --reload
```

## Tests
```bash
pytest -q --cov=app           # Run with coverage
mypy app/                     # Type check
pylint app/                   # Lint
```
