## Setup (venv)

### Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

### Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

## Run
uvicorn app.main:app --reload

## Tests
pytest -q --cov=app
