from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app import directory
from app.schemas import User, UserInput, UserUpdate

router = APIRouter()


@router.get("/users", response_model=list[User], summary="List directory users")
def list_users() -> list[User]:
    """Return all users currently in the phone directory."""
    return directory.list_users()


@router.get("/users/{user_id}", response_model=User, summary="Get a user")
def get_user(user_id: UUID) -> User:
    """Return one directory entry by its ID."""
    user = directory.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/users", response_model=User, status_code=status.HTTP_201_CREATED, summary="Create a user")
def create_user(user_input: UserInput) -> User:
    """Add a new entry to the phone directory."""
    return directory.create_user(user_input)


@router.patch("/users/{user_id}", response_model=User, summary="Edit a user")
def edit_user(user_id: UUID, changes: UserUpdate) -> User:
    """Update the provided fields on an existing directory entry."""
    user = directory.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updates = changes.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide at least one field to update")
    if any(value is None for value in updates.values()):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Fields cannot be set to null")

    updated_user = directory.update_user(user_id, updates)
    if updated_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return updated_user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a user")
def delete_user(user_id: UUID) -> None:
    """Remove a directory entry."""
    if not directory.delete_user(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
