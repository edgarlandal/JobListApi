from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Annotated
from unittest.mock import create_autospec
from uuid import UUID

import pytest
import pytest_asyncio
from fastapi import Depends
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import (
    get_async_db, get_current_user, get_job_service, get_user_service, oauth_scheme,
)
from app.main import create_app
from app.models.user import UserRole
from app.services.job import JobService
from app.services.user import UserService


@pytest.fixture
def user_payload():
    return {
        "email": "new@example.com", "password": "Password123!",
        "firstname": "New", "lastname": "User",
    }


@pytest.fixture
def job_payload():
    return {
        "enterprise": "Example", "role": "Backend developer", "salary": 50000,
        "type_salary": "Yearly", "mode": "Remote", "location": "Tijuana",
        "status_job": "Send", "notes": "Applied online",
        "last_update_at": "2026-10-19T12:00:00Z",
    }


@pytest.fixture
def route_context(job_payload):
    actor = SimpleNamespace(
        id=UUID("11111111-1111-4111-8111-111111111111"),
        email="actor@example.com", firstname="Actor", lastname="User",
        role=UserRole.ADMIN, is_active=True, is_verified=False,
        created_at=datetime(2026, 10, 19, tzinfo=timezone.utc), last_login_at=None,
        hashed_password="must-not-appear-in-responses",
    )
    target = SimpleNamespace(**{
        **vars(actor), "id": UUID("22222222-2222-4222-8222-222222222222"),
        "email": "new@example.com", "firstname": "New", "role": UserRole.USER,
    })
    job = SimpleNamespace(
        **job_payload, id=UUID("33333333-3333-4333-8333-333333333333")
    )
    user_service = create_autospec(UserService, instance=True, spec_set=True)
    job_service = create_autospec(JobService, instance=True, spec_set=True)
    for name in ("register_user", "get_user_by_id", "admin_update_user", "update_my_profile"):
        getattr(user_service, name).return_value = target
    for name in ("create_job", "get_job_by_id", "update_job"):
        getattr(job_service, name).return_value = job
    user_service.delete_user.return_value = None
    job_service.delete_job.return_value = None

    app = create_app()
    app.state.limiter.reset()

    async def current_user(token: Annotated[str, Depends(oauth_scheme)]):
        # Keep the real Bearer requirement, active-user check, and RoleChecker.
        # JWT decoding and database lookup belong to the authentication tests.
        return actor

    async def forbid_database():
        raise AssertionError("Endpoint unit tests must not access the database")

    app.dependency_overrides.update({
        get_current_user: current_user,
        get_user_service: lambda: user_service,
        get_job_service: lambda: job_service,
        get_async_db: forbid_database,
    })
    try:
        yield SimpleNamespace(
            app=app, actor=actor, target=target, job=job,
            user_service=user_service, job_service=job_service,
        )
    finally:
        app.dependency_overrides.clear()
        app.state.limiter.reset()


@pytest_asyncio.fixture
async def route_client(route_context):
    async with AsyncClient(
        transport=ASGITransport(app=route_context.app), base_url="http://test",
        headers={"Authorization": "Bearer unit-test-token"},
    ) as client:
        yield client
