"""User management API routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role, hash_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserResponse
from app.schemas.common import MessageResponse
from app.utils.exceptions import NotFoundException

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=dict)
async def list_users(
    page: int = 1,
    page_size: int = 20,
    role: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    repo = UserRepository(db)
    users, total = await repo.get_all(
        skip=(page - 1) * page_size,
        limit=page_size,
        role=role,
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "users": [UserResponse.model_validate(u).model_dump() for u in users],
    }


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.sub != user_id and current_user.role != "admin":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Access denied")
    repo = UserRepository(db)
    user = await repo.get(user_id)
    if not user:
        raise NotFoundException("User", user_id)
    return user


@router.put("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: str,
    role: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    repo = UserRepository(db)
    user = await repo.update(user_id, role=role)
    return user


@router.delete("/{user_id}", response_model=MessageResponse)
async def deactivate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    repo = UserRepository(db)
    user = await repo.update(user_id, is_active=False)
    return {"message": "User deactivated", "detail": user_id}
