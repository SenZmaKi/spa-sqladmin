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

from fastapi import FastAPI

from spa_sqladmin import Admin, SimpleAuthBackend

from admin import OrderAdmin, ProductAdmin, StatsView, UserAdmin
from db import Base, engine
from seed import seed_database

app = FastAPI(title="spa-sqladmin demo")

auth = SimpleAuthBackend(
    secret_key="change-me-in-production",
    credentials={"admin": "password"},
)

admin = Admin(
    app,
    engine,
    title="Store Admin",
    authentication_backend=auth,
    embed_docs=True,
)

admin.add_view(UserAdmin)
admin.add_view(ProductAdmin)
admin.add_view(OrderAdmin)
admin.add_view(StatsView)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(engine)
    seed_database()


@app.get("/")
def index():
    return {"message": "Visit /admin — log in with admin / password"}
