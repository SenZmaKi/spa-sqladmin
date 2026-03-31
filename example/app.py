"""
spa-sqladmin example application.

Run from the example/ directory:
    uvicorn app:app --port 8091 --reload

Then visit:
    http://localhost:8091/admin       → redirects to login
    http://localhost:8091/admin/login → login page (admin / password)
    http://localhost:8091/docs        → Swagger UI (requires login)
    http://localhost:8091/redoc       → ReDoc (requires login)
"""

import base64

from fastapi import FastAPI

from spa_sqladmin import Admin, SimpleAuthBackend

from admin import GitHubLink, OrderAdmin, ProductAdmin, StatsView, UserAdmin
from db import Base, engine
from seed import seed_database

app = FastAPI(title="spa-sqladmin demo")

auth = SimpleAuthBackend(
    secret_key="change-me-in-production",
    credentials={"admin": "password"},
)

# -- Cart SVG icon (used as both favicon and logo) --------------------------
_CART_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" fill="none"'
    b' stroke="#7c3aed" stroke-width="2" stroke-linecap="round"'
    b' stroke-linejoin="round">'
    b'<circle cx="12" cy="27" r="2"/>'
    b'<circle cx="25" cy="27" r="2"/>'
    b'<path d="M3 3h4l3.68 16.39a2 2 0 0 0 1.99 1.61h9.72a2 2 0 0 0'
    b' 1.99-1.61L27 8H9"/>'
    b"</svg>"
)
_CART_DATA_URL = f"data:image/svg+xml;base64,{base64.b64encode(_CART_SVG).decode()}"

admin = Admin(
    app,
    engine,
    title="Store Admin",
    authentication_backend=auth,
    embed_docs=True,
    logo_url=_CART_DATA_URL,
    favicon_url=_CART_DATA_URL,
    color_palette={
        "light": {
            "primary": "239 84% 67%",
            "primary-foreground": "0 0% 100%",
            "ring": "239 84% 67%",
            "accent": "239 84% 95%",
            "accent-foreground": "239 84% 30%",
        },
        "dark": {
            "primary": "243 75% 70%",
            "primary-foreground": "0 0% 100%",
            "ring": "243 75% 70%",
            "accent": "243 30% 20%",
            "accent-foreground": "243 75% 85%",
        },
    },
    font_config={
        "url": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
        "family": "'Inter', sans-serif",
    },
)

admin.add_view(UserAdmin)
admin.add_view(ProductAdmin)
admin.add_view(OrderAdmin)
admin.add_view(StatsView)
admin.add_view(GitHubLink)



@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(engine)
    seed_database()


@app.get("/")
def index():
    return {"message": "Visit /admin — log in with admin / password"}
