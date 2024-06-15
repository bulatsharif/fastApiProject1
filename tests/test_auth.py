import pytest
from sqlalchemy import insert, select

from src.auth.models import roles
from conftest import client, async_session_maker

async def test_add_role():
    async with async_session_maker() as session:
        stmt = insert(roles).values(id=1, name="admin",permissions=None)
        await session.execute(stmt)
        await session.commit()

        query = select(roles)
        result = await session.execute(query)
        print(result.all())

def test_register():
    client.post("/auth/registe", json={
        "email": "string",
        "password": "string",
        "is_active": True,
        "is_superuser": False,
        "is_verified": False,
        "username": "string",
        "role_id": 0,
    })