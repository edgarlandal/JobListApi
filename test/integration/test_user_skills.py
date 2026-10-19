from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models.skill import Skill, UserSkill


@pytest.mark.parametrize("offset, expected_count", [(0, 1), (1, 0)])
async def test_list_skills_only_counts_current_user_assignments(
    client, db_session, test_user, admin_user, user_token, offset, expected_count
):
    skill = Skill(name="Python", slug="python")
    db_session.add(skill)
    await db_session.flush()
    db_session.add_all([
        UserSkill(user_id=test_user.id, skill_id=skill.id, level=2),
        UserSkill(user_id=admin_user.id, skill_id=skill.id, level=1),
    ])
    await db_session.commit()

    response = await client.get(
        "/api/v1/users/me/skills",
        params={"limit": 1, "offset": offset},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["limit"] == 1
    assert data["offset"] == offset
    assert len(data["items"]) == expected_count
    if expected_count:
        assert data["items"][0]["skill"]["id"] == str(skill.id)
        assert data["items"][0]["level"] == 2


@pytest.mark.parametrize("token_fixture", ["user_token", "admin_token"])
async def test_remove_skill_only_deletes_current_user_assignment(
    client, db_session, test_user, admin_user, request, token_fixture
):
    token = request.getfixturevalue(token_fixture)
    actor = test_user if token_fixture == "user_token" else admin_user
    other = admin_user if token_fixture == "user_token" else test_user
    skill = Skill(name="Python", slug="python")
    db_session.add(skill)
    await db_session.flush()
    db_session.add_all([
        UserSkill(user_id=actor.id, skill_id=skill.id, level=2),
        UserSkill(user_id=other.id, skill_id=skill.id, level=1),
    ])
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/users/me/{skill.id}/skills",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    assert response.content == b""
    remaining = (await db_session.execute(
        select(UserSkill.user_id).where(UserSkill.skill_id == skill.id)
    )).scalars().all()
    assert remaining == [other.id]
    assert await db_session.scalar(select(Skill.id).where(Skill.id == skill.id)) == skill.id
    assert await db_session.scalar(select(actor.__class__.id).where(
        actor.__class__.id == actor.id
    )) == actor.id

    repeated = await client.delete(
        f"/api/v1/users/me/{skill.id}/skills",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert repeated.status_code == 404


async def test_remove_skill_cannot_delete_another_users_assignment(
    client, db_session, user_token, admin_user
):
    skill = Skill(name="Python", slug="python")
    db_session.add(skill)
    await db_session.flush()
    db_session.add(UserSkill(user_id=admin_user.id, skill_id=skill.id, level=2))
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/users/me/{skill.id}/skills",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 404
    assert await db_session.scalar(select(UserSkill.user_id).where(
        UserSkill.skill_id == skill.id
    )) == admin_user.id


async def test_remove_missing_skill(client, user_token):
    response = await client.delete(
        f"/api/v1/users/me/{uuid4()}/skills",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 404


async def test_remove_skill_rejects_invalid_uuid(client, user_token):
    response = await client.delete(
        "/api/v1/users/me/invalid-id/skills",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 422


async def test_add_skill_still_rejects_duplicate_assignment(client, db_session, user_token):
    skill = Skill(name="Python", slug="python")
    db_session.add(skill)
    await db_session.commit()
    payload = {"skill_id": str(skill.id), "level": 2}
    headers = {"Authorization": f"Bearer {user_token}"}

    created = await client.post("/api/v1/users/me/skills", json=payload, headers=headers)
    assert created.status_code == 201
    duplicate = await client.post("/api/v1/users/me/skills", json=payload, headers=headers)
    assert duplicate.status_code == 409


async def test_add_skill_requires_catalog_entry(client, user_token):
    response = await client.post(
        "/api/v1/users/me/skills",
        json={"skill_id": str(uuid4()), "level": 2},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 404


@pytest.mark.parametrize("payload, expected_level", [({"level": 3}, 3), ({}, 1)])
async def test_update_skill_only_changes_current_user_assignment(
    client, db_session, test_user, admin_user, user_token, payload, expected_level
):
    skill = Skill(name="Python", slug="python")
    db_session.add(skill)
    await db_session.flush()
    db_session.add_all([
        UserSkill(user_id=test_user.id, skill_id=skill.id, level=1),
        UserSkill(user_id=admin_user.id, skill_id=skill.id, level=2),
    ])
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/users/me/{skill.id}/skills",
        json=payload,
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 202
    assert response.json()["level"] == expected_level
    assert response.json()["skill"]["id"] == str(skill.id)
    levels = dict((await db_session.execute(
        select(UserSkill.user_id, UserSkill.level).where(UserSkill.skill_id == skill.id)
    )).all())
    assert levels == {test_user.id: expected_level, admin_user.id: 2}


async def test_update_skill_cannot_change_another_users_assignment(
    client, db_session, admin_user, user_token
):
    skill = Skill(name="Python", slug="python")
    db_session.add(skill)
    await db_session.flush()
    db_session.add(UserSkill(user_id=admin_user.id, skill_id=skill.id, level=1))
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/users/me/{skill.id}/skills",
        json={"level": 3},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 404
    assert await db_session.scalar(select(UserSkill.level).where(
        UserSkill.user_id == admin_user.id, UserSkill.skill_id == skill.id
    )) == 1


@pytest.mark.parametrize("level", [0, 4, None])
async def test_update_skill_rejects_invalid_level(client, user_token, level):
    response = await client.patch(
        f"/api/v1/users/me/{uuid4()}/skills",
        json={"level": level},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 422
