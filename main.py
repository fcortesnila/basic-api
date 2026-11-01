from typing import Annotated
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(
    title="Basic Phone Directory API",
    description="A small in-memory phone directory with create, edit, and delete operations.",
    version="1.0.0",
)


class UserInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=3, max_length=30)
    email: str | None = Field(default=None, max_length=254)


class User(UserInput):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, min_length=3, max_length=30)
    email: str | None = Field(default=None, max_length=254)


# Demo storage: entries are lost when the server restarts.
phone_directory: dict[UUID, User] = {}


@app.get("/users", response_model=list[User], summary="List directory users")
def list_users() -> list[User]:
    """Return all users currently in the phone directory."""
    return list(phone_directory.values())


@app.get("/users/{user_id}", response_model=User, summary="Get a user")
def get_user(user_id: UUID) -> User:
    """Return one directory entry by its ID."""
    user = phone_directory.get(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@app.post("/users", response_model=User, status_code=status.HTTP_201_CREATED, summary="Create a user")
def create_user(user_input: UserInput) -> User:
    """Add a new entry to the phone directory."""
    user = User(id=uuid4(), **user_input.model_dump())
    phone_directory[user.id] = user
    return user


@app.patch("/users/{user_id}", response_model=User, summary="Edit a user")
def edit_user(user_id: UUID, changes: UserUpdate) -> User:
    """Update the provided fields on an existing directory entry."""
    user = phone_directory.get(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updates = changes.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide at least one field to update")
    if any(value is None for value in updates.values()):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Fields cannot be set to null")

    updated_user = user.model_copy(update=updates)
    phone_directory[user_id] = updated_user
    return updated_user


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a user")
def delete_user(user_id: UUID) -> None:
    """Remove a directory entry."""
    if phone_directory.pop(user_id, None) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
