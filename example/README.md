# spa-sqladmin Example

Exhaustive standalone FastAPI application demonstrating `spa-sqladmin` features.

## Features showcased

- **Authentication** — `SimpleAuthBackend` with username/password
- **Custom branding** — SVG logo in the sidebar, custom favicon, custom title
- **Color palette** — indigo/violet primary color overrides light + dark mode
- **Dark / Light / System mode** — theme switcher in the header (cycles between modes, persisted to localStorage via Zustand)
- **Sidebar collapse** — persisted to localStorage via Zustand
- **7 diverse models** — Users, Categories, Products, Tags, Orders, Order Items, Employees (50-field stress test)
- **Rich column types** — enums, booleans, decimals, JSON, datetimes, many-to-many, self-referential relationships
- **Custom icons** — FA class strings, Lucide names, raw SVG strings

## Setup

Install `spa-sqladmin` from the parent directory (local editable install):

```shell
cd example
pip install -e .
```

Or with `uv`:

```shell
cd example
uv sync
```

## Run

```shell
cd example
uvicorn app:app --port 8091 --reload
```

Then visit **[http://localhost:8091/admin](http://localhost:8091/admin)**.

### Default credentials

| Username | Password  |
|----------|-----------|
| `admin`  | `admin123`|
