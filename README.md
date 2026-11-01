# Basic Phone Directory API

A small FastAPI app with five endpoints for an in-memory phone directory.

## Run locally

Requires Python 3.10 or newer.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
fastapi dev main.py
```

Open <http://127.0.0.1:8000/docs> for the interactive API documentation.

## Run with Docker

Build the image from this folder:

```powershell
docker build -t basic-api .
```

Start the container:

```powershell
docker run --rm -p 8000:8000 --name basic-api basic-api
```

Then open <http://localhost:8000/docs>. Stop the container with `Ctrl+C`.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/users` | List all directory entries |
| GET | `/users/{user_id}` | Get one entry by UUID |
| POST | `/users` | Create an entry |
| POST | `/users/{user_id}` | Edit one or more fields |
| POST | `/users/{user_id}/delete` | Delete an entry |

Create body example:

```json
{
  "name": "Avery Chen",
  "phone": "+1-416-555-0100",
  "email": "avery@example.com"
}
```

Edit body example (include only fields to change):

```json
{
  "phone": "+1-416-555-0123"
}
```

Storage is in memory, so entries reset when the app restarts. This demo is not intended for real personal or patient data.

## Development and Codex workflow

This project was built with Codex to demonstrate a small, reviewable coding task.

- **Task:** Create a Python FastAPI phone directory with two GET endpoints and three POST endpoints.
- **Changes:** Codex implemented list, get, create, edit, and delete routes using in-memory storage; added Docker support, focused `TestClient` tests, and a GitHub Actions test workflow.
- **Review:** A review checked update and delete behavior and test coverage. It found that create-field validation cases were grouped together and the generated-ID check only required a non-empty value. The tests now check each invalid field independently, confirm the returned ID is a UUID stored in the directory, and identify the invalid field in the validation response. Production API behavior was unchanged.
- **Validation:** The tightened test suite passed in [GitHub Actions run #5](https://github.com/fcortesnila/basic-api/actions/runs/40998575101). The local test command could not start because Python was unavailable, and a Docker image build could not run because the Docker engine was unavailable.

For development, install the development dependencies with `python -m pip install -r requirements-dev.txt`, run tests with `python -m pytest -q`, and start the app with `fastapi dev main.py`.
