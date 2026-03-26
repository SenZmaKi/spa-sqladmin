<p align="center">
<a href="https://github.com/senzmaki/spa-sqladmin">
    <img width="400px" src="https://raw.githubusercontent.com/senzmaki/spa-sqladmin/main/docs/assets/images/banner.jpg" alt"SQLAdmin">
</a>
</p>

<p align="center">
<a href="https://github.com/senzmaki/spa-sqladmin/actions">
    <img src="https://github.com/senzmaki/spa-sqladmin/workflows/Test%20Suite/badge.svg" alt="Build Status">
</a>
</p>

---

# spa-sqladmin: React SPA Admin for Starlette/FastAPI

`spa-sqladmin` is a modern React SPA rewrite of [sqladmin](https://github.com/aminalaee/sqladmin) providing a better UI/UX.

Main features include:

- [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) sync/async engines
- [Starlette](https://github.com/encode/starlette) integration
- [FastAPI](https://github.com/tiangolo/fastapi) integration
- [SQLModel](https://github.com/tiangolo/sqlmodel) support
- Modern React SPA UI with [Shadcn UI](https://ui.shadcn.com/), [Tanstack Router](https://tanstack.com/router), [Tanstack Table](https://tanstack.com/table), and [Tanstack Query](https://tanstack.com/query)

---

## Installation

Install directly from GitHub:

```shell
$ pip install git+https://github.com/SenZmaKi/spa-sqladmin.git
```

With optional dependencies:

```shell
$ pip install "spa-sqladmin[full] @ git+https://github.com/SenZmaKi/spa-sqladmin.git"
```

Or with `uv`:

```shell
$ uv add "spa-sqladmin @ git+https://github.com/SenZmaKi/spa-sqladmin.git"
```

---

## Screenshots

<img width="1492" alt="spa-sqladmin-screenshot-1" src="https://raw.githubusercontent.com/SenZmaKi/spa-sqladmin/main/docs/assets/images/screenshot-1.png">
<img width="1492" alt="spa-sqladmin-screenshot-2" src="https://raw.githubusercontent.com/SenZmaKi/spa-sqladmin/main/docs/assets/images/screenshot-2.png">

## Quickstart

Let's define an example SQLAlchemy model:

```python
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base


Base = declarative_base()
engine = create_engine(
    "sqlite:///example.db",
    connect_args={"check_same_thread": False},
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)


Base.metadata.create_all(engine)  # Create tables
```

If you want to use `SQLAdmin` with `FastAPI`:

```python
from fastapi import FastAPI
from spa_sqladmin import Admin, ModelView


app = FastAPI()
admin = Admin(app, engine)


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.name]


admin.add_view(UserAdmin)
```

Or if you want to use `SQLAdmin` with `Starlette`:

```python
from spa_sqladmin import Admin, ModelView
from starlette.applications import Starlette


app = Starlette()
admin = Admin(app, engine)


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.name]


admin.add_view(UserAdmin)
```

Now visiting `/admin` on your browser you can see the `SQLAdmin` interface.

Find an extensive example in the [example](https://github.com/SenZmaKi/spa-sqladmin/tree/main/example) folder.

For a full overview of `Admin(...)` parameters, icon formats, palette syntax, and custom admin patterns, see [`docs/USAGE.md`](docs/USAGE.md).

## Acknowledgements

This project would not have been possible without [sqladmin](https://github.com/aminalaee/sqladmin).
