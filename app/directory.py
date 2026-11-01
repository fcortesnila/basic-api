from uuid import UUID, uuid4

from app.schemas import User, UserInput

# Demo storage: entries are lost when the server restarts.
phone_directory: dict[UUID, User] = {}


def list_users() -> list[User]:
    return list(phone_directory.values())


def get_user(user_id: UUID) -> User | None:
    return phone_directory.get(user_id)


def create_user(user_input: UserInput) -> User:
    user = User(id=uuid4(), **user_input.model_dump())
    phone_directory[user.id] = user
    return user


def update_user(user_id: UUID, updates: dict[str, object]) -> User | None:
    user = phone_directory.get(user_id)
    if user is None:
        return None

    updated_user = user.model_copy(update=updates)
    phone_directory[user_id] = updated_user
    return updated_user


def delete_user(user_id: UUID) -> bool:
    return phone_directory.pop(user_id, None) is not None
