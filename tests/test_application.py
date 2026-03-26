from typing import Generator

import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from starlette.applications import Starlette
from starlette.datastructures import MutableHeaders
from starlette.middleware import Middleware
from starlette.testclient import TestClient
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from spa_sqladmin import Admin, ModelView
from tests.common import sync_engine as engine

Base = declarative_base()  # type: ignore


class DataModel(Base):
    __tablename__ = "datamodel"
    id = Column(Integer, primary_key=True)
    data = Column(String)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(32), default="SQLAdmin")


@pytest.fixture(autouse=True)
def prepare_database() -> Generator[None, None, None]:
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


def test_application_title() -> None:
    app = Starlette()
    Admin(app=app, engine=engine)

    with TestClient(app) as client:
        response = client.get("/admin")

    assert response.status_code == 200
    # SPA serves index.html with admin config injected
    assert "__ADMIN_CONFIG__" in response.text
    assert "root" in response.text


def test_application_logo() -> None:
    app = Starlette()
    Admin(
        app=app,
        engine=engine,
        logo_url="https://example.com/logo.svg",
        base_url="/dashboard",
    )

    with TestClient(app) as client:
        response = client.get("/dashboard")

    assert response.status_code == 200
    # SPA serves index.html with config (logo is in site API, not in HTML)
    assert "__ADMIN_CONFIG__" in response.text


def test_middlewares() -> None:
    class CorrelationIdMiddleware:
        def __init__(self, app: ASGIApp) -> None:
            self.app = app

        async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
            async def send_wrapper(message: Message) -> None:
                if message["type"] == "http.response.start":
                    headers = MutableHeaders(scope=message)
                    headers.append("X-Correlation-ID", "UUID")
                await send(message)

            await self.app(scope, receive, send_wrapper)

    app = Starlette()
    Admin(
        app=app,
        engine=engine,
        middlewares=[Middleware(CorrelationIdMiddleware)],
    )

    with TestClient(app) as client:
        response = client.get("/admin")

    assert response.status_code == 200
    assert "x-correlation-id" in response.headers



def test_build_category_menu():
    app = Starlette()
    admin = Admin(app=app, engine=engine)

    class UserAdmin(ModelView, model=User):
        category = "Accounts"

    admin.add_view(UserAdmin)

    admin._menu.items.pop().name = "Accounts"


def test_normalize_wtform_fields() -> None:
    app = Starlette()
    admin = Admin(app=app, engine=engine)

    class DataModelAdmin(ModelView, model=DataModel): ...

    datamodel = DataModel(id=1, data="abcdef")
    admin.add_view(DataModelAdmin)
    assert admin._normalize_wtform_data(datamodel) == {"data_": "abcdef"}


def test_denormalize_wtform_fields() -> None:
    app = Starlette()
    admin = Admin(app=app, engine=engine)

    class DataModelAdmin(ModelView, model=DataModel): ...

    datamodel = DataModel(id=1, data="abcdef")
    admin.add_view(DataModelAdmin)
    assert admin._denormalize_wtform_data({"data_": "abcdef"}, datamodel) == {
        "data": "abcdef"
    }


def test_validate_page_and_page_size():
    app = Starlette()
    admin = Admin(app=app, engine=engine)

    class UserAdmin(ModelView, model=User): ...

    admin.add_view(UserAdmin)

    client = TestClient(app)

    response = client.get("/admin/api/user/list?page=10000")
    assert response.status_code == 200

    response = client.get("/admin/api/user/list?page=aaaa")
    assert response.status_code == 400



