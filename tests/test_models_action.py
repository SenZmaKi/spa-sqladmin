from typing import Any, Generator, List
from unittest.mock import Mock

import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.testclient import TestClient

from spa_sqladmin import Admin, ModelView
from spa_sqladmin.application import action
from spa_sqladmin.filters import AllUniqueStringValuesFilter, OperationColumnFilter
from tests.common import sync_engine as engine

Base: Any = declarative_base()

Session = sessionmaker(bind=engine)

app = Starlette()
admin = Admin(app=app, engine=engine)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, default="user")

    def __repr__(self) -> str:
        return f"User: {self.id}"


class UserAdmin(ModelView, model=User):
    column_filters = [
        OperationColumnFilter(User.name),
        AllUniqueStringValuesFilter(User.name, parameter_name="simple_name"),
    ]
    column_list = [User.id, User.name]

    async def _action_stub(self, request: Request) -> Response:
        pks = request.query_params.get("pks", "")

        obj_strs: List[str] = []

        class RequestObject(object):
            pass

        for pk in pks.split(","):
            request_object = RequestObject()
            request_object.path_params = {"pk": pk}
            obj = await self.get_object_for_edit(request_object)

            obj_strs.append(repr(obj))

        response = RedirectResponse(
            request.url_for("admin:list", identity=self.identity)
        )
        response.headers["X-Objs"] = ",".join(obj_strs)
        return response

    @action(name="details", add_in_detail=True, add_in_list=False)
    async def action_details(self, request: Request) -> Response:
        return await self._action_stub(request)  # pragma: no cover

    @action(name="list", add_in_detail=False, add_in_list=True)
    async def action_list(self, request: Request) -> Response:
        return await self._action_stub(request)  # pragma: no cover

    @action(name="details_list", add_in_detail=True, add_in_list=True)
    async def action_details_list(self, request: Request) -> Response:
        return await self._action_stub(request)  # pragma: no cover

    @action(
        name="details_confirm",
        confirmation_message="!Details Confirm?!",
        add_in_detail=True,
        add_in_list=False,
    )
    async def action_details_confirm(self, request: Request) -> Response:
        return await self._action_stub(request)  # pragma: no cover

    @action(
        name="list_confirm",
        confirmation_message="!List Confirm?!",
        add_in_detail=False,
        add_in_list=True,
    )
    async def action_list_confirm(self, request: Request) -> Response:
        return await self._action_stub(request)  # pragma: no cover

    @action(
        name="details_list_confirm",
        confirmation_message="!Details List Confirm?!",
        add_in_detail=True,
        add_in_list=True,
    )
    async def action_details_list_confirm(self, request: Request) -> Response:
        return await self._action_stub(request)  # pragma: no cover

    @action(
        name="label_details",
        label="Label Details",
        add_in_detail=True,
        add_in_list=False,
    )
    async def action_label_details(self, request: Request) -> Response:
        return await self._action_stub(request)  # pragma: no cover

    @action(
        name="label_list", label="Label List", add_in_detail=False, add_in_list=True
    )
    async def action_label_list(self, request: Request) -> Response:
        return await self._action_stub(request)  # pragma: no cover

    @action(
        name="label_details_list",
        label="Label Details List",
        add_in_detail=True,
        add_in_list=True,
    )
    async def action_label_details_list(self, request: Request) -> Response:
        return await self._action_stub(request)  # pragma: no cover

    @action(
        name="label_details_confirm",
        label="Label Details Confirm",
        confirmation_message="!Label Details Confirm?!",
        add_in_detail=True,
        add_in_list=False,
    )
    async def action_label_details_confirm(self, request: Request) -> Response:
        return await self._action_stub(request)  # pragma: no cover

    @action(
        name="label_list_confirm",
        label="Label List Confirm",
        confirmation_message="!Label List Confirm?!",
        add_in_detail=False,
        add_in_list=True,
    )
    async def action_label_list_confirm(self, request: Request) -> Response:
        return await self._action_stub(request)  # pragma: no cover

    @action(
        name="label_details_list_confirm",
        label="Label Details List Confirm",
        confirmation_message="!Label Details List Confirm?!",
        add_in_detail=True,
        add_in_list=True,
    )
    async def action_label_details_list_confirm(self, request: Request) -> Response:
        return await self._action_stub(request)  # pragma: no cover


@pytest.fixture(autouse=True)
def prepare_database() -> Generator[None, None, None]:
    Base.metadata.create_all(engine)
    # Add UserAdmin only once
    if not admin.views:
        admin.add_view(UserAdmin)

    yield

    Base.metadata.drop_all(engine)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app=app, base_url="http://testserver") as c:
        yield c


def test_model_action(client: TestClient) -> None:
    assert admin.views[0]._custom_actions_in_list == {
        "list": "list",
        "details-list": "details_list",
        "label-list": "Label List",
        "label-details-list": "Label Details List",
        "list-confirm": "list_confirm",
        "details-list-confirm": "details_list_confirm",
        "label-list-confirm": "Label List Confirm",
        "label-details-list-confirm": "Label Details List Confirm",
    }

    assert admin.views[0]._custom_actions_in_detail == {
        "details": "details",
        "details-confirm": "details_confirm",
        "details-list": "details_list",
        "details-list-confirm": "details_list_confirm",
        "label-details": "Label Details",
        "label-details-confirm": "Label Details Confirm",
        "label-details-list": "Label Details List",
        "label-details-list-confirm": "Label Details List Confirm",
    }

    assert admin.views[0]._custom_actions_confirmation == {
        "details-confirm": "!Details Confirm?!",
        "details-list-confirm": "!Details List Confirm?!",
        "label-details-confirm": "!Label Details Confirm?!",
        "label-details-list-confirm": "!Label Details List Confirm?!",
        "label-list-confirm": "!Label List Confirm?!",
        "list-confirm": "!List Confirm?!",
    }

    request = Mock(Request)
    request.url_for = Mock()

    admin.views[0]._url_for_action(request, "test")
    request.url_for.assert_called_with("admin:action-user-test")

    with Session() as session:
        user1 = User()
        user2 = User()
        session.add(user1)
        session.add(user2)
        session.commit()

        response = client.get(
            f"/admin/user/action/details?pks={user1.id},{user2.id}",
            follow_redirects=False,
        )
        assert response.status_code == 307
        assert f"User: {user1.id}" in response.headers["X-Objs"]
        assert f"User: {user2.id}" in response.headers["X-Objs"]

        response = client.get("/admin/api/user/list")
        assert response.status_code == 200
        data = response.json()
        actions_in_list = data["actions_in_list"]
        action_confirmations = data["action_confirmations"]
        # List-only and list+detail actions should be in actions_in_list
        assert "list-confirm" in actions_in_list
        assert "details-list-confirm" in actions_in_list
        assert "label-list-confirm" in actions_in_list
        assert "label-details-list-confirm" in actions_in_list
        # Detail-only actions should NOT be in actions_in_list
        assert "details-confirm" not in actions_in_list
        assert "label-details-confirm" not in actions_in_list
        # Confirmation messages for list actions should be present
        assert action_confirmations["list-confirm"] == "!List Confirm?!"
        assert action_confirmations["details-list-confirm"] == "!Details List Confirm?!"
        assert action_confirmations["label-list-confirm"] == "!Label List Confirm?!"
        assert action_confirmations["label-details-list-confirm"] == "!Label Details List Confirm?!"

        response = client.get(f"/admin/api/user/detail/{user1.id}")
        assert response.status_code == 200
        data = response.json()
        actions_in_detail = data["actions"]
        action_confirmations = data["action_confirmations"]
        # Detail-only and list+detail actions should be in actions_in_detail
        assert "details-confirm" in actions_in_detail
        assert "details-list-confirm" in actions_in_detail
        assert "label-details-confirm" in actions_in_detail
        assert "label-details-list-confirm" in actions_in_detail
        # List-only actions should NOT be in actions_in_detail
        assert "list-confirm" not in actions_in_detail
        assert "label-list-confirm" not in actions_in_detail
        # Confirmation messages for detail actions should be present
        assert action_confirmations["details-confirm"] == "!Details Confirm?!"
        assert action_confirmations["details-list-confirm"] == "!Details List Confirm?!"
        assert action_confirmations["label-details-confirm"] == "!Label Details Confirm?!"
        assert action_confirmations["label-details-list-confirm"] == "!Label Details List Confirm?!"


def test_filter_processing_has_operator(client: TestClient) -> None:
    """Test that ModelView correctly processes filters with has_operator attribute"""
    with Session() as session:
        batman = User(name="batman")
        superman = User(name="superman")
        session.add_all([batman, superman])
        session.commit()

        response = client.get("/admin/api/user/list?name=bat&name_op=contains")
        assert response.status_code == 200
        data = response.json()
        names = [row["name"] for row in data["rows"]]
        assert "batman" in names
        assert "superman" not in names


def test_filter_processing_without_operator(client: TestClient) -> None:
    """Test that ModelView correctly processes filters without has_operator attribute"""
    with Session() as session:
        batman = User(name="batman")
        superman = User(name="superman")
        session.add_all([batman, superman])
        session.commit()

        response = client.get("/admin/api/user/list?simple_name=batman")
        assert response.status_code == 200
        data = response.json()
        names = [row["name"] for row in data["rows"]]
        assert "batman" in names
        assert "superman" not in names


def test_filter_operation_edge_cases(client: TestClient) -> None:
    """Test edge cases for operation-based filters"""
    with Session() as session:
        batman = User(name="batman")
        superman = User(name="superman")
        session.add_all([batman, superman])
        session.commit()

        # Test with operation parameter but no value - should show all users
        response = client.get("/admin/api/user/list?name_op=contains")
        assert response.status_code == 200
        data = response.json()
        names = [row["name"] for row in data["rows"]]
        assert "batman" in names
        assert "superman" in names

        # Test with value but no operation parameter - should show all users
        response = client.get("/admin/api/user/list?name=batman")
        assert response.status_code == 200
        data = response.json()
        names = [row["name"] for row in data["rows"]]
        assert "batman" in names
        assert "superman" in names

        # Test with empty operation value
        response = client.get("/admin/api/user/list?name=batman&name_op=")
        assert response.status_code == 200
        data = response.json()
        names = [row["name"] for row in data["rows"]]
        assert "batman" in names
        assert "superman" in names

        # Test with empty filter value
        response = client.get("/admin/api/user/list?name=&name_op=contains")
        assert response.status_code == 200
        data = response.json()
        names = [row["name"] for row in data["rows"]]
        assert "batman" in names
        assert "superman" in names


def test_filter_mixed_types(client: TestClient) -> None:
    """Test ModelView with both operation-based and simple filters"""
    with Session() as session:
        batman = User(name="batman")
        superman = User(name="superman")
        joker = User(name="joker")
        session.add_all([batman, superman, joker])
        session.commit()

        # Test operation-based filter (ColumnFilter with has_operator=True)
        response = client.get("/admin/api/user/list?name=man&name_op=contains")
        assert response.status_code == 200
        data = response.json()
        names = [row["name"] for row in data["rows"]]
        assert "batman" in names
        assert "superman" in names
        assert "joker" not in names
