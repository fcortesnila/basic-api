import json
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app import agent_service
from app.directory import phone_directory
from app.main import app


@pytest.fixture()
def client():
    """Keep the module-level in-memory directory isolated between tests."""
    phone_directory.clear()
    with agent_service._PROPOSALS_LOCK:
        agent_service._PENDING_ACTIONS.clear()
    with TestClient(app) as test_client:
        yield test_client
    phone_directory.clear()
    with agent_service._PROPOSALS_LOCK:
        agent_service._PENDING_ACTIONS.clear()


class FakeResponseItem:
    def __init__(self, *, name: str, arguments: dict, call_id: str = "call-1") -> None:
        self.type = "function_call"
        self.name = name
        self.arguments = json.dumps(arguments)
        self.call_id = call_id

    def model_dump(self, *, exclude_none: bool = True) -> dict:
        values = {
            "type": self.type,
            "name": self.name,
            "arguments": self.arguments,
            "call_id": self.call_id,
        }
        return (
            {key: value for key, value in values.items() if value is not None}
            if exclude_none
            else values
        )


class FakeResponses:
    def __init__(self, *responses: SimpleNamespace) -> None:
        self.responses = list(responses)
        self.calls: list[dict] = []

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        return self.responses.pop(0)


def fake_response(*, output: list | None = None, text: str = "") -> SimpleNamespace:
    return SimpleNamespace(output=output or [], output_text=text)


def fake_openai_client(*responses: SimpleNamespace) -> SimpleNamespace:
    return SimpleNamespace(responses=FakeResponses(*responses))


def create_user(client: TestClient, **overrides: object) -> dict:
    payload = {
        "name": "Avery Chen",
        "phone": "+1-416-555-0100",
        "email": "avery@example.com",
    }
    payload.update(overrides)
    response = client.post("/users", json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_user_returns_generated_id_and_fields(client: TestClient) -> None:
    response = client.post(
        "/users",
        json={"name": "Avery Chen", "phone": "+1-416-555-0100"},
    )

    assert response.status_code == 201
    body = response.json()
    generated_id = UUID(body["id"])
    assert generated_id in phone_directory
    assert body["name"] == "Avery Chen"
    assert body["phone"] == "+1-416-555-0100"
    assert body["email"] is None


def test_list_users_returns_created_entries(client: TestClient) -> None:
    first = create_user(client)
    second = create_user(client, name="Jordan Lee", phone="555-0101")

    response = client.get("/users")

    assert response.status_code == 200
    assert response.json() == [first, second]


def test_get_user_returns_matching_entry(client: TestClient) -> None:
    created = create_user(client)

    response = client.get(f"/users/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", ""),
        ("name", "N" * 101),
        ("phone", "12"),
        ("phone", "1" * 31),
        ("email", "a" * 255),
    ],
)
def test_create_rejects_invalid_field_lengths(
    client: TestClient, field: str, value: str
) -> None:
    payload = {
        "name": "Avery Chen",
        "phone": "+1-416-555-0100",
        "email": "avery@example.com",
    }
    payload[field] = value

    response = client.post(
        "/users",
        json=payload,
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == field
    assert client.get("/users").json() == []


@pytest.mark.parametrize("email", ["not-an-email", "avery@", "avery@example..com"])
def test_create_rejects_invalid_email_format(client: TestClient, email: str) -> None:
    response = client.post(
        "/users",
        json={
            "name": "Avery Chen",
            "phone": "+1-416-555-0100",
            "email": email,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == "email"
    assert client.get("/users").json() == []


def test_edit_user_updates_one_field_and_preserves_other_fields(client: TestClient) -> None:
    created = create_user(client)

    response = client.patch(f"/users/{created['id']}", json={"phone": "+1-416-555-0199"})

    assert response.status_code == 200
    assert response.json() == {
        **created,
        "phone": "+1-416-555-0199",
    }


def test_edit_user_updates_multiple_fields(client: TestClient) -> None:
    created = create_user(client)

    response = client.patch(
        f"/users/{created['id']}",
        json={"name": "Avery C.", "email": "avery.c@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        **created,
        "name": "Avery C.",
        "email": "avery.c@example.com",
    }


def test_edit_rejects_empty_patch_without_changing_user(client: TestClient) -> None:
    created = create_user(client)

    response = client.patch(f"/users/{created['id']}", json={})

    assert response.status_code == 400
    assert client.get(f"/users/{created['id']}").json() == created


@pytest.mark.parametrize("payload", [{"name": None}, {"phone": None}, {"email": None}])
def test_edit_rejects_null_values_without_changing_user(
    client: TestClient, payload: dict[str, object]
) -> None:
    created = create_user(client)

    response = client.patch(f"/users/{created['id']}", json=payload)

    assert response.status_code == 422
    assert client.get(f"/users/{created['id']}").json() == created


def test_edit_rejects_invalid_field_length_without_changing_user(client: TestClient) -> None:
    created = create_user(client)

    response = client.patch(f"/users/{created['id']}", json={"phone": "12"})

    assert response.status_code == 422
    assert client.get(f"/users/{created['id']}").json() == created


@pytest.mark.parametrize("email", ["not-an-email", "avery@"])
def test_edit_rejects_invalid_email_without_changing_user(
    client: TestClient, email: str
) -> None:
    created = create_user(client)

    response = client.patch(f"/users/{created['id']}", json={"email": email})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == "email"
    assert client.get(f"/users/{created['id']}").json() == created


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("get", "/users/{user_id}", None),
        ("patch", "/users/{user_id}", {"name": "Missing"}),
        ("delete", "/users/{user_id}", None),
    ],
)
def test_user_operations_return_404_for_missing_id(
    client: TestClient, method: str, path: str, payload: dict | None
) -> None:
    missing_id = "00000000-0000-0000-0000-000000000001"
    response = getattr(client, method)(
        path.format(user_id=missing_id),
        **({"json": payload} if payload is not None else {}),
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}
    assert client.get("/users").json() == []


def test_delete_user_returns_no_content_and_removes_entry(client: TestClient) -> None:
    created = create_user(client)

    response = client.delete(f"/users/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/users").json() == []
    assert client.get(f"/users/{created['id']}").status_code == 404


def test_deleting_same_user_twice_returns_404(client: TestClient) -> None:
    created = create_user(client)
    delete_response = client.delete(f"/users/{created['id']}")

    second_delete = client.delete(f"/users/{created['id']}")

    assert delete_response.status_code == 204
    assert second_delete.status_code == 404
    assert client.get("/users").json() == []


def test_legacy_edit_and_delete_routes_are_not_available(client: TestClient) -> None:
    created = create_user(client)

    legacy_edit = client.post(f"/users/{created['id']}", json={"phone": "555-0101"})
    legacy_delete = client.post(f"/users/{created['id']}/delete")

    assert legacy_edit.status_code == 405
    assert legacy_delete.status_code == 404
    assert client.get(f"/users/{created['id']}").json() == created


def test_agent_read_tool_uses_directory_and_does_not_mutate(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    created = create_user(client)
    fake_client = fake_openai_client(
        fake_response(
            output=[
                FakeResponseItem(
                    name="get_user",
                    arguments={"user_id": created["id"]},
                )
            ]
        ),
        fake_response(text="Found Avery's directory entry."),
    )
    monkeypatch.setattr(agent_service, "get_openai_client", lambda: fake_client)

    response = client.post("/agent/chat", json={"message": "Look up Avery."})

    assert response.status_code == 200
    assert response.json()["answer"] == "Found Avery's directory entry."
    assert response.json()["proposals"] == []
    assert client.get("/users").json() == [created]
    tool_names = {tool["name"] for tool in fake_client.responses.calls[0]["tools"]}
    assert "list_users" in tool_names
    assert "get_user" in tool_names
    assert "delete_user" not in tool_names
    tool_output = next(
        item
        for item in fake_client.responses.calls[1]["input"]
        if item.get("type") == "function_call_output"
    )
    assert json.loads(tool_output["output"])["user"]["id"] == created["id"]


def test_agent_list_users_tool_returns_directory_entries(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    created = create_user(client)
    fake_client = fake_openai_client(
        fake_response(
            output=[
                FakeResponseItem(name="list_users", arguments={}),
            ]
        ),
        fake_response(text="There is one directory entry."),
    )
    monkeypatch.setattr(agent_service, "get_openai_client", lambda: fake_client)

    response = client.post("/agent/chat", json={"message": "How many entries are there?"})

    assert response.status_code == 200
    assert response.json()["proposals"] == []
    tool_output = next(
        item
        for item in fake_client.responses.calls[1]["input"]
        if item.get("type") == "function_call_output"
    )
    assert json.loads(tool_output["output"])["users"] == [created]
    assert client.get("/users").json() == [created]


def test_agent_create_requires_confirmation_and_confirmation_is_one_time(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_client = fake_openai_client(
        fake_response(
            output=[
                FakeResponseItem(
                    name="propose_create_user",
                    arguments={
                        "name": "Avery Chen",
                        "phone": "+1-416-555-0100",
                        "email": "avery@example.com",
                    },
                )
            ]
        ),
        fake_response(text="The new entry is ready for confirmation."),
    )
    monkeypatch.setattr(agent_service, "get_openai_client", lambda: fake_client)

    proposed = client.post(
        "/agent/chat",
        json={"message": "Add Avery Chen, +1-416-555-0100, avery@example.com."},
    )

    assert proposed.status_code == 200
    proposal = proposed.json()["proposals"][0]
    assert proposal["action"] == "create"
    assert proposal["changes"] == {
        "name": "Avery Chen",
        "phone": "+1-416-555-0100",
        "email": "avery@example.com",
    }
    assert client.get("/users").json() == []

    confirmed = client.post(
        "/agent/confirm",
        json={"confirmation_id": proposal["confirmation_id"]},
    )
    repeated = client.post(
        "/agent/confirm",
        json={"confirmation_id": proposal["confirmation_id"]},
    )

    assert confirmed.status_code == 200
    assert confirmed.json()["action"] == "create"
    assert confirmed.json()["user"]["name"] == "Avery Chen"
    assert repeated.status_code == 404
    assert len(client.get("/users").json()) == 1


def test_agent_update_requires_confirmation(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    created = create_user(client)
    fake_client = fake_openai_client(
        fake_response(
            output=[
                FakeResponseItem(
                    name="propose_update_user",
                    arguments={
                        "user_id": created["id"],
                        "name": None,
                        "phone": "+1-416-555-0199",
                        "email": None,
                    },
                )
            ]
        ),
        fake_response(text="The phone update is ready for confirmation."),
    )
    monkeypatch.setattr(agent_service, "get_openai_client", lambda: fake_client)

    proposed = client.post(
        "/agent/chat",
        json={"message": f"Change {created['name']}'s phone number."},
    )

    assert proposed.status_code == 200
    proposal = proposed.json()["proposals"][0]
    assert proposal["action"] == "update"
    assert proposal["changes"] == {"phone": "+1-416-555-0199"}
    assert client.get(f"/users/{created['id']}").json() == created

    confirmed = client.post(
        "/agent/confirm",
        json={"confirmation_id": proposal["confirmation_id"]},
    )

    assert confirmed.status_code == 200
    assert confirmed.json()["user"]["phone"] == "+1-416-555-0199"
    assert client.get(f"/users/{created['id']}").json()["phone"] == "+1-416-555-0199"


def test_agent_rejects_invalid_tool_arguments_without_proposal_or_write(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_client = fake_openai_client(
        fake_response(
            output=[
                FakeResponseItem(
                    name="propose_create_user",
                    arguments={
                        "name": "Avery Chen",
                        "phone": "12",
                        "email": "not-an-email",
                    },
                )
            ]
        ),
        fake_response(text="I could not prepare that entry because its details are invalid."),
    )
    monkeypatch.setattr(agent_service, "get_openai_client", lambda: fake_client)

    response = client.post("/agent/chat", json={"message": "Add an entry."})

    assert response.status_code == 200
    assert response.json()["proposals"] == []
    assert client.get("/users").json() == []
    tool_output = next(
        item
        for item in fake_client.responses.calls[1]["input"]
        if item.get("type") == "function_call_output"
    )
    result = json.loads(tool_output["output"])
    assert result["error"] == "Invalid tool arguments"


def test_agent_without_api_key_returns_configuration_error(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post("/agent/chat", json={"message": "List users."})

    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]
