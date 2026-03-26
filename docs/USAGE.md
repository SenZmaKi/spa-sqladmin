# Usage Guide

This guide focuses on the parts of `spa-sqladmin` you usually configure first:

- `Admin(...)` constructor parameters
- accepted value types and expected syntax
- branding and theme options
- supported sidebar icon formats
- how to configure a `ModelView` for a resource
- how to add custom admin pages with `BaseView`

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

| Parameter | Expected type | What it does |
| --- | --- | --- |
| `app` | `Starlette` or `FastAPI` app | Your ASGI application. The admin app is mounted into it. |
| `engine` | `Engine` or `AsyncEngine` | SQLAlchemy engine used to build a session maker automatically. |
| `session_maker` | `sessionmaker` or `async_sessionmaker` | Optional custom session factory. Use this when you need to control session creation yourself. |
| `base_url` | `str` | Mount point for the admin UI and API. Defaults to `"/admin"`. |
| `title` | `str` | Used for the browser title and the sidebar heading. |
| `logo_url` | `str \| None` | Image URL shown in the sidebar instead of plain title text. Data URLs also work. |
| `favicon_url` | `str \| None` | Browser-tab favicon URL. Data URLs also work. |
| `color_palette` | `dict[str, dict[str, str]] \| None` | Optional theme token overrides for light and dark mode. |
| `middlewares` | `Sequence[Middleware] \| None` | Extra Starlette middlewares added to the mounted admin app. |
| `debug` | `bool` | Passed to the internal mounted Starlette app as its debug flag. |
| `authentication_backend` | `AuthenticationBackend \| None` | Enables login/logout/auth checks for the admin. |

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

`logo_url` is for the large brand image in the sidebar. It is not the same thing as a menu icon.

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

#### 3. Legacy FontAwesome strings

There is backward-compatibility support for a limited set of FontAwesome class strings. These are translated to a semantically similar Lucide icon.

Examples that work:

- `fa-solid fa-user`
- `fa-solid fa-users`
- `fa-solid fa-box`
- `fa-solid fa-shopping-cart`
- `fa-solid fa-tag`
- `fa-solid fa-envelope`
- `fa-solid fa-calendar`
- `fa-solid fa-database`
- `fa-solid fa-shield`
- `fa-solid fa-heart`
- `fa-solid fa-home`
- `fa-solid fa-credit-card`
- `fa-solid fa-truck`
- `fa-solid fa-dashboard`
- `fa-solid fa-table-columns`
- `fa-solid fa-user-group`

Do not assume arbitrary FontAwesome names will work. Only the specific hardcoded mappings in the frontend are supported.

### Icon fallback behavior

The frontend resolves icons in this order:

1. empty string -> `LayoutDashboard`
2. inline SVG string -> render SVG
3. known FontAwesome mapping -> mapped Lucide icon
4. known Lucide name -> matching Lucide icon
5. unknown value -> `LayoutDashboard`

If you want predictable results, prefer a supported Lucide name or an explicit SVG string.

## Creating a custom admin for a resource with `ModelView`

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

- Prefer Lucide icon names over FontAwesome strings.
- Use inline SVG strings when you need a brand-specific or custom icon.
- Keep `color_palette` values in Tailwind-style HSL tokens.
- Use `ModelView` for model resources and `BaseView` for custom pages.
- If you already have a session factory pattern in your app, pass `session_maker` explicitly.
- Prefer `admin.add_view(...)` unless you specifically want `add_model_view(...)` or `add_base_view(...)`.

## Complete example

The repository's `example/` app demonstrates:

- custom `title`
- SVG data URL `logo_url`
- SVG data URL `favicon_url`
- light and dark `color_palette`
- Lucide icons
- legacy FontAwesome icon strings
- raw SVG sidebar icons
- multiple `ModelView` resources

If you want a working reference, start there after reading this guide.
