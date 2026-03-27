"""Admin view configuration for the example app."""

from sqlalchemy import func, select
from starlette.requests import Request
from starlette.responses import JSONResponse
from spa_sqladmin import LinkView, ModelView
from db import SessionLocal
from models import Order, Product, User


class UserAdmin(ModelView, model=User):
    category = "Models"
    name = "User"
    name_plural = "Users"
    icon = "Users"
    column_list = [
        User.id,
        User.username,
        User.email,
        User.role,
        User.is_active,
        User.created_at,
    ]
    column_searchable_list = [User.username, User.email]
    column_sortable_list = [User.id, User.username, User.created_at]
    form_excluded_columns = [User.created_at, User.orders]


class ProductAdmin(ModelView, model=Product):
    category = "Models"
    name = "Product"
    name_plural = "Products"
    icon = "Package"
    column_list = [
        Product.id,
        Product.name,
        Product.price,
        Product.stock,
        Product.is_active,
    ]
    column_searchable_list = [Product.name]
    column_sortable_list = [Product.id, Product.name, Product.price, Product.stock]
    form_excluded_columns = [Product.created_at]


class OrderAdmin(ModelView, model=Order):
    category = "Models"
    name = "Order"
    name_plural = "Orders"
    icon = "ShoppingCart"
    column_list = [Order.id, Order.status, Order.total, Order.user, Order.created_at]
    column_sortable_list = [Order.id, Order.total, Order.created_at]
    form_excluded_columns = [Order.created_at]


class StatsView(LinkView):
    """Protected stats endpoint — served directly through the admin."""

    name = "Stats"
    icon = "BarChart2"
    category = "Internal"
    category_icon = "Lock"

    async def get_response(self, request: Request) -> JSONResponse:
        with SessionLocal() as session:
            users = session.execute(select(func.count()).select_from(User)).scalar()
            products = session.execute(
                select(func.count()).select_from(Product)
            ).scalar()
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
