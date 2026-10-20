"""Isolated HTTP tests for the jobs CRUD router."""

import pytest
from fastapi import HTTPException

from app.models.user import UserRole
from app.schemas.job import JobCreate, JobUpdate
from app.schemas.pagination import PaginationParams


@pytest.fixture(autouse=True, params=[UserRole.USER, UserRole.ADMIN])
def allowed_role(route_context, request):
    route_context.actor.role = request.param


async def test_create_job_uses_authenticated_owner(route_client, route_context, job_payload):
    response = await route_client.post("/api/v1/jobs", json=job_payload)
    assert response.status_code == 201
    assert response.json()["id"] == str(route_context.job.id)
    assert response.json()["enterprise"] == job_payload["enterprise"]
    route_context.job_service.create_job.assert_awaited_once_with(
        JobCreate(**job_payload), route_context.actor.id
    )


async def test_list_jobs(route_client, route_context):
    route_context.job_service.get_jobs.return_value = {
        "items": [route_context.job], "total": 6, "limit": 2, "offset": 4,
    }
    response = await route_client.get("/api/v1/jobs?limit=2&offset=4")
    assert response.status_code == 200
    data = response.json()
    assert (data["total"], data["limit"], data["offset"]) == (6, 2, 4)
    assert data["items"][0]["id"] == str(route_context.job.id)
    route_context.job_service.get_jobs.assert_awaited_once_with(PaginationParams(limit=2, offset=4))


async def test_get_job(route_client, route_context):
    job_id = str(route_context.job.id)
    response = await route_client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 200
    assert response.json()["id"] == job_id
    route_context.job_service.get_job_by_id.assert_awaited_once_with(job_id)


async def test_update_job(route_client, route_context, job_payload):
    payload = {**job_payload, "notes": "Interview scheduled"}
    route_context.job.notes = payload["notes"]
    job_id = str(route_context.job.id)
    response = await route_client.patch(f"/api/v1/jobs/{job_id}", json=payload)
    assert response.status_code == 200
    assert response.json()["notes"] == payload["notes"]
    route_context.job_service.update_job.assert_awaited_once_with(
        job_id=job_id, job_in=JobUpdate(**payload)
    )


async def test_delete_job(route_client, route_context):
    job_id = str(route_context.job.id)
    response = await route_client.delete(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 204
    assert response.content == b""
    route_context.job_service.get_job_by_id.assert_awaited_once_with(job_id)
    route_context.job_service.delete_job.assert_awaited_once_with(job_id)


@pytest.mark.parametrize("method,service_method", [
    ("GET", "get_job_by_id"), ("PATCH", "update_job"), ("DELETE", "get_job_by_id"),
])
async def test_missing_job(route_client, route_context, job_payload, method, service_method):
    getattr(route_context.job_service, service_method).side_effect = HTTPException(404, "Job not found")
    kwargs = {"json": job_payload} if method == "PATCH" else {}
    response = await route_client.request(method, f"/api/v1/jobs/{route_context.job.id}", **kwargs)
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"
    route_context.job_service.delete_job.assert_not_awaited()


@pytest.mark.parametrize("invalid", [{"mode": "invalid"}, {"salary": "invalid"}, {"status_job": "invalid"}])
async def test_invalid_creation(route_client, route_context, job_payload, invalid):
    response = await route_client.post("/api/v1/jobs", json={**job_payload, **invalid})
    assert response.status_code == 422
    route_context.job_service.create_job.assert_not_awaited()


async def test_update_requires_all_current_schema_fields(route_client, route_context):
    response = await route_client.patch(
        f"/api/v1/jobs/{route_context.job.id}", json={"notes": "Interview scheduled"}
    )
    assert response.status_code == 422
    route_context.job_service.update_job.assert_not_awaited()
