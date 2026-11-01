from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from main import app, phone_directory


@pytest.fixture()
def client():
    """Keep the module-level in-memory directory isolated between tests."""
    phone_directory.clear()
    with TestClient(app) as test_client:
        yield test_client
    phone_directory.clear()


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
