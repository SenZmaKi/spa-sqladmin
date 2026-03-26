import enum
import json
from typing import Any, Generator

import pytest
from sqlalchemy import (
    JSON,
    Column,
    Date,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
    select,
)
from sqlalchemy.orm import declarative_base, relationship, selectinload, sessionmaker
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.testclient import TestClient

from spa_sqladmin import Admin, ModelView
from tests.common import sync_engine as engine

Base = declarative_base()  # type: Any
session_maker = sessionmaker(bind=engine)

app = Starlette()
admin = Admin(app=app, engine=engine)


class Status(enum.Enum):
    ACTIVE = "ACTIVE"
    DEACTIVE = "DEACTIVE"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(length=16))
    email = Column(String, unique=True)
    birthdate = Column(Date)
    status = Column(Enum(Status), default=Status.ACTIVE)
    meta_data = Column(JSON)

    addresses = relationship("Address", back_populates="user")
    profile = relationship("Profile", back_populates="user", uselist=False)

    addresses_formattable = relationship("AddressFormattable", back_populates="user")
    profile_formattable = relationship(
        "ProfileFormattable", back_populates="user", uselist=False
    )

    def __str__(self) -> str:
        return f"User {self.id}"


class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="addresses")

    def __str__(self) -> str:
        return f"Address {self.id}"


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    user = relationship("User", back_populates="profile")

    def __str__(self) -> str:
        return f"Profile {self.id}"


class AddressFormattable(Base):
    __tablename__ = "addresses_formattable"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="addresses_formattable")

    def __str__(self) -> str:
        return f"Address {self.id}"


class ProfileFormattable(Base):
    __tablename__ = "profiles_formattable"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    user = relationship("User", back_populates="profile_formattable")

    def __str__(self) -> str:
        return f"Profile {self.id}"


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True)


class Product(Base):
    __tablename__ = "product"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    price = Column(Integer)


@pytest.fixture
def prepare_database() -> Generator[None, None, None]:
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client(prepare_database: Any) -> Generator[TestClient, None, None]:
    with TestClient(app=app, base_url="http://testserver") as c:
        yield c


class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.name,
        User.email,
        User.addresses,
        User.profile,
        User.addresses_formattable,
        User.profile_formattable,
        User.status,
    ]
    column_labels = {User.email: "Email"}
    column_searchable_list = [User.name]
    column_sortable_list = [User.id]
    column_export_list = [User.name, User.status]
    column_formatters = {
        User.addresses_formattable: lambda m, a: [
            f"Formatted {a}" for a in m.addresses_formattable
        ],
        User.profile_formattable: lambda m, a: f"Formatted {m.profile_formattable}",
    }
    column_formatters_detail = {
        User.addresses_formattable: lambda m, a: [
            f"Formatted {a}" for a in m.addresses_formattable
        ],
        User.profile_formattable: lambda m, a: f"Formatted {m.profile_formattable}",
    }
    save_as = True
    form_create_rules = ["name", "email", "addresses", "profile", "birthdate", "status"]
    form_edit_rules = ["name", "email", "addresses", "profile", "birthdate"]


class AddressAdmin(ModelView, model=Address):
    column_list = ["id", "user_id", "user", "user.profile.id"]
    name_plural = "Addresses"
    export_max_rows = 3


class ProfileAdmin(ModelView, model=Profile):
    column_list = ["id", "user_id", "user"]


class MovieAdmin(ModelView, model=Movie):
    can_edit = False
    can_delete = False
    can_view_details = False

    def is_accessible(self, request: Request) -> bool:
        return False

    def is_visible(self, request: Request) -> bool:
        return False


class ProductAdmin(ModelView, model=Product):
    pass


admin.add_view(UserAdmin)
admin.add_view(AddressAdmin)
admin.add_view(ProfileAdmin)
admin.add_view(MovieAdmin)
admin.add_view(ProductAdmin)


def test_root_view(client: TestClient) -> None:
    response = client.get("/admin/api/site")

    assert response.status_code == 200
    data = response.json()
    model_names = [m["name_plural"] for m in data["models"]]
    assert "Users" in model_names
    assert "Addresses" in model_names


def test_invalid_list_page(client: TestClient) -> None:
    response = client.get("/admin/api/example/list")

    assert response.status_code == 404


def test_list_view_single_page(client: TestClient) -> None:
    with session_maker() as session:
        for _ in range(5):
            user = User(name="John Doe")
            session.add(user)
        session.commit()

    response = client.get("/admin/api/user/list")

    assert response.status_code == 200
    data = response.json()

    assert data["count"] == 5
    assert len(data["rows"]) == 5
    assert data["page"] == 1
    assert data["identity"] == "user"


def test_list_view_with_relationships(client: TestClient) -> None:
    with session_maker() as session:
        for _ in range(5):
            user = User(name="John Doe")
            user.addresses.append(Address())
            user.profile = Profile()
            session.add(user)
        session.commit()

    response = client.get("/admin/api/user/list")

    assert response.status_code == 200
    data = response.json()
    row = data["rows"][0]

    # Relationship values are serialized as objects with pk/repr/identity
    addr_val = row["addresses"]
    assert isinstance(addr_val, list)
    assert addr_val[0]["repr"] == "Address 1"
    assert addr_val[0]["pk"] == "1"
    assert addr_val[0]["identity"] == "address"

    profile_val = row["profile"]
    assert isinstance(profile_val, dict)
    assert profile_val["repr"] == "Profile 1"
    assert profile_val["pk"] == "1"
    assert profile_val["identity"] == "profile"


def test_list_view_with_formatted_relationships(client: TestClient) -> None:
    with session_maker() as session:
        for _ in range(5):
            user = User(name="John Doe")
            user.addresses_formattable.append(AddressFormattable())
            user.profile_formattable = ProfileFormattable()
            session.add(user)
        session.commit()

    response = client.get("/admin/api/user/list")

    assert response.status_code == 200
    data = response.json()
    row = data["rows"][0]

    # Formatted relationship fields are still present as serialized relation data
    assert "addresses_formattable" in row
    assert "profile_formattable" in row
    addr_val = row["addresses_formattable"]
    assert isinstance(addr_val, list)
    assert len(addr_val) > 0
    assert addr_val[0]["repr"] == "Address 1"

    profile_val = row["profile_formattable"]
    assert isinstance(profile_val, dict)
    assert profile_val["repr"] == "Profile 1"


def test_list_view_multi_page(client: TestClient) -> None:
    with session_maker() as session:
        for _ in range(45):
            user = User(name="John Doe")
            session.add(user)
        session.commit()

    response = client.get("/admin/api/user/list")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 45
    assert data["page"] == 1
    assert len(data["rows"]) == data["page_size"]

    response = client.get("/admin/api/user/list?page=3")

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 3
    assert data["count"] == 45

    response = client.get("/admin/api/user/list?page=5")

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 5
    assert data["count"] == 45


def test_list_page_permission_actions(client: TestClient) -> None:
    with session_maker() as session:
        for _ in range(10):
            user = User(name="John Doe")
            session.add(user)
            session.flush()

            address = Address(user_id=user.id)
            session.add(address)

        session.commit()

    response = client.get("/admin/api/user/list")

    assert response.status_code == 200
    data = response.json()
    perms = data["permissions"]
    assert perms["can_view_details"] is True
    assert perms["can_delete"] is True
    assert perms["can_edit"] is True
    assert perms["can_create"] is True

    response = client.get("/admin/api/address/list")

    assert response.status_code == 200
    data = response.json()
    perms = data["permissions"]
    assert perms["can_view_details"] is True
    assert perms["can_edit"] is True
    assert perms["can_delete"] is True


def test_unauthorized_detail_page(client: TestClient) -> None:
    response = client.get("/admin/api/movie/detail/1")

    assert response.status_code == 403


def test_not_found_detail_page(client: TestClient) -> None:
    response = client.get("/admin/api/user/detail/1")

    assert response.status_code == 404


def test_detail_page(client: TestClient) -> None:
    with session_maker() as session:
        user = User(name="Amin Alaee")
        session.add(user)
        session.flush()

        for _ in range(2):
            address = Address(user_id=user.id)
            session.add(address)
            address_formattable = AddressFormattable(user_id=user.id)
            session.add(address_formattable)
        profile = Profile(user=user)
        session.add(profile)
        profile_formattable = ProfileFormattable(user=user)
        session.add(profile_formattable)
        session.commit()

    response = client.get("/admin/api/user/detail/1")

    assert response.status_code == 200
    data = response.json()

    assert data["pk"] == "1"
    assert data["repr"] == "User 1"
    assert data["identity"] == "user"

    fields_by_name = {f["name"]: f for f in data["fields"]}

    assert fields_by_name["id"]["value"] == 1
    assert fields_by_name["name"]["value"] == "Amin Alaee"

    # Relationship fields
    assert fields_by_name["addresses"]["is_relation"] is True
    addr_related = fields_by_name["addresses"]["related"]
    assert isinstance(addr_related, list)
    assert addr_related[0]["repr"] == "Address 1"

    assert fields_by_name["profile"]["is_relation"] is True
    profile_related = fields_by_name["profile"]["related"]
    assert profile_related["repr"] == "Profile 1"

    # Formatted relationship fields are present
    assert "addresses_formattable" in fields_by_name
    assert "profile_formattable" in fields_by_name

    # Permissions
    assert data["permissions"]["can_edit"] is True
    assert data["permissions"]["can_delete"] is True


def test_column_labels(client: TestClient) -> None:
    with session_maker() as session:
        user = User(name="Foo")
        session.add(user)
        session.commit()

    response = client.get("/admin/api/user/list")

    assert response.status_code == 200
    data = response.json()
    col_labels = {c["name"]: c["label"] for c in data["columns"]}
    assert col_labels["email"] == "Email"

    response = client.get("/admin/api/user/detail/1")

    assert response.status_code == 200
    data = response.json()
    field_labels = {f["name"]: f["label"] for f in data["fields"]}
    assert field_labels["email"] == "Email"


def test_delete_endpoint_unauthorized_response(client: TestClient) -> None:
    response = client.delete("/admin/api/movie/delete")

    assert response.status_code == 403


def test_delete_endpoint_not_found_response(client: TestClient) -> None:
    response = client.delete("/admin/api/user/delete?pks=1")

    assert response.status_code == 404

    with session_maker() as s:
        assert s.query(User).count() == 0


def test_delete_endpoint(client: TestClient) -> None:
    with session_maker() as session:
        user = User(name="Bar")
        session.add(user)
        session.commit()

    with session_maker() as s:
        assert s.query(User).count() == 1

    response = client.delete("/admin/api/user/delete?pks=1")

    assert response.status_code == 200
    assert response.json()["success"] is True

    with session_maker() as s:
        assert s.query(User).count() == 0


def test_create_endpoint_unauthorized_response(client: TestClient) -> None:
    response = client.get("/admin/api/movie/form-schema?action=create")

    assert response.status_code == 403


def test_create_endpoint_get_form(client: TestClient) -> None:
    response = client.get("/admin/api/user/form-schema?action=create")

    assert response.status_code == 200
    data = response.json()
    field_names = [f["name"] for f in data["fields"]]

    assert "name" in field_names
    assert "email" in field_names
    assert "addresses" in field_names
    assert "profile" in field_names
    assert "status" in field_names
    assert "birthdate" in field_names

    assert data["identity"] == "user"


def test_create_endpoint_with_required_fields(client: TestClient) -> None:
    response = client.get("/admin/api/product/form-schema?action=create")

    assert response.status_code == 200
    data = response.json()
    fields_by_name = {f["name"]: f for f in data["fields"]}

    assert fields_by_name["name"]["required"] is True
    assert fields_by_name["price"]["required"] is False


def test_create_endpoint_post_form(client: TestClient) -> None:
    body: dict = {"birthdate": "Wrong Date Format"}
    response = client.post("/admin/api/user/create", json=body)

    assert response.status_code == 400
    errors = response.json()["errors"]
    assert "birthdate" in errors
    assert "Not a valid date value." in errors["birthdate"]

    body = {"name": "SQLAlchemy", "email": "amin"}
    response = client.post("/admin/api/user/create", json=body)

    assert response.status_code == 200
    assert response.json()["success"] is True

    stmt = select(func.count(User.id))
    with session_maker() as s:
        assert s.execute(stmt).scalar_one() == 1

    stmt = (
        select(User)
        .limit(1)
        .options(selectinload(User.addresses))
        .options(selectinload(User.profile))
    )
    with session_maker() as s:
        user = s.execute(stmt).scalar_one()
    assert user.name == "SQLAlchemy"
    assert user.email == "amin"
    assert user.addresses == []
    assert user.profile is None

    body = {"user": str(user.id)}
    response = client.post("/admin/api/address/create", json=body)

    assert response.status_code == 200

    stmt = select(func.count(Address.id))
    with session_maker() as s:
        assert s.execute(stmt).scalar_one() == 1

    stmt = select(Address).limit(1).options(selectinload(Address.user))
    with session_maker() as s:
        address = s.execute(stmt).scalar_one()
    assert address.user.id == user.id
    assert address.user_id == user.id

    body = {"user": str(user.id)}
    response = client.post("/admin/api/profile/create", json=body)

    assert response.status_code == 200

    stmt = select(func.count(Profile.id))
    with session_maker() as s:
        assert s.execute(stmt).scalar_one() == 1

    stmt = select(Profile).limit(1).options(selectinload(Profile.user))
    with session_maker() as s:
        profile = s.execute(stmt).scalar_one()
    assert profile.user.id == user.id
    assert profile.user_id == user.id

    body = {
        "name": "SQLAdmin",
        "addresses": [str(address.id)],
        "profile": str(profile.id),
    }
    response = client.post("/admin/api/user/create", json=body)

    assert response.status_code == 200

    stmt = select(func.count(User.id))
    with session_maker() as s:
        assert s.execute(stmt).scalar_one() == 2

    stmt = (
        select(User)
        .offset(1)
        .limit(1)
        .options(selectinload(User.addresses))
        .options(selectinload(User.profile))
    )
    with session_maker() as s:
        user = s.execute(stmt).scalar_one()
    assert user.name == "SQLAdmin"
    assert user.addresses[0].id == address.id
    assert user.profile.id == profile.id

    # Duplicate unique email should fail
    body = {"name": "SQLAlchemy", "email": "amin"}
    response = client.post("/admin/api/user/create", json=body)
    assert response.status_code == 400


def test_is_accessible_method(client: TestClient) -> None:
    response = client.get("/admin/api/movie/list")

    assert response.status_code == 403


def test_is_visible_method(client: TestClient) -> None:
    response = client.get("/admin/api/site")

    assert response.status_code == 200
    data = response.json()
    model_names = [m["name"] for m in data["models"]]
    assert "User" in model_names
    assert "Address" in model_names
    assert "Movie" not in model_names


def test_edit_endpoint_unauthorized_response(client: TestClient) -> None:
    response = client.get("/admin/api/movie/form-schema?action=edit&pk=1")

    assert response.status_code == 403


def test_not_found_edit_page(client: TestClient) -> None:
    response = client.get("/admin/api/user/form-schema?action=edit&pk=1")

    assert response.status_code == 404


def test_update_get_page(client: TestClient) -> None:
    with session_maker() as session:
        user = User(name="Joe", meta_data={"A": "B"})
        session.add(user)
        session.flush()

        address = Address(user=user)
        session.add(address)
        profile = Profile(user=user)
        session.add(profile)
        session.commit()

    response = client.get("/admin/api/user/form-schema?action=edit&pk=1")

    assert response.status_code == 200
    data = response.json()
    fields_by_name = {f["name"]: f for f in data["fields"]}

    assert "addresses" in fields_by_name
    assert "profile" in fields_by_name
    assert fields_by_name["name"]["value"] == "Joe"
    # status should not be in edit form (form_edit_rules excludes it)
    assert "status" not in fields_by_name

    response = client.get("/admin/api/address/form-schema?action=edit&pk=1")

    assert response.status_code == 200
    data = response.json()
    fields_by_name = {f["name"]: f for f in data["fields"]}
    assert "user" in fields_by_name

    response = client.get("/admin/api/profile/form-schema?action=edit&pk=1")

    assert response.status_code == 200
    data = response.json()
    fields_by_name = {f["name"]: f for f in data["fields"]}
    assert "user" in fields_by_name


def test_update_submit_form(client: TestClient) -> None:
    with session_maker() as session:
        user = User(name="Joe")
        session.add(user)
        session.flush()

        address = Address(user=user)
        session.add(address)
        address_2 = Address(id=2)
        session.add(address_2)
        profile = Profile(user=user)
        session.add(profile)
        session.commit()

    body = {"name": "Jack", "email": "amin"}
    response = client.post("/admin/api/user/edit/1", json=body)

    assert response.status_code == 200
    assert response.json()["success"] is True

    stmt = (
        select(User)
        .limit(1)
        .options(selectinload(User.addresses))
        .options(selectinload(User.profile))
    )
    with session_maker() as s:
        user = s.execute(stmt).scalar_one()
    assert user.name == "Jack"
    assert user.addresses == []
    assert user.profile is None
    assert user.email == "amin"

    body = {"name": "Jack", "addresses": ["1"], "profile": "1"}
    response = client.post("/admin/api/user/edit/1", json=body)

    assert response.status_code == 200

    stmt = select(Address).filter(Address.id == 1).limit(1)
    with session_maker() as s:
        address = s.execute(stmt).scalar_one()
    assert address.user_id == 1

    stmt = select(Profile).limit(1)
    with session_maker() as s:
        profile = s.execute(stmt).scalar_one()
    assert profile.user_id == 1

    # Name too long should fail validation
    body = {"name": "Jack" * 10}
    response = client.post("/admin/api/user/edit/1", json=body)

    assert response.status_code == 400

    body = {"user": str(user.id)}
    response = client.post("/admin/api/address/edit/1", json=body)

    assert response.status_code == 200

    stmt = select(Address).filter(Address.id == 1).limit(1)
    with session_maker() as s:
        address = s.execute(stmt).scalar_one()
    assert address.user_id == 1

    # Duplicate unique email should fail
    body = {"name": "Jack", "email": "amin"}
    client.post("/admin/api/user/edit/1", json=body)
    # Create user 2 first via create endpoint
    body_create = {"name": "Jack2", "email": "other"}
    client.post("/admin/api/user/create", json=body_create)
    body = {"name": "Jack", "email": "amin"}
    response = client.post("/admin/api/user/edit/2", json=body)
    assert response.status_code == 400

    body = {"name": "Jack", "addresses": ["1", "2"], "profile": "1"}
    response = client.post("/admin/api/user/edit/1", json=body)

    assert response.status_code == 200

    stmt = select(Address).limit(2)
    with session_maker() as s:
        result = s.execute(stmt).all()
    for address in result:
        assert address[0].user_id == 1


def test_searchable_list(client: TestClient) -> None:
    with session_maker() as session:
        user = User(name="Ross")
        session.add(user)
        user = User(name="Boss")
        session.add(user)
        session.commit()

    response = client.get("/admin/api/user/list")
    data = response.json()
    assert data["searchable"] is True
    assert "name" in data["search_placeholder"]
    assert len(data["rows"]) == 2

    response = client.get("/admin/api/user/list?search=ro")
    data = response.json()
    assert len(data["rows"]) == 1
    assert data["rows"][0]["name"] == "Ross"

    response = client.get("/admin/api/user/list?search=rose")
    data = response.json()
    assert len(data["rows"]) == 0


def test_sortable_list(client: TestClient) -> None:
    with session_maker() as session:
        user = User(name="Lisa")
        session.add(user)
        session.commit()

    response = client.get("/admin/api/user/list?sortBy=id&sort=asc")
    data = response.json()

    # Verify the id column is marked as sortable
    id_col = next(c for c in data["columns"] if c["name"] == "id")
    assert id_col["sortable"] is True
    assert len(data["rows"]) == 1

    response = client.get("/admin/api/user/list?sortBy=id&sort=desc")
    data = response.json()
    assert len(data["rows"]) == 1


def test_export_csv(client: TestClient) -> None:
    with session_maker() as session:
        user = User(name="Daniel", status="ACTIVE")
        session.add(user)
        session.commit()

    response = client.get("/admin/api/user/export/csv")
    assert response.text == "name,status\r\nDaniel,ACTIVE\r\n"


def test_export_csv_utf8(client: TestClient) -> None:
    with session_maker() as session:
        user_1 = User(name="Daniel", status="ACTIVE")
        user_2 = User(name="دانيال", status="ACTIVE")
        user_3 = User(name="積極的", status="ACTIVE")
        user_4 = User(name="Даниэль", status="ACTIVE")
        session.add(user_1)
        session.add(user_2)
        session.add(user_3)
        session.add(user_4)
        session.commit()

    response = client.get("/admin/api/user/export/csv")
    assert response.text == (
        "name,status\r\nDaniel,ACTIVE\r\nدانيال,ACTIVE\r\n"
        "積極的,ACTIVE\r\nДаниэль,ACTIVE\r\n"
    )


def test_export_json(client: TestClient) -> None:
    with session_maker() as session:
        user = User(name="Daniel", status="ACTIVE")
        session.add(user)
        session.commit()

    response = client.get("/admin/api/user/export/json")
    assert response.text == '[{"name": "Daniel", "status": "ACTIVE"}]'


def test_export_json_utf8(client: TestClient) -> None:
    with session_maker() as session:
        user_1 = User(name="Daniel", status="ACTIVE")
        user_2 = User(name="دانيال", status="ACTIVE")
        user_3 = User(name="積極的", status="ACTIVE")
        user_4 = User(name="Даниэль", status="ACTIVE")
        session.add(user_1)
        session.add(user_2)
        session.add(user_3)
        session.add(user_4)
        session.commit()

    response = client.get("/admin/api/user/export/json")
    assert response.text == (
        '[{"name": "Daniel", "status": "ACTIVE"},'
        '{"name": "دانيال", "status": "ACTIVE"},'
        '{"name": "積極的", "status": "ACTIVE"},'
        '{"name": "Даниэль", "status": "ACTIVE"}]'
    )


def test_export_json_complex_model(client: TestClient) -> None:
    with session_maker() as session:
        user = User(name="Daniel", status="ACTIVE")
        session.add(user)
        session.commit()
        address = Address(user_id=user.id)
        session.add(address)
        session.commit()

    response = client.get("/admin/api/address/export/json")
    assert response.text == json.dumps(
        [{"id": "1", "user_id": "1", "user": "User 1", "user.profile.id": "None"}]
    )


def test_export_csv_row_count(client: TestClient) -> None:
    def row_count(resp) -> int:
        return resp.text.count("\r\n") - 1

    with session_maker() as session:
        for _ in range(20):
            user = User(name="Raymond")
            session.add(user)
            session.flush()

            address = Address(user_id=user.id)
            session.add(address)

        session.commit()

    response = client.get("/admin/api/user/export/csv")
    assert row_count(response) == 20

    response = client.get("/admin/api/address/export/csv")
    assert row_count(response) == 3


def test_export_bad_type_is_404(client: TestClient) -> None:
    response = client.get("/admin/api/user/export/bad_type")
    assert response.status_code == 404


def test_export_permission(client: TestClient) -> None:
    response = client.get("/admin/api/movie/export/csv")
    assert response.status_code == 403
