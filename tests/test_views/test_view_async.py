import enum
from typing import Any, AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    Date,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base, relationship, selectinload, sessionmaker
from starlette.applications import Starlette
from starlette.requests import Request

from spa_sqladmin import Admin, ModelView
from tests.common import async_engine as engine

pytestmark = pytest.mark.anyio

Base = declarative_base()  # type: Any
session_maker = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

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
    date_of_birth = Column(Date)
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

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
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
    price = Column(BigInteger)


@pytest.fixture
async def prepare_database() -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def client(prepare_database: Any) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


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


async def test_root_view(client: AsyncClient) -> None:
    response = await client.get("/admin/api/site")

    assert response.status_code == 200
    data = response.json()
    model_names = [m["name_plural"] for m in data["models"]]
    assert "Users" in model_names
    assert "Addresses" in model_names


async def test_invalid_list_page(client: AsyncClient) -> None:
    response = await client.get("/admin/api/example/list")

    assert response.status_code == 404


async def test_list_view_single_page(client: AsyncClient) -> None:
    async with session_maker() as session:
        for _ in range(5):
            user = User(name="John Doe")
            session.add(user)
        await session.commit()

    response = await client.get("/admin/api/user/list")
    assert response.status_code == 200

    data = response.json()
    assert data["count"] == 5
    assert len(data["rows"]) == 5
    assert "columns" in data


async def test_list_view_with_relations(client: AsyncClient) -> None:
    async with session_maker() as session:
        for _ in range(5):
            user = User(name="John Doe")
            user.addresses.append(Address())
            user.profile = Profile()
            session.add(user)
        await session.commit()

    response = await client.get("/admin/api/user/list")

    assert response.status_code == 200

    data = response.json()
    row = data["rows"][0]
    # addresses is a many relation – list of dicts with repr
    assert isinstance(row["addresses"], list)
    assert row["addresses"][0]["repr"] == "Address 1"
    # profile is a single relation – dict with repr
    assert row["profile"]["repr"] == "Profile 1"


async def test_list_view_with_formatted_relations(client: AsyncClient) -> None:
    async with session_maker() as session:
        for _ in range(5):
            user = User(name="John Doe")
            user.addresses_formattable.append(AddressFormattable())
            user.profile_formattable = ProfileFormattable()
            session.add(user)
        await session.commit()

    response = await client.get("/admin/api/user/list")

    assert response.status_code == 200

    data = response.json()
    row = data["rows"][0]
    # addresses_formattable is a list of relation dicts with repr
    assert isinstance(row["addresses_formattable"], list)
    assert "repr" in row["addresses_formattable"][0]


async def test_list_view_multi_page(client: AsyncClient) -> None:
    async with session_maker() as session:
        for _ in range(45):
            user = User(name="John Doe")
            session.add(user)
        await session.commit()

    response = await client.get("/admin/api/user/list")
    assert response.status_code == 200

    data = response.json()
    assert data["count"] == 45
    assert data["page"] == 1
    assert data["page_size"] == 10

    response = await client.get("/admin/api/user/list?page=3")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 3

    response = await client.get("/admin/api/user/list?page=5")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 5


async def test_list_page_permission_actions(client: AsyncClient) -> None:
    async with session_maker() as session:
        for _ in range(10):
            user = User(name="John Doe")
            session.add(user)
            await session.flush()

            address = Address(user_id=user.id)
            session.add(address)

        await session.commit()

    response = await client.get("/admin/api/user/list")

    assert response.status_code == 200
    data = response.json()
    perms = data["permissions"]
    assert perms["can_view_details"] is True
    assert perms["can_delete"] is True

    response = await client.get("/admin/api/address/list")

    assert response.status_code == 200
    data = response.json()
    perms = data["permissions"]
    assert perms["can_view_details"] is True
    assert perms["can_delete"] is True


async def test_unauthorized_detail_page(client: AsyncClient) -> None:
    response = await client.get("/admin/api/movie/detail/1")

    assert response.status_code == 403


async def test_not_found_detail_page(client: AsyncClient) -> None:
    response = await client.get("/admin/api/user/detail/1")

    assert response.status_code == 404


async def test_detail_page(client: AsyncClient) -> None:
    async with session_maker() as session:
        user = User(name="Amin Alaee")
        session.add(user)
        await session.flush()

        for _ in range(2):
            address = Address(user_id=user.id)
            session.add(address)
            address_formattable = AddressFormattable(user_id=user.id)
            session.add(address_formattable)
        profile = Profile(user_id=user.id)
        session.add(profile)
        profile_formattable = ProfileFormattable(user=user)
        session.add(profile_formattable)
        await session.commit()

    response = await client.get("/admin/api/user/detail/1")

    assert response.status_code == 200
    data = response.json()
    fields = {f["name"]: f for f in data["fields"]}
    assert fields["id"]["value"] == 1
    assert fields["name"]["value"] == "Amin Alaee"
    # addresses is a many-relation: related is a list of dicts
    assert isinstance(fields["addresses"]["related"], list)
    assert fields["addresses"]["related"][0]["repr"] == "Address 1"
    # profile is a single relation: related is a dict
    assert fields["profile"]["related"]["repr"] == "Profile 1"


async def test_column_labels(client: AsyncClient) -> None:
    async with session_maker() as session:
        user = User(name="Foo")
        session.add(user)
        await session.commit()

    response = await client.get("/admin/api/user/list")

    assert response.status_code == 200
    data = response.json()
    labels = [c["label"] for c in data["columns"]]
    assert "Email" in labels

    response = await client.get("/admin/api/user/detail/1")

    assert response.status_code == 200
    data = response.json()
    labels = [f["label"] for f in data["fields"]]
    assert "Email" in labels


async def test_delete_endpoint_unauthorized_response(client: AsyncClient) -> None:
    response = await client.delete("/admin/api/movie/delete?pks=1")

    assert response.status_code == 403


async def test_delete_endpoint_not_found_response(client: AsyncClient) -> None:
    response = await client.delete("/admin/api/user/delete?pks=1")

    assert response.status_code == 404


async def test_delete_endpoint(client: AsyncClient) -> None:
    async with session_maker() as session:
        user = User(name="Bar")
        session.add(user)
        await session.commit()

    stmt = select(func.count(User.id))

    async with session_maker() as s:
        result = await s.execute(stmt)
    assert result.scalar_one() == 1

    response = await client.delete("/admin/api/user/delete?pks=1")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    async with session_maker() as s:
        result = await s.execute(stmt)
    assert result.scalar_one() == 0


async def test_create_endpoint_unauthorized_response(client: AsyncClient) -> None:
    response = await client.get("/admin/api/movie/form-schema")

    assert response.status_code == 403


async def test_create_endpoint_get_form(client: AsyncClient) -> None:
    response = await client.get("/admin/api/user/form-schema")

    assert response.status_code == 200
    data = response.json()
    fields = {f["name"]: f for f in data["fields"]}
    assert fields["addresses"]["type"] == "relation_select_multiple"
    assert fields["profile"]["type"] == "relation_select"
    assert fields["name"]["type"] == "string"
    assert fields["email"]["type"] == "string"


async def test_create_endpoint_with_required_fields(client: AsyncClient) -> None:
    response = await client.get("/admin/api/product/form-schema")

    assert response.status_code == 200
    data = response.json()
    fields = {f["name"]: f for f in data["fields"]}
    assert fields["name"]["required"] is True
    assert fields["price"]["required"] is False


async def test_create_endpoint_post_form(client: AsyncClient) -> None:
    data = {"date_of_birth": "Wrong Date Format"}
    response = await client.post("/admin/api/user/create", data=data)

    assert response.status_code == 400
    resp_data = response.json()
    assert "errors" in resp_data

    data = {"name": "SQLAlchemy", "email": "amin"}
    response = await client.post("/admin/api/user/create", data=data)

    stmt = select(func.count(User.id))
    async with session_maker() as s:
        result = await s.execute(stmt)
    assert result.scalar_one() == 1

    stmt = (
        select(User)
        .limit(1)
        .options(selectinload(User.addresses))
        .options(selectinload(User.profile))
    )
    async with session_maker() as s:
        result = await s.execute(stmt)
    user = result.scalar_one()
    assert user.name == "SQLAlchemy"
    assert user.email == "amin"
    assert user.addresses == []
    assert user.profile is None

    data = {"user": user.id}
    response = await client.post("/admin/api/address/create", data=data)

    stmt = select(func.count(Address.id))
    async with session_maker() as s:
        result = await s.execute(stmt)
    assert result.scalar_one() == 1

    stmt = select(Address).limit(1).options(selectinload(Address.user))
    async with session_maker() as s:
        result = await s.execute(stmt)
    address = result.scalar_one()
    assert address.user.id == user.id
    assert address.user_id == user.id

    data = {"user": user.id}
    response = await client.post("/admin/api/profile/create", data=data)

    stmt = select(func.count(Profile.id))
    async with session_maker() as s:
        result = await s.execute(stmt)
    assert result.scalar_one() == 1

    stmt = select(Profile).limit(1).options(selectinload(Profile.user))
    async with session_maker() as s:
        result = await s.execute(stmt)
    profile = result.scalar_one()
    assert profile.user.id == user.id

    data = {
        "name": "SQLAdmin",
        "addresses": [address.id],
        "profile": profile.id,
    }
    response = await client.post("/admin/api/user/create", data=data)

    stmt = select(func.count(User.id))
    async with session_maker() as s:
        result = await s.execute(stmt)
    assert result.scalar_one() == 2

    stmt = (
        select(User)
        .offset(1)
        .limit(1)
        .options(selectinload(User.addresses))
        .options(selectinload(User.profile))
    )
    async with session_maker() as s:
        result = await s.execute(stmt)
    user = result.scalar_one()
    assert user.name == "SQLAdmin"
    assert user.addresses[0].id == address.id
    assert user.profile.id == profile.id

    data = {"name": "SQLAlchemy", "email": "amin"}
    response = await client.post("/admin/api/user/create", data=data)
    assert response.status_code == 400
    resp_data = response.json()
    assert "error" in resp_data or "errors" in resp_data


async def test_list_view_page_size_options(client: AsyncClient) -> None:
    response = await client.get("/admin/api/user/list")

    assert response.status_code == 200
    data = response.json()
    assert data["page_size_options"] == [10, 25, 50, 100]


async def test_is_accessible_method(client: AsyncClient) -> None:
    response = await client.get("/admin/api/movie/list")

    assert response.status_code == 403


async def test_is_visible_method(client: AsyncClient) -> None:
    response = await client.get("/admin/api/site")

    assert response.status_code == 200
    data = response.json()
    model_names = [m["name_plural"] for m in data["models"]]
    assert "Users" in model_names
    assert "Addresses" in model_names
    assert "Movie" not in model_names
    assert "Movies" not in model_names


async def test_edit_endpoint_unauthorized_response(client: AsyncClient) -> None:
    response = await client.get("/admin/api/movie/form-schema?action=edit&pk=1")

    assert response.status_code == 403


async def test_not_found_edit_page(client: AsyncClient) -> None:
    response = await client.get("/admin/api/user/form-schema?action=edit&pk=1")

    assert response.status_code == 404


async def test_update_get_page(client: AsyncClient) -> None:
    async with session_maker() as session:
        user = User(name="Joe", meta_data={"A": "B"})
        session.add(user)
        await session.flush()

        address = Address(user=user)
        session.add(address)
        profile = Profile(user=user)
        session.add(profile)
        await session.commit()

    response = await client.get("/admin/api/user/form-schema?action=edit&pk=1")

    assert response.status_code == 200
    data = response.json()
    fields = {f["name"]: f for f in data["fields"]}
    assert fields["addresses"]["type"] == "relation_select_multiple"
    assert fields["name"]["value"] == "Joe"

    response = await client.get("/admin/api/address/form-schema?action=edit&pk=1")

    assert response.status_code == 200
    data = response.json()
    fields = {f["name"]: f for f in data["fields"]}
    assert fields["user"]["type"] == "relation_select"

    response = await client.get("/admin/api/profile/form-schema?action=edit&pk=1")

    assert response.status_code == 200
    data = response.json()
    fields = {f["name"]: f for f in data["fields"]}
    assert fields["user"]["type"] == "relation_select"


async def test_update_submit_form(client: AsyncClient) -> None:
    async with session_maker() as session:
        user = User(name="Joe")
        session.add(user)
        await session.flush()

        address = Address(user=user)
        session.add(address)
        address_2 = Address(id=2)
        session.add(address_2)
        profile = Profile(user=user)
        session.add(profile)
        await session.commit()

    data = {"name": "Jack", "email": "amin"}
    response = await client.post("/admin/api/user/edit/1", data=data)

    stmt = (
        select(User)
        .limit(1)
        .options(selectinload(User.addresses))
        .options(selectinload(User.profile))
    )
    async with session_maker() as s:
        result = await s.execute(stmt)
    user = result.scalar_one()
    assert user.name == "Jack"
    assert user.addresses == []
    assert user.profile is None
    assert user.email == "amin"

    data = {"name": "Jack", "addresses": "1", "profile": "1"}
    response = await client.post("/admin/api/user/edit/1", data=data)

    stmt = select(Address).filter(Address.id == 1).limit(1)
    async with session_maker() as s:
        result = await s.execute(stmt)
    address = result.scalar_one()
    assert address.user_id == 1

    stmt = select(Profile).limit(1)
    async with session_maker() as s:
        result = await s.execute(stmt)
    profile = result.scalar_one()
    assert profile.user_id == 1

    data = {"name": "Jack" * 10}
    response = await client.post("/admin/api/user/edit/1", data=data)

    assert response.status_code == 400

    data = {"user": user.id}
    response = await client.post("/admin/api/address/edit/1", data=data)

    stmt = select(Address).filter(Address.id == 1).limit(1)
    async with session_maker() as s:
        result = await s.execute(stmt)
    address = result.scalar_one()
    assert address.user_id == 1

    data = {"name": "Jack", "addresses": ["1", "2"], "profile": "1"}
    response = await client.post("/admin/api/user/edit/1", data=data)

    stmt = select(Address).limit(1)
    async with session_maker() as s:
        result = await s.execute(stmt)
    for address in result:
        assert address[0].user_id == 1


async def test_searchable_list(client: AsyncClient) -> None:
    async with session_maker() as session:
        user = User(name="Ross")
        session.add(user)
        user = User(name="Boss")
        session.add(user)
        await session.commit()

    response = await client.get("/admin/api/user/list")
    assert response.status_code == 200
    data = response.json()
    assert data["searchable"] is True
    assert "name" in data["search_placeholder"]

    response = await client.get("/admin/api/user/list?search=ro")
    assert response.status_code == 200
    data = response.json()
    row_names = [r["name"] for r in data["rows"]]
    assert "Ross" in row_names
    assert "Boss" not in row_names

    response = await client.get("/admin/api/user/list?search=rose")
    assert response.status_code == 200
    data = response.json()
    assert len(data["rows"]) == 0


async def test_sortable_list(client: AsyncClient) -> None:
    async with session_maker() as session:
        user = User(name="Lisa")
        session.add(user)
        await session.commit()

    response = await client.get("/admin/api/user/list?sortBy=id&sort=asc")

    assert response.status_code == 200
    data = response.json()
    id_column = next(c for c in data["columns"] if c["name"] == "id")
    assert id_column["sortable"] is True

    response = await client.get("/admin/api/user/list?sortBy=id&sort=desc")

    assert response.status_code == 200


async def test_export_csv(client: AsyncClient) -> None:
    async with session_maker() as session:
        user = User(name="Daniel", status="ACTIVE")
        session.add(user)
        await session.commit()

    response = await client.get("/admin/api/user/export/csv")
    assert response.text == "name,status\r\nDaniel,ACTIVE\r\n"


async def test_export_csv_row_count(client: AsyncClient) -> None:
    def row_count(resp) -> int:
        return resp.text.count("\r\n") - 1

    async with session_maker() as session:
        for _ in range(20):
            user = User(name="Raymond")
            session.add(user)
            await session.flush()

            address = Address(user_id=user.id)
            session.add(address)

        await session.commit()

    response = await client.get("/admin/api/user/export/csv")
    assert row_count(response) == 20

    response = await client.get("/admin/api/address/export/csv")
    assert row_count(response) == 3


async def test_export_csv_utf8(client: AsyncClient) -> None:
    async with session_maker() as session:
        user_1 = User(name="Daniel", status="ACTIVE")
        user_2 = User(name="دانيال", status="ACTIVE")
        user_3 = User(name="積極的", status="ACTIVE")
        user_4 = User(name="Даниэль", status="ACTIVE")
        session.add(user_1)
        session.add(user_2)
        session.add(user_3)
        session.add(user_4)
        await session.commit()

    response = await client.get("/admin/api/user/export/csv")
    assert response.text == (
        "name,status\r\nDaniel,ACTIVE\r\nدانيال,ACTIVE\r\n"
        "積極的,ACTIVE\r\nДаниэль,ACTIVE\r\n"
    )


async def test_export_json(client: AsyncClient) -> None:
    async with session_maker() as session:
        user = User(name="Daniel", status="ACTIVE")
        session.add(user)
        await session.commit()

    response = await client.get("/admin/api/user/export/json")
    assert response.text == '[{"name": "Daniel", "status": "ACTIVE"}]'


async def test_export_json_utf8(client: AsyncClient) -> None:
    async with session_maker() as session:
        user_1 = User(name="Daniel", status="ACTIVE")
        user_2 = User(name="دانيال", status="ACTIVE")
        user_3 = User(name="積極的", status="ACTIVE")
        user_4 = User(name="Даниэль", status="ACTIVE")
        session.add(user_1)
        session.add(user_2)
        session.add(user_3)
        session.add(user_4)
        await session.commit()

    response = await client.get("/admin/api/user/export/json")
    assert response.text == (
        '[{"name": "Daniel", "status": "ACTIVE"},'
        '{"name": "دانيال", "status": "ACTIVE"},'
        '{"name": "積極的", "status": "ACTIVE"},'
        '{"name": "Даниэль", "status": "ACTIVE"}]'
    )


async def test_export_bad_type_is_404(client: AsyncClient) -> None:
    response = await client.get("/admin/api/user/export/bad_type")
    assert response.status_code == 404


async def test_export_permission_csv(client: AsyncClient) -> None:
    response = await client.get("/admin/api/movie/export/csv")
    assert response.status_code == 403


async def test_export_permission_json(client: AsyncClient) -> None:
    response = await client.get("/admin/api/movie/export/json")
    assert response.status_code == 403
