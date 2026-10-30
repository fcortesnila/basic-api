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

This starter uses memory for storage, so entries reset when the app restarts. Replace the dictionary with a database for persistent data.
