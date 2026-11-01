# Basic Phone Directory API

A small FastAPI app with five endpoints for an in-memory phone directory.

## Run locally

Requires Python 3.10 or newer.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
fastapi dev app/main.py
```

Open <http://127.0.0.1:8000/docs> for the interactive API documentation.

## Agent prototype

The optional OpenAI-backed agent can answer directory questions and prepare create or update proposals. It only reads directory data or stages proposals; it never applies a change from `/agent/chat`.

Set an API key before starting the server:

```powershell
$env:OPENAI_API_KEY = "your-api-key"
$env:OPENAI_MODEL = "gpt-4.1-mini"
fastapi dev app/main.py
```

Send a request to `POST /agent/chat`:

```json
{
  "message": "Change Avery's phone number to +1-416-555-0199."
}
```

If the agent proposes a change, the response includes a `confirmation_id` and a preview. Apply it only by sending that ID to `POST /agent/confirm`:

```json
{
  "confirmation_id": "value-returned-in-the-proposal"
}
```

Confirmations expire after 10 minutes and can be used once. Pending proposals are stored in memory and are lost when the app restarts. The agent has no delete tool. Existing direct directory endpoints remain available independently of the agent confirmation flow. This demo has no authentication; keep it local and never use real personal or patient data. Requests and directory information used to answer them are sent to OpenAI.

## Run with Docker

Build the image from this folder:

```powershell
docker build -t basic-api .
```

The image installs the pinned runtime dependencies from `requirements.lock` and runs as a non-root user.
To refresh the lockfile with Python 3.12, install `pip-tools` and run `pip-compile --generate-hashes --strip-extras --output-file=requirements.lock requirements.txt`.

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
| PATCH | `/users/{user_id}` | Edit one or more fields |
| DELETE | `/users/{user_id}` | Delete an entry |
| POST | `/agent/chat` | Ask a question or prepare a create/update proposal |
| POST | `/agent/confirm` | Confirm a pending agent proposal |

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

When provided, `email` must be a valid email address.

Storage is in memory, so entries reset when the app restarts. This demo is not intended for real personal or patient data.

## Development and Codex workflow

This project was built with Codex to demonstrate a small, reviewable coding task.

- **Task:** Create a Python FastAPI phone directory with list, get, create, edit, and delete endpoints.
- **Changes:** Codex implemented list, get, create, edit, and delete routes using in-memory storage. The update and delete endpoints use `PATCH` and `DELETE`; the app also includes Docker support, focused `TestClient` tests, and a GitHub Actions test workflow.
- **Review:** A review checked update and delete behavior and test coverage. It found that create-field validation cases were grouped together and the generated-ID check only required a non-empty value. The tests now check each invalid field independently, confirm the returned ID is a UUID stored in the directory, and identify the invalid field in the validation response. Production API behavior was unchanged.
- **Validation:** The tightened test suite passed in [GitHub Actions run #5](https://github.com/fcortesnila/basic-api/actions/runs/40998575101). The local test command could not start because Python was unavailable, and a Docker image build could not run because the Docker engine was unavailable.

For development, install the development dependencies with `python -m pip install -r requirements-dev.txt`, run tests with `python -m pytest -q`, and start the app with `fastapi dev app/main.py`.
