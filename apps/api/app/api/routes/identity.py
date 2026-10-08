from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, CurrentUserDep, require_permission
from app.core.tokens import decode_token
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
UserReadDep = Annotated[CurrentUser, Depends(require_permission("identity.user.read"))]
UserManageDep = Annotated[CurrentUser, Depends(require_permission("identity.user.manage"))]


@router.get("/users", response_model=Page[UserRead], summary="用户列表")
async def list_users(
    session: SessionDep,
    actor: UserReadDep,
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
        data_scope=actor.data_scope,
    )


@router.post(
    "/users",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建用户",
)
async def create_user(payload: UserCreate, session: SessionDep, actor: UserManageDep) -> User:
    return await service.create_user(session, payload, data_scope=actor.data_scope)


@router.get("/users/{user_id}", response_model=UserRead, summary="用户详情")
async def get_user(user_id: UUID, session: SessionDep, actor: UserReadDep) -> User:
    return await service.get_user(session, user_id, data_scope=actor.data_scope)


@router.patch("/users/{user_id}", response_model=UserRead, summary="更新用户")
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    session: SessionDep,
    actor: UserManageDep,
    request: Request,
) -> User:
    entity = await service.update_user(
        session, user_id, payload, data_scope=actor.data_scope
    )
    if payload.is_active is False:
        request.state.security_event_type = "auth.sessions_revoked"
        request.state.security_event_category = "session"
        request.state.security_event_severity = "warning"
        request.state.audit_subject = str(user_id)
    return entity


@router.post(
    "/users/{user_id}/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="重置用户密码",
)
async def change_password(
    user_id: UUID,
    payload: PasswordChange,
    session: SessionDep,
    actor: UserManageDep,
    request: Request,
) -> Response:
    await service.change_password(
        session,
        user_id,
        payload.new_password,
        data_scope=actor.data_scope,
    )
    request.state.security_event_type = "auth.sessions_revoked"
    request.state.security_event_category = "session"
    request.state.security_event_severity = "warning"
    request.state.audit_subject = str(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/auth/login", response_model=LoginResponse, summary="登录并签发访问令牌")
async def login(payload: LoginRequest, session: SessionDep, request: Request) -> LoginResponse:
    request.state.audit_subject = payload.username.strip().lower()
    response = await auth_service.login(session, payload)
    claims = decode_token(response.access_token, expected_type="access")
    request.state.actor_user_id = response.user.id
    request.state.organization_id = response.user.organization_id
    request.state.auth_session_id = claims.session_id
    return response


@router.post("/auth/refresh", response_model=TokenPairResponse, summary="轮换刷新令牌")
async def refresh(
    payload: RefreshRequest,
    session: SessionDep,
    request: Request,
) -> TokenPairResponse:
    response = await auth_service.refresh(session, payload.refresh_token)
    claims = decode_token(response.access_token, expected_type="access")
    request.state.actor_user_id = response.user.id
    request.state.organization_id = response.user.organization_id
    request.state.auth_session_id = claims.session_id
    return response


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
        role_codes=sorted(current_user.role_codes),
        permission_codes=sorted(current_user.permission_codes),
        data_scope_type=current_user.data_scope.scope_type,
        data_scope_source=current_user.data_scope.source,
        user=UserRead.model_validate(user),
    )


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT, summary="注销当前会话")
async def logout(current_user: CurrentUserDep, session: SessionDep) -> Response:
    await auth_service.revoke_session(session, current_user.session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
