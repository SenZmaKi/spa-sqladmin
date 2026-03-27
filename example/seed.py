"""Seed the example database with demo data."""

import random
from datetime import datetime, timedelta
from db import SessionLocal
from models import Order, OrderStatus, Product, Role, User


def seed_database() -> None:
    with SessionLocal() as session:
        if session.query(User).count() > 0:
            return  # already seeded

        users = [
            User(
                username="alice",
                email="alice@example.com",
                role=Role.ADMIN,
                is_active=True,
            ),
            User(
                username="bob",
                email="bob@example.com",
                role=Role.EDITOR,
                is_active=True,
            ),
            User(
                username="carol",
                email="carol@example.com",
                role=Role.VIEWER,
                is_active=False,
            ),
            User(
                username="dave",
                email="dave@example.com",
                role=Role.EDITOR,
                is_active=True,
            ),
            User(
                username="eve",
                email="eve@example.com",
                role=Role.VIEWER,
                is_active=True,
            ),
        ]
        session.add_all(users)

        products = [
            Product(name="Laptop Pro", price=1299.99, stock=15, is_active=True),
            Product(name="Wireless Mouse", price=29.99, stock=100, is_active=True),
            Product(name="USB-C Hub", price=49.99, stock=60, is_active=True),
            Product(name="Mechanical Keyboard", price=89.99, stock=40, is_active=True),
            Product(name="4K Monitor", price=399.99, stock=8, is_active=False),
            Product(name="Webcam HD", price=69.99, stock=25, is_active=True),
            Product(name="Standing Desk", price=549.99, stock=5, is_active=True),
            Product(name="Desk Lamp", price=34.99, stock=0, is_active=False),
        ]
        session.add_all(products)
        session.flush()

        statuses = list(OrderStatus)
        for i, user in enumerate(users):
            for j in range(random.randint(1, 4)):
                order = Order(
                    status=statuses[(i + j) % len(statuses)],
                    total=round(random.uniform(20, 600), 2),
                    user_id=user.id,
                    created_at=datetime.utcnow()
                    - timedelta(days=random.randint(0, 90)),
                )
                session.add(order)

        session.commit()
