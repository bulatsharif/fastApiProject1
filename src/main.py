from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from typing import List, Optional

from fastapi import FastAPI, Request, status, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import ValidationException
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_users import FastAPIUsers
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from auth.auth import auth_backend
from auth.manager import get_user_manager
from auth.schemas import UserRead, UserCreate
from operations.router import router as router_operation
from redis import asyncio as aioredis

from config import REDIS_HOST, REDIS_PORT
from tasks.router import router as router_tasks
from tasks.router import get_dashboard_report
from pages.router import router as router_pages
from chat.router import router as router_chat

app = FastAPI(
    title="Trading APP"
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup():
   redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}", encoding="utf8", decode_responses=True)
   FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")



@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail" : exc.errors()}),
    )

fake_users = [
    {"id": 1, "role": "admin", "name": "Bob"},
    {"id": 2, "role": "investor", "name": "John"},
    {"id": 3, "role": "trader", "name": "Matt"},
    {"id": 4, "role": "admin", "name": "Alice", "degree": [{"id" : 1, "created_at" : "2020-01-01T00:00:00",
                                                            "type_degree" : "expert"}]},
]

origins = [
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers = ["Content-Type", "Authorization", "Set-Cookie", "Access-Control-Allow-Headers", "Access-Control-Allow-Origin"],
)

# parameters are strings by default

class DegreeType(Enum):
    newbie = "newbie"
    expert = "expert"

class Degree(BaseModel):
    id: int
    created_at: datetime
    type_degree: DegreeType


class User(BaseModel):
    id: int
    role: str
    name: str
    degree: Optional[List[Degree]] = []

# response_model is used for validating the information that we send to the user
@app.get("/users/{user_id}", response_model=List[User])
def get_user(user_id: int):
    return [user for user in fake_users if user.get("id") == user_id]


fake_trades = [
    {"id": 1, "user_id": 1, "currency": "BTC", "side": "buy", "price": 123, "amount": 2.12},
    {"id": 2, "user_id": 1, "currency": "BTC", "side": "sell", "price": 125, "amount": 2.12}
]


# model type - pydantic

class Trade(BaseModel):
    id: int
    user_id: int
    currency: str = Field(max_length = 5)
    side: str
    price: float = Field(ge=0) #some conditions required for the request
    amount: float


@app.post("/trades")
def add_trades(trades: List[Trade]):
    fake_trades.extend(trades)
    return {"status" : 200, "data": fake_trades}

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(router_tasks)

app.include_router(router_operation)
app.include_router(router_pages)
app.include_router(router_chat)
# here we are using query requests, which are not the same as path requests
# In FastAPI, if you define parameters in your endpoint function that are not part of the path,
# they are automatically interpreted as query parameters.
# Query parameters are part of the URL following the ? symbol and are typically used to filter or paginate results.

# Request: GET /trades?limit=1&offset=0
#
# Explanation: This request asks for 1 trade starting from the first trade in the list.
# Result: [{"id" : 1, "user_id" : 1, "currency" : "BTC", "side" : "buy", "price" : 123, "amount" : 2.12}]
# Request: GET /trades?limit=1&offset=1
#
# Explanation: This request asks for 1 trade starting from the second trade in the list.
# Result: [{"id": 2, "user_id" : 1, "currency" : "BTC", "side" : "sell", "price" : 125, "amount" : 2.12}]

# @app.get("/trades")
# def get_trades(limit: int = 1, offset: int = 0):
#     return fake_trades[offset:][:limit]
#
# # the returned element is always converted to json
#
# fake_users2 = [
#     {"id": 1, "role": "admin", "name": "Bob"},
#     {"id": 2, "role": "investor", "name": "John"},
#     {"id": 3, "role": "trader", "name": "Matt"},
# ]
#
# @app.post("/users/{user_id}")
# def change_user_name(user_id: int, new_name: str):
#     current_user = list(filter(lambda user: user.get("id") == user_id, fake_users2))[0]
#     current_user["name"] = new_name
#     return {"status" : 200, "data" : current_user}
#

current_active_user = fastapi_users.current_user(active=True)

@app.get("/protected-route")
def protected_route(user: User = Depends(current_active_user)):
    return f"Hello, {user.username}"

@app.get("/unprotected-route")
def protected_route():
    return f"Hello, anonym"
