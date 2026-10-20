import pytest

from app.models.user import UserRole
from app.schemas.pagination import PaginationParams


PROTECTED_ENDPOINTS = [
    ("GET", "/api/v1/admin"), ("POST", "/api/v1/admin"),
    ("GET", "/api/v1/admin/{id}"), ("PATCH", "/api/v1/admin/{id}"),
    ("DELETE", "/api/v1/admin/{id}"),
    ("GET", "/api/v1/users/me"), ("PATCH", "/api/v1/users/me"),
    ("DELETE", "/api/v1/users/me"),
    ("GET", "/api/v1/jobs"), ("POST", "/api/v1/jobs"),
    ("GET", "/api/v1/jobs/{id}"), ("PATCH", "/api/v1/jobs/{id}"),
    ("DELETE", "/api/v1/jobs/{id}"),
]


@pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
@pytest.mark.parametrize("access,expected", [("anonymous", 401), ("inactive", 400)])
async def test_protected_endpoints(route_client, route_context, method, path, access, expected):
    if access == "anonymous":
        route_client.headers.pop("Authorization")
    else:
        route_context.actor.is_active = False
    response = await route_client.request(method, path.format(id=route_context.target.id), json={})
    assert response.status_code == expected
    assert route_context.user_service.mock_calls == []
    assert route_context.job_service.mock_calls == []


@pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS[:8])
async def test_wrong_role_is_forbidden(route_client, route_context, method, path):
    route_context.actor.role = UserRole.USER if "/admin" in path else UserRole.ADMIN
    response = await route_client.request(method, path.format(id=route_context.target.id), json={})
    assert response.status_code == 403
    assert route_context.user_service.mock_calls == []


@pytest.mark.parametrize("path,service_name,method", [
    ("/api/v1/admin", "user_service", "get_users"),
    ("/api/v1/jobs", "job_service", "get_jobs"),
])
async def test_default_pagination_and_empty_result(route_client, route_context, path, service_name, method):
    service_method = getattr(getattr(route_context, service_name), method)
    service_method.return_value = {"items": [], "total": 0, "limit": 20, "offset": 0}
    response = await route_client.get(path)
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 20, "offset": 0}
    service_method.assert_awaited_once_with(PaginationParams())


@pytest.mark.parametrize("path", ["/api/v1/admin", "/api/v1/jobs"])
@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1", "limit=invalid"])
async def test_invalid_pagination(route_client, route_context, path, query):
    response = await route_client.get(f"{path}?{query}")
    assert response.status_code == 422
    assert route_context.user_service.mock_calls == []
    assert route_context.job_service.mock_calls == []
