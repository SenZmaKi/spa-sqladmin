"""
Example spa-sqladmin application — exhaustive feature showcase.

Demonstrates:
- SimpleAuthBackend (username/password in-memory auth)
- Custom app title, logo (SVG data URL), favicon (SVG data URL)
- Custom color palette (indigo/violet theme) for light + dark mode
- Dark / light / system mode switcher in the UI header
- Sidebar collapse state persisted via Zustand
- All ModelView features across 7 diverse models

Run from the example/ directory:
    uvicorn app:app --port 8091 --reload

Then visit:
    http://localhost:8091/admin          → redirects to login
    http://localhost:8091/admin/login    → login page
    Credentials: admin / admin123
"""

import base64

from fastapi import FastAPI

from spa_sqladmin import Admin, SimpleAuthBackend

from admin import (
    CategoryAdmin,
    EmployeeAdmin,
    OrderAdmin,
    OrderItemAdmin,
    ProductAdmin,
    TagAdmin,
    UserAdmin,
)
from db import Base, engine
from seed import seed_database

# ---------------------------------------------------------------------------
# App icon assets (inline SVG data URLs — no external dependencies)
# ---------------------------------------------------------------------------

_LOGO_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" fill="none">
  <rect width="48" height="48" rx="12" fill="#4f46e5"/>
  <path d="M14 20h20l-2 13H16L14 20z" fill="white" opacity="0.9"/>
  <path d="M18 20c0-3.314 2.686-6 6-6s6 2.686 6 6"
        stroke="white" stroke-width="2.5" fill="none" stroke-linecap="round"/>
  <circle cx="19" cy="37" r="1.5" fill="#4f46e5"/>
  <circle cx="29" cy="37" r="1.5" fill="#4f46e5"/>
</svg>"""

_FAVICON_SVG = _LOGO_SVG

STORE_LOGO_URL = f"data:image/svg+xml;base64,{base64.b64encode(_LOGO_SVG).decode()}"
STORE_FAVICON_URL = f"data:image/svg+xml;base64,{base64.b64encode(_FAVICON_SVG).decode()}"

# ---------------------------------------------------------------------------
# Custom color palette — indigo/violet theme
# Consumers supply HSL values matching Tailwind's CSS-variable format.
# Only override the vars you want to change; the rest fall back to defaults.
# ---------------------------------------------------------------------------
STORE_PALETTE = {
    "light": {
        "primary": "239 84% 67%",            # indigo-500
        "primary-foreground": "0 0% 100%",
        "ring": "239 84% 67%",
    },
    "dark": {
        "primary": "243 75% 70%",            # softer indigo for dark bg
        "primary-foreground": "0 0% 100%",
        "ring": "243 75% 70%",
    },
}

# ---------------------------------------------------------------------------
# FastAPI app + spa-sqladmin Admin
# ---------------------------------------------------------------------------
app = FastAPI(title="My Store — spa-sqladmin demo")

auth = SimpleAuthBackend(
    secret_key="change-me-in-production-please",
    credentials={"admin": "admin123"},
)

admin = Admin(
    app,
    engine,
    title="My Store Admin",
    logo_url=STORE_LOGO_URL,
    favicon_url=STORE_FAVICON_URL,
    color_palette=STORE_PALETTE,
    authentication_backend=auth,
)

admin.add_view(UserAdmin)
admin.add_view(CategoryAdmin)
admin.add_view(ProductAdmin)
admin.add_view(TagAdmin)
admin.add_view(OrderAdmin)
admin.add_view(OrderItemAdmin)
admin.add_view(EmployeeAdmin)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(engine)
    seed_database()


@app.get("/")
def index():
    return {"message": "Visit /admin — log in with admin / admin123"}
