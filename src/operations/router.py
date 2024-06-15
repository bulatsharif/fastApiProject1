import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import redis
from fastapi import APIRouter, Depends, HTTPException, FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_session
from operations.models import operation
from operations.schemas import OperationCreate
from redis import asyncio as aioredis


router = APIRouter(
    prefix="/operations",
    tags=["Operation"],
)

# redis_client = redis.StrictRedis(host='localhost', port=6379, db = 0)
#
# @app.on_event("startup")
# async def startup():
#     FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
#
# # router unites certain set of endpoints

@router.get("/")
async def get_specific_operations(operation_type: str, session: AsyncSession = Depends(get_async_session)):
    try:
        query = select(operation).where(operation.c.type == operation_type)
        result = await session.execute(query)
        return {
            "status": "success",
            "data" : result.mappings().all(),
            "details" : None
        }
    except:
        raise HTTPException(status_code=500, detail= {
            "status": "error",
            "data" : None,
            "details" : None
        })

@router.get("/long-operation")
@cache(expire=30)
def get_long_op():
    time.sleep(2)
    return "Много данных"
# ORM - Object-relation model
# technology of working with database, way to transfer objects from python to database objects (tables)
# SQL Injection

# @router.post("/")
# async def add_specific_operations(new_operation: OperationCreate, session: AsyncSession = Depends(get_async_session)):
#     stmt = insert(operation).values(**new_operation.dict())
#     await session.execute(stmt)
#     await session.commit()
#     return {"status": "success"}

