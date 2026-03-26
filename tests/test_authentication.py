from typing import Generator

import pytest
from sqlalchemy import Column, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

from spa_sqladmin import Admin, BaseView, SimpleAuthBackend, action, expose
from spa_sqladmin.authentication import AuthenticationBackend
from spa_sqladmin.models import ModelView
from tests.common import sync_engine as engine

Base = declarative_base()  # type: Any
session_maker = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True)


class CustomBackend(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        if form["username"] != "a":
            return False

        request.session.update({"token": "amin"})
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        if "token" not in request.session:
            return False
        return True


class CustomAdmin(BaseView):
    @expose("/custom", methods=["GET"])
    async def custom(self, request: Request):
        return JSONResponse({"status": "ok"})


class MovieAdmin(ModelView, model=Movie):
    @action(name="test")
    async def test_page(self, request: Request):
        return JSONResponse({"status": "ok"})


app = Starlette()
authentication_backend = CustomBackend(secret_key="sqladmin")
admin = Admin(app=app, engine=engine, authentication_backend=authentication_backend)
admin.add_base_view(CustomAdmin)
admin.add_model_view(MovieAdmin)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app=app, base_url="http://testserver") as c:
        yield c


def test_access_login_required_api(client: TestClient) -> None:
    # API endpoints return 401 JSON when not authenticated
    response = client.get("/admin/api/site")
    assert response.status_code == 401


def test_login_failure(client: TestClient) -> None:
    response = client.post("/admin/api/login", data={"username": "x", "password": "b"})
    assert response.status_code == 401


def test_login(client: TestClient) -> None:
    response = client.post("/admin/api/login", data={"username": "a", "password": "b"})
    assert len(response.cookies) == 1
    assert response.status_code == 200
    assert response.json() == {"success": True}


def test_logout(client: TestClient) -> None:
    # Login first to get a session
    login_resp = client.post(
        "/admin/api/login", data={"username": "a", "password": "b"}
    )
    client.cookies = login_resp.cookies

    response = client.get("/admin/api/logout")
    assert response.status_code == 200
    assert response.json() == {"success": True}

    # After logout, API should return 401
    response = client.get("/admin/api/site")
    assert response.status_code == 401


def test_expose_access_login_required_views(client: TestClient) -> None:
    response = client.get("/admin/custom")
    # Without auth, expose view redirects to login page (SPA)
    assert response.status_code == 200

    login_resp = client.post(
        "/admin/api/login", data={"username": "a", "password": "b"}
    )
    client.cookies = login_resp.cookies

    response = client.get("/admin/custom")
    assert {"status": "ok"} == response.json()


def test_action_access_login_required_views(client: TestClient) -> None:
    response = client.get("/admin/movie/action/test")
    # Without auth, action redirects to login (SPA serves HTML)
    assert response.status_code == 200

    login_resp = client.post(
        "/admin/api/login", data={"username": "a", "password": "b"}
    )
    client.cookies = login_resp.cookies

    response = client.get("/admin/movie/action/test")
    assert {"status": "ok"} == response.json()


# ---------------------------------------------------------------------------
# SimpleAuthBackend tests
# ---------------------------------------------------------------------------

simple_app = Starlette()
simple_auth = SimpleAuthBackend(
    secret_key="simple-secret",
    credentials={"alice": "pw1", "bob": "pw2"},
)
simple_admin = Admin(
    app=simple_app, engine=engine, authentication_backend=simple_auth
)


@pytest.fixture
def simple_client() -> Generator[TestClient, None, None]:
    with TestClient(app=simple_app, base_url="http://testserver") as c:
        yield c


def test_simple_auth_login_success(simple_client: TestClient) -> None:
    response = simple_client.post(
        "/admin/api/login", data={"username": "alice", "password": "pw1"}
    )
    assert response.status_code == 200
    assert response.json() == {"success": True}
    assert len(response.cookies) == 1


def test_simple_auth_login_failure(simple_client: TestClient) -> None:
    response = simple_client.post(
        "/admin/api/login", data={"username": "alice", "password": "wrong"}
    )
    assert response.status_code == 401


def test_simple_auth_login_unknown_user(simple_client: TestClient) -> None:
    response = simple_client.post(
        "/admin/api/login", data={"username": "nobody", "password": "pw1"}
    )
    assert response.status_code == 401


def test_simple_auth_logout(simple_client: TestClient) -> None:
    login_resp = simple_client.post(
        "/admin/api/login", data={"username": "bob", "password": "pw2"}
    )
    simple_client.cookies = login_resp.cookies

    # Should be authenticated
    response = simple_client.get("/admin/api/auth-status")
    assert response.json()["authenticated"] is True

    simple_client.get("/admin/api/logout")

    response = simple_client.get("/admin/api/auth-status")
    assert response.json()["authenticated"] is False


def test_simple_auth_protected_api(simple_client: TestClient) -> None:
    response = simple_client.get("/admin/api/site")
    assert response.status_code == 401

    login_resp = simple_client.post(
        "/admin/api/login", data={"username": "alice", "password": "pw1"}
    )
    simple_client.cookies = login_resp.cookies

    response = simple_client.get("/admin/api/site")
    assert response.status_code == 200
