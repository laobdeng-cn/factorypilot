from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.user import User
from app.schemas.enterprise import Page
from app.schemas.identity import (
    LoginRequest,
    LoginResponse,
    PasswordChange,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.services import identity as service

router = APIRouter()
SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
PageParam = Annotated[int, Query(ge=1)]
PageSizeParam = Annotated[int, Query(ge=1, le=100)]


@router.get("/users", response_model=Page[UserRead], summary="用户列表")
async def list_users(
    session: SessionDep,
    page: PageParam = 1,
    page_size: PageSizeParam = 20,
    organization_id: UUID | None = None,
    department_id: UUID | None = None,
    primary_plant_id: UUID | None = None,
    is_active: bool | None = None,
    q: str | None = None,
) -> Page[UserRead]:
    return await service.list_users(
        session,
        page=page,
        page_size=page_size,
        organization_id=organization_id,
        department_id=department_id,
        primary_plant_id=primary_plant_id,
        is_active=is_active,
        q=q,
    )


@router.post(
    "/users",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建用户",
)
async def create_user(payload: UserCreate, session: SessionDep) -> User:
    return await service.create_user(session, payload)


@router.get("/users/{user_id}", response_model=UserRead, summary="用户详情")
async def get_user(user_id: UUID, session: SessionDep) -> User:
    return await service.get_user(session, user_id)


@router.patch("/users/{user_id}", response_model=UserRead, summary="更新用户")
async def update_user(user_id: UUID, payload: UserUpdate, session: SessionDep) -> User:
    return await service.update_user(session, user_id, payload)


@router.post(
    "/users/{user_id}/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="重置用户密码",
)
async def change_password(
    user_id: UUID, payload: PasswordChange, session: SessionDep
) -> Response:
    await service.change_password(session, user_id, payload.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/auth/login", response_model=LoginResponse, summary="校验用户名和密码")
async def login(payload: LoginRequest, session: SessionDep) -> LoginResponse:
    return await service.authenticate_user(session, payload)
