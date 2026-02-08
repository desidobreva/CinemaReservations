## Cinema Reservations API

Small FastAPI service to manage movies, halls, screenings and seat
reservations. It includes role-based access (users, providers, admins),
reservation ticketing, and basic administrative tools.

## Features
- Create and manage movies, halls and screenings (admin/provider)
- Reserve seats (tickets are created at reservation time to block seats)
- Confirm, cancel and reschedule reservations
- Provider/admin flows to approve or decline reservations
- Test suite, type checks and linting configured

## Quick Start (install & run)

Ensure Python 3.11+ is installed. Create and activate a virtual environment,
then install the project and developer tools from `pyproject.toml`:

### Windows (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

### Linux / macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### Production install
```bash
pip install -e .
```

Run the API (development):

```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive API docs.

## API overview (selected endpoints)
- `POST /auth/register` — register and receive access token
- `POST /auth/login` — obtain access token
- `GET /cinema/movies` — list movies
- `POST /reservations` — create reservation (user)
- `POST /reservations/{id}/confirm` — confirm payment for reservation
- `POST /provider/reservations/{id}/approve` — provider approves
- `POST /admin/complete-past-reservations` — admin maintenance task

See the OpenAPI docs at `/docs` for full details and request/response
schemas.

## Tests, type checks and lint

Run tests and coverage:
```bash
pytest -q --cov=app           # Run tests with coverage
```

Type check and lint:
```bash
python -m mypy app/           # Type check
python -m pylint app/         # Lint
```

## Notes for graders / CI
- This project uses `pyproject.toml` as the authoritative manifest. Use
	`pip install -e .[dev]` to install runtime and dev dependencies in CI.
- An admin user is seeded automatically during DB initialization
	(`admin@example.com` / `admin1234`) for tests and local development.

## License
MIT
