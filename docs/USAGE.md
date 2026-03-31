# Usage Guide

This guide focuses on the parts of `spa-sqladmin` you usually configure first:

- `Admin(...)` constructor parameters
- accepted value types and expected syntax
- branding and theme options
- supported sidebar icon formats
- how to configure a `ModelView` for a resource (including enums, relationships, and formatters)
- how to add custom admin pages and stats endpoints with `BaseView` and `LinkView`

For generated API docs, also see the [Application API reference](api_reference/application.md), [ModelView API reference](api_reference/model_view.md), and [BaseView API reference](api_reference/base_view.md).

## Quickstart mental model

`spa-sqladmin` has three main pieces:

1. `Admin(...)` mounts the admin SPA and API into your Starlette/FastAPI app.
2. `ModelView` classes describe how a SQLAlchemy model should appear in the admin.
3. `BaseView` classes add custom pages or endpoints that are not tied to a single model.

Typical usage looks like this:

```python
from fastapi import FastAPI
from sqlalchemy import create_engine
from spa_sqladmin import Admin, ModelView

from .models import User

app = FastAPI()
engine = create_engine("sqlite:///example.db", connect_args={"check_same_thread": False})


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.name]


admin = Admin(app, engine, title="My Admin")
admin.add_view(UserAdmin)
```

## `Admin(...)` parameters

The public constructor is:

```python
Admin(
    app,
    engine=None,
    session_maker=None,
    base_url="/admin",
    title="Admin",
    logo_url=None,
    favicon_url=None,
    color_palette=None,
    middlewares=None,
    debug=False,
    authentication_backend=None,
)
```

### Parameter reference

| Parameter                | Expected type                          | What it does                                                                                  |
| ------------------------ | -------------------------------------- | --------------------------------------------------------------------------------------------- |
| `app`                    | `Starlette` or `FastAPI` app           | Your ASGI application. The admin app is mounted into it.                                      |
| `engine`                 | `Engine` or `AsyncEngine`              | SQLAlchemy engine used to build a session maker automatically.                                |
| `session_maker`          | `sessionmaker` or `async_sessionmaker` | Optional custom session factory. Use this when you need to control session creation yourself. |
| `base_url`               | `str`                                  | Mount point for the admin UI and API. Defaults to `"/admin"`.                                 |
| `title`                  | `str`                                  | Used for the browser title and the sidebar heading.                                           |
| `logo_url`               | `str \| None`                          | Image URL shown in the sidebar alongside the title. Data URLs also work.                      |
| `favicon_url`            | `str \| None`                          | Browser-tab favicon URL. Data URLs also work.                                                 |
| `color_palette`          | `dict[str, dict[str, str]] \| None`    | Optional theme token overrides for light and dark mode.                                       |
| `middlewares`            | `Sequence[Middleware] \| None`         | Extra Starlette middlewares added to the mounted admin app.                                   |
| `debug`                  | `bool`                                 | Passed to the internal mounted Starlette app as its debug flag.                               |
| `authentication_backend` | `AuthenticationBackend \| None`        | Enables login/logout/auth checks for the admin.                                               |

### `engine` vs `session_maker`

Use one of these patterns:

```python
admin = Admin(app, engine)
```

or:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

Session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
admin = Admin(app, session_maker=Session)
```

In practice, you should provide either `engine` or `session_maker`. If you provide `session_maker`, it takes precedence.

### `base_url`

`base_url` changes both the UI and API paths.

```python
admin = Admin(app, engine, base_url="/dashboard")
```

With that configuration:

- the SPA lives under `/dashboard`
- the API lives under `/dashboard/api/...`
- static admin assets live under `/dashboard/statics/...`

### `middlewares`

`middlewares` are applied to the admin sub-application, not the whole parent app.

```python
from starlette.middleware import Middleware

admin = Admin(
    app,
    engine,
    middlewares=[Middleware(MyAdminOnlyMiddleware)],
)
```

### `authentication_backend`

If you pass an authentication backend, both the SPA and API require auth.

```python
from spa_sqladmin import Admin, SimpleAuthBackend

auth = SimpleAuthBackend(
    secret_key="change-me",
    credentials={"admin": "admin123"},
)

admin = Admin(app, engine, authentication_backend=auth)
```

`SimpleAuthBackend` is the built-in option for simple username/password auth. You can also provide your own subclass of `AuthenticationBackend`.

## Branding parameters

### `title`

```python
admin = Admin(app, engine, title="My Store Admin")
```

This value is used in the HTML title and in the admin site metadata returned to the SPA.

### `logo_url`

`logo_url` is for the brand image in the sidebar. When provided, it is shown alongside the `title` text — both are visible at the same time. It is not the same thing as a menu icon.

Accepted values:

- absolute URLs like `https://example.com/logo.svg`
- relative/static URLs your app serves
- data URLs, including inline SVG data URLs

```python
import base64

logo_svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">...</svg>'
logo_url = f"data:image/svg+xml;base64,{base64.b64encode(logo_svg).decode()}"

admin = Admin(app, engine, logo_url=logo_url)
```

### `favicon_url`

`favicon_url` controls the browser tab icon.

```python
admin = Admin(app, engine, favicon_url="https://example.com/favicon.ico")
```

SVG data URLs work here too:

```python
import base64

favicon_svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">...</svg>'
favicon_url = f"data:image/svg+xml;base64,{base64.b64encode(favicon_svg).decode()}"

admin = Admin(app, engine, favicon_url=favicon_url)
```

## `color_palette` syntax

`color_palette` lets you override the CSS custom properties used by the React admin UI.

The expected shape is:

```python
color_palette = {
    "light": {
        "primary": "239 84% 67%",
        "primary-foreground": "0 0% 100%",
        "ring": "239 84% 67%",
    },
    "dark": {
        "primary": "243 75% 70%",
        "primary-foreground": "0 0% 100%",
        "ring": "243 75% 70%",
    },
}
```

Then:

```python
admin = Admin(app, engine, color_palette=color_palette)
```

### Color format

For the color tokens, use **space-separated HSL components**, not `hsl(...)`.

Use this:

```python
"239 84% 67%"
```

Do not use this:

```python
"hsl(239, 84%, 67%)"
```

### Supported palette keys

The built-in frontend theme defines these CSS variables:

- `background`
- `foreground`
- `card`
- `card-foreground`
- `popover`
- `popover-foreground`
- `primary`
- `primary-foreground`
- `secondary`
- `secondary-foreground`
- `muted`
- `muted-foreground`
- `accent`
- `accent-foreground`
- `destructive`
- `destructive-foreground`
- `border`
- `input`
- `ring`
- `radius`

You only need to override the keys you care about.

### A note on `radius`

`radius` is also part of the palette object, but it is not a color token. It is used as a raw CSS variable value, so it should be a normal CSS length such as:

```python
"0.5rem"
```

### Partial palettes are allowed

You can override only `light`, only `dark`, or just a few variables inside either mode.

```python
admin = Admin(
    app,
    engine,
    color_palette={
        "light": {
            "primary": "160 84% 39%",
            "primary-foreground": "0 0% 100%",
        }
    },
)
```

Any variables you do not provide continue using the built-in defaults.

## Sidebar icons

The `icon` and `category_icon` fields on `ModelView` and `BaseView` are plain strings, but the frontend only understands specific string formats.

These fields are used here:

```python
class UserAdmin(ModelView, model=User):
    icon = "Users"
    category = "Accounts"
    category_icon = "Shield"
```

### Supported icon formats

#### 1. Lucide icon names

This is the recommended format.

```python
class ProductAdmin(ModelView, model=Product):
    icon = "Package"
```

Important details:

- the value must match a supported icon name from the frontend's `lucide-react` subset
- matching is case-insensitive
- unknown names silently fall back to `LayoutDashboard`

The current supported Lucide names are:

`Users`, `Package`, `Settings`, `FileText`, `ShoppingCart`, `Tag`, `Mail`, `Globe`, `Image`, `MessageSquare`, `Calendar`, `Database`, `Shield`, `Star`, `Heart`, `BookOpen`, `Folder`, `Home`, `Bell`, `Map`, `CreditCard`, `Truck`, `LayoutDashboard`, `Activity`, `AlertCircle`, `AlertTriangle`, `Archive`, `Award`, `BarChart`, `BarChart2`, `BarChart3`, `Bookmark`, `Box`, `Briefcase`, `Building`, `Building2`, `Camera`, `Check`, `CheckCircle`, `Circle`, `Clipboard`, `Clock`, `Cloud`, `Code`, `Cog`, `Compass`, `Copy`, `DollarSign`, `Download`, `Edit`, `Eye`, `EyeOff`, `File`, `Film`, `Filter`, `Flag`, `Gift`, `Hash`, `Headphones`, `HelpCircle`, `Inbox`, `Info`, `Key`, `Layers`, `Layout`, `Link`, `List`, `Lock`, `LogIn`, `LogOut`, `MapPin`, `Megaphone`, `Menu`, `Mic`, `Monitor`, `Moon`, `MoreHorizontal`, `Music`, `Navigation`, `Paperclip`, `Pen`, `Phone`, `PieChart`, `Pin`, `Play`, `Plus`, `Printer`, `Radio`, `RefreshCw`, `Repeat`, `Rocket`, `RotateCw`, `Rss`, `Save`, `Scissors`, `Search`, `Send`, `Server`, `Share`, `ShieldCheck`, `Smartphone`, `Speaker`, `Sun`, `Table`, `Target`, `Terminal`, `ThumbsUp`, `ThumbsDown`, `Hammer`, `Trash`, `Trash2`, `TrendingUp`, `TrendingDown`, `Upload`, `User`, `UserCheck`, `UserPlus`, `UserX`, `Video`, `Wallet`, `Wifi`, `Wrench`, `X`, `Zap`, `ZoomIn`, `ZoomOut`, `GitBranch`, `GitCommit`, `GitMerge`, `GitPullRequest`, `Github`, `Cpu`, `HardDrive`, `MemoryStick`, `Plug`, `Power`, `QrCode`, `Scan`, `Usb`, `Car`, `Bike`, `Bus`, `Plane`, `Ship`, `Train`

#### 2. Raw SVG strings

You can provide the full SVG markup as the icon string.

```python
BOX_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"'
    ' fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"'
    ' stroke-linejoin="round"><path d="M12 2 2 7l10 5 10-5-10-5Z"/>'
    '<path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/></svg>'
)


class CategoryAdmin(ModelView, model=Category):
    icon = BOX_SVG
```

Rules:

- the string must start with `<svg`
- it should be valid inline SVG markup
- the frontend injects sizing classes when rendering it

#### 3. Legacy FontAwesome strings (removed)

### Icon fallback behavior

The frontend resolves icons in this order:

1. empty string → `LayoutDashboard`
2. inline SVG string → render SVG
3. known Lucide name (case-insensitive) → matching Lucide icon
4. unknown value → `LayoutDashboard`

If you want predictable results, prefer a supported Lucide name or an explicit SVG string.

## Adding custom views with `LinkView`

`LinkView` lets you expose any response — JSON, HTML, a redirect — as a named
sidebar entry inside the admin, gated behind admin authentication.

### Serving custom content (`get_response`)

Override `get_response(self, request)` to return any response. The admin
registers a route at `/{base_url}/{identity}` that:

1. Checks admin authentication (unauthenticated users → login page).
2. Calls your `get_response` and returns the result.

```python
from spa_sqladmin import LinkView
from starlette.requests import Request
from starlette.responses import JSONResponse

class StoreStats(LinkView):
    name = "Stats"
    icon = "BarChart2"
    category = "Internal"
    category_icon = "Lock"

    async def get_response(self, request: Request) -> JSONResponse:
        return JSONResponse({"users": 42, "orders": 128})

admin.add_view(StoreStats)
```

You can also query the database directly inside `get_response`. Use your own
`sessionmaker` (the same one you pass to `Admin`) and run any SQLAlchemy query:

```python
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker
from spa_sqladmin import LinkView
from starlette.requests import Request
from starlette.responses import JSONResponse

from db import SessionLocal  # your sessionmaker
from models import Order, Product, User


class StatsView(LinkView):
    name = "Stats"
    icon = "BarChart2"
    category = "Internal"
    category_icon = "Lock"

    async def get_response(self, request: Request) -> JSONResponse:
        with SessionLocal() as session:
            users = session.execute(select(func.count()).select_from(User)).scalar()
            products = session.execute(select(func.count()).select_from(Product)).scalar()
            orders = session.execute(select(func.count()).select_from(Order)).scalar()
            revenue = session.execute(select(func.sum(Order.total))).scalar() or 0.0
        return JSONResponse(
            {
                "users": users,
                "products": products,
                "orders": orders,
                "total_revenue": round(float(revenue), 2),
            }
        )

admin.add_view(StatsView)
```

### External redirect (`url`)

Set `url` without overriding `get_response` to create an auth-gated redirect.
Unauthenticated users are sent to the login page first; authenticated users are
forwarded to the URL.

```python
class AnalyticsLink(LinkView):
    name = "Analytics"
    icon = "BarChart"
    url = "https://analytics.example.com"
    category = "External"
    category_icon = "Link"

admin.add_view(AnalyticsLink)
```

Use `target` to control how the link opens. Set `target = "_blank"` to open the
URL in a new tab — `rel="noopener noreferrer"` is added automatically by the
frontend:

```python
class AnalyticsLink(LinkView):
    name = "Analytics"
    icon = "BarChart"
    url = "https://analytics.example.com"
    target = "_blank"   # open in new tab
    category = "External"
    category_icon = "Link"

admin.add_view(AnalyticsLink)
```

### Embedding API docs (`embed_docs`)

Pass `embed_docs=True` to `Admin` to add `/docs`, `/redoc`,
and `/openapi.json` to the admin sidebar.

```python
admin = Admin(app, engine, authentication_backend=auth, embed_docs=True)
# optional: custom page title
# admin = Admin(..., embed_docs=True, docs_title="My API")
```

When an `authentication_backend` is configured, the endpoints are gated behind
admin auth — unauthenticated requests are redirected to the login page. The
existing FastAPI doc routes are replaced with auth-checking handlers that call
FastAPI's own `get_swagger_ui_html` / `get_redoc_html` / `app.openapi()`.

Without an `authentication_backend`, the sidebar entries are added as plain
links and the original FastAPI doc routes are left untouched.

A complete setup using `SimpleAuthBackend` and `embed_docs` together:

```python
from fastapi import FastAPI
from spa_sqladmin import Admin, SimpleAuthBackend

app = FastAPI(title="My App")

auth = SimpleAuthBackend(
    secret_key="change-me-in-production",
    credentials={"admin": "password"},
)

admin = Admin(
    app,
    engine,
    title="My Admin",
    authentication_backend=auth,
    embed_docs=True,
)
```

### `LinkView` attributes

| Attribute | Default | Description |
|-----------|---------|-------------|
| `url` | `""` | External URL to redirect to (when `get_response` is not overridden). |
| `target` | `""` | HTML `target` attribute for the sidebar and dashboard link (e.g. `"_blank"` to open in a new tab). `rel="noopener noreferrer"` is added automatically when `target="_blank"`. |
| `name` | class name | Display name shown in the sidebar. |
| `icon` | `""` | Lucide icon name or inline SVG string. |
| `identity` | slugified class name | URL segment for the admin route (`/{base_url}/{identity}`). |
| `category` | `""` | Optional category to group this link under. |
| `category_icon` | `""` | Icon for the category group. |

`ModelView` is the standard way to customize how a database resource appears in the admin.

```python
from spa_sqladmin import ModelView


class UserAdmin(ModelView, model=User):
    name = "User"
    name_plural = "Users"
    icon = "Users"
    category = "Accounts"
    category_icon = "Shield"

    can_create = True
    can_edit = True
    can_delete = False
    can_view_details = True
    can_export = True

    column_list = [User.id, User.username, User.email, User.is_active]
    column_details_list = [
        User.id,
        User.username,
        User.email,
        User.full_name,
        User.is_active,
        User.created_at,
    ]
    column_searchable_list = [User.username, User.email]
    column_sortable_list = [User.id, User.username, User.created_at]
    page_size = 25
    page_size_options = [25, 50, 100]

    form_excluded_columns = [User.created_at, User.updated_at]


admin.add_view(UserAdmin)
```

### Displaying relationship columns

You can include a relationship attribute directly in `column_list` or `column_details_list`.
spa-sqladmin will call `str()` on the related object, so make sure your model defines `__str__`.

```python
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    status = Column(Enum(OrderStatus))
    total = Column(Float)
    user = relationship("User", back_populates="orders")

    def __str__(self) -> str:
        return f"Order #{self.id}"


class OrderAdmin(ModelView, model=Order):
    column_list = [Order.id, Order.status, Order.total, Order.user, Order.created_at]
    column_sortable_list = [Order.id, Order.total, Order.created_at]
    form_excluded_columns = [Order.created_at]
```

`Order.user` in `column_list` will render each row's user as its `__str__` value.

### Enum columns

SQLAlchemy `Enum` columns are supported out of the box. Values are shown and edited
using a select widget populated with the enum members.

```python
import enum
from sqlalchemy import Column, Enum

class Role(str, enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    role = Column(Enum(Role), default=Role.VIEWER, nullable=False)


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.role]
```

### Column formatters

`column_formatters` lets you customize how a value is rendered in the list page.
Each value is a callable that receives `(model_instance, attribute_name)` and returns
a string (or any JSON-serialisable value).

```python
class ProductAdmin(ModelView, model=Product):
    column_list = [Product.id, Product.name, Product.price, Product.is_active]
    column_formatters = {
        Product.price: lambda m, a: f"${m.price:,.2f}",
        Product.is_active: lambda m, a: "✓" if m.is_active else "✗",
    }
```


### Important `ModelView` behaviors

- `model` is required and must be a real SQLAlchemy model
- `identity` is generated from the model class name unless you override it
- `name` defaults to a prettified model name
- `name_plural` defaults to `f"{name}s"`
- `column_list` and `column_exclude_list` are mutually exclusive
- `form_columns` and `form_excluded_columns` are mutually exclusive
- `column_details_list` and `column_details_exclude_list` are mutually exclusive
- `column_export_list` and `column_export_exclude_list` are mutually exclusive

### Accepted field syntax in lists

Most field configuration lists accept either:

- SQLAlchemy attributes like `User.email`
- string paths like `"profile.display_name"`

For example:

```python
class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, "profile.display_name"]
```

### Search placeholder text

The search box placeholder is built automatically from `column_searchable_list` and your column labels.

```python
class UserAdmin(ModelView, model=User):
    column_labels = {"name": "Name", "email": "Email"}
    column_searchable_list = [User.name, User.email]
```

This produces a placeholder like:

```text
Name, Email
```

## Custom admin pages with `BaseView`

Use `BaseView` when you want a custom page, report endpoint, or dashboard entry that is not just CRUD for a single model.

```python
from spa_sqladmin import BaseView, expose
from starlette.responses import JSONResponse


class ReportView(BaseView):
    name = "Reports"
    icon = "BarChart3"
    category = "Analytics"
    category_icon = "BarChart"

    @expose("/reports", methods=["GET"])
    async def reports(self, request):
        return JSONResponse({"status": "ok"})


admin.add_view(ReportView)
```

### `@expose(...)`

`@expose(...)` creates custom routes on admin views.

```python
@expose(
    "/reports/{id}",
    methods=["GET"],
    identity="report-detail",
    include_in_schema=True,
)
async def report_detail(self, request):
    ...
```

Arguments:

- `path: str`
- `methods: list[str] | None`
- `identity: str | None`
- `include_in_schema: bool`

For `ModelView`, the path is automatically prefixed with that resource's identity.

For example:

```python
class UserAdmin(ModelView, model=User):
    @expose("/profile/{pk}", methods=["GET"])
    async def profile(self, request):
        ...
```

That becomes a route under the user's admin area rather than a top-level app route.

## Custom actions on a `ModelView`

Use `@action(...)` when you want a button in the list or detail page.

```python
from spa_sqladmin import action
from starlette.responses import JSONResponse


class UserAdmin(ModelView, model=User):
    @action(
        name="mark-active",
        label="Mark active",
        confirmation_message="Mark the selected users as active?",
        add_in_list=True,
        add_in_detail=True,
    )
    async def mark_active(self, request):
        pks = request.query_params.get("pks", "")
        selected_ids = [pk for pk in pks.split(",") if pk]
        return JSONResponse({"selected_ids": selected_ids})
```

Notes:

- `name` is slugified for the route
- `label` defaults to `name` if omitted
- list/detail buttons can be enabled separately
- the admin passes selected primary keys in the `pks` query parameter

## Database access inside custom views

If you need database access in a `BaseView`, use the admin's session maker or your own explicit session maker.

```python
from sqlalchemy import func, select
from starlette.responses import JSONResponse


class ReportView(BaseView):
    name = "Reports"
    icon = "BarChart3"

    @expose("/reports", methods=["GET"])
    async def reports(self, request):
        async with self._admin_ref.session_maker(expire_on_commit=False) as session:
            result = await session.execute(select(func.count(User.id)))
            user_count = result.scalar_one()

        return JSONResponse({"user_count": user_count})
```

If your project uses synchronous sessions, use the equivalent sync session pattern instead.

## Practical recommendations

- Prefer Lucide icon names over inline SVG strings for simplicity.
- Use inline SVG strings when you need a brand-specific or custom icon.
- Keep `color_palette` values in Tailwind-style HSL tokens.
- Use `ModelView` for model resources and `BaseView` for custom pages.
- If you already have a session factory pattern in your app, pass `session_maker` explicitly.
- Prefer `admin.add_view(...)` unless you specifically want `add_model_view(...)` or `add_base_view(...)`.

## Complete example

The repository's `example/` directory contains a fully-wired FastAPI app
that demonstrates:

- `SimpleAuthBackend` with `credentials` and `embed_docs`
- `title` customization
- Multiple `ModelView` resources with icons, categories, search, sort, and `form_excluded_columns`
- Enum columns (displayed as readable enum values)
- Relationship columns displayed directly in `column_list` (e.g. `Order.user`)
- A `LinkView` subclass (`StatsView`) that queries the database and returns JSON

To run the example:

```shell
cd example
uv run uvicorn app:app --port 8091 --reload
# or: pip install -e .. && uvicorn app:app --port 8091 --reload
```

Then visit:

| URL | Description |
|-----|-------------|
| `http://localhost:8091/admin` | Admin UI (redirects to login) |
| `http://localhost:8091/admin/login` | Login — use `admin` / `password` |
| `http://localhost:8091/docs` | Swagger UI (auth-gated via `embed_docs=True`) |

Start there for a working reference after reading this guide.
