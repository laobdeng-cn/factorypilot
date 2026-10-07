from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUserDep
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.enterprise import Page
from app.schemas.identity import (
    CurrentUserResponse,
    LoginRequest,
    LoginResponse,
    PasswordChange,
    RefreshRequest,
    TokenPairResponse,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.services import auth as auth_service
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


@router.post("/auth/login", response_model=LoginResponse, summary="登录并签发访问令牌")
async def login(payload: LoginRequest, session: SessionDep) -> LoginResponse:
    return await auth_service.login(session, payload)


@router.post("/auth/refresh", response_model=TokenPairResponse, summary="轮换刷新令牌")
async def refresh(payload: RefreshRequest, session: SessionDep) -> TokenPairResponse:
    return await auth_service.refresh(session, payload.refresh_token)


@router.get("/auth/me", response_model=CurrentUserResponse, summary="当前登录用户")
async def me(current_user: CurrentUserDep) -> CurrentUserResponse:
    user = current_user.user
    return CurrentUserResponse(
        session_id=current_user.session_id,
        user_id=current_user.user_id,
        organization_id=current_user.organization_id,
        department_id=current_user.department_id,
        primary_plant_id=current_user.primary_plant_id,
        username=user.username,
        display_name=user.display_name,
        user=UserRead.model_validate(user),
    )


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT, summary="注销当前会话")
async def logout(current_user: CurrentUserDep, session: SessionDep) -> Response:
    await auth_service.revoke_session(session, current_user.session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
