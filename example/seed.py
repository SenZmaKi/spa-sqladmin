"""Populate the database with realistic sample data."""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from db import SessionLocal
from models import (
    Category,
    Continent,
    Department,
    Employee,
    Order,
    OrderItem,
    OrderStatus,
    Priority,
    Product,
    ProductStatus,
    Tag,
    User,
    UserRole,
)


def seed_database() -> None:
    session = SessionLocal()
    try:
        if session.query(User).count() > 0:
            return

        _seed_users(session)
        categories = _seed_categories(session)
        tags = _seed_tags(session)
        products = _seed_products(session, categories)
        users = session.query(User).all()
        _seed_orders(session, users, products, tags)
        _seed_employees(session)

        session.commit()
        print("✓ Database seeded with sample data")
    except Exception as e:
        session.rollback()
        print(f"Seeding error: {e}")
        raise
    finally:
        session.close()


# ── Users ────────────────────────────────────────────────────────────────


def _seed_users(session) -> None:
    user_data = [
        ("alice", "alice@example.com", "Alice Johnson", UserRole.ADMIN, True, True),
        ("bob", "bob@example.com", "Bob Smith", UserRole.EDITOR, True, False),
        ("carol", "carol@example.com", "Carol Williams", UserRole.VIEWER, True, False),
        ("dave", "dave@example.com", "Dave Brown", UserRole.EDITOR, False, False),
        ("eve", "eve@example.com", "Eve Davis", UserRole.VIEWER, True, False),
        ("frank", "frank@example.com", "Frank Miller", UserRole.ADMIN, True, True),
        ("grace", "grace@example.com", "Grace Wilson", UserRole.VIEWER, True, False),
        ("hank", "hank@example.com", "Hank Moore", UserRole.EDITOR, True, False),
    ]
    for i, (uname, email, full, role, active, superuser) in enumerate(user_data):
        session.add(
            User(
                username=uname,
                email=email,
                full_name=full,
                role=role,
                is_active=active,
                is_superuser=superuser,
                bio=(
                    f"Bio for {full}. This user works in the {role.value} role."
                    if i % 2 == 0
                    else None
                ),
                profile_data=(
                    {"theme": "dark", "language": "en", "notifications": True}
                    if i % 3 == 0
                    else None
                ),
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365)),
            )
        )
    session.flush()


# ── Categories ───────────────────────────────────────────────────────────


def _seed_categories(session) -> list[Category]:
    top = [
        Category(name="Electronics", slug="electronics", is_featured=True, display_order=1),
        Category(name="Clothing", slug="clothing", is_featured=True, display_order=2),
        Category(name="Books", slug="books", is_featured=False, display_order=3),
        Category(name="Home & Garden", slug="home-garden", is_featured=False, display_order=4),
    ]
    session.add_all(top)
    session.flush()

    electronics, clothing, books, home = top
    children = [
        Category(name="Phones", slug="phones", is_featured=True, display_order=1, parent_id=electronics.id),
        Category(name="Laptops", slug="laptops", is_featured=False, display_order=2, parent_id=electronics.id),
        Category(name="Men's", slug="mens", is_featured=False, display_order=1, parent_id=clothing.id),
        Category(name="Women's", slug="womens", is_featured=True, display_order=2, parent_id=clothing.id),
    ]
    session.add_all(children)
    session.flush()
    return top + children


# ── Tags ─────────────────────────────────────────────────────────────────


def _seed_tags(session) -> list[Tag]:
    tags = []
    for name, color in [
        ("VIP", "#ef4444"),
        ("Urgent", "#f97316"),
        ("Wholesale", "#22c55e"),
        ("Recurring", "#3b82f6"),
        ("Discounted", "#a855f7"),
    ]:
        t = Tag(name=name, color=color)
        tags.append(t)
        session.add(t)
    session.flush()
    return tags


# ── Products ─────────────────────────────────────────────────────────────


def _seed_products(session, categories: list[Category]) -> list[Product]:
    cat_map = {c.slug: c for c in categories}
    product_data = [
        ("iPhone 15 Pro", "IPH-15P", 999.99, 150.00, 750.0, 45, 0.187, ProductStatus.ACTIVE, True, "phones"),
        ("MacBook Air M3", "MBA-M3", 1299.00, 1499.00, 950.0, 30, 1.24, ProductStatus.ACTIVE, True, "laptops"),
        ("Samsung Galaxy S24", "SAM-S24", 849.99, None, 600.0, 60, 0.168, ProductStatus.ACTIVE, True, "phones"),
        ("Pixel 8", "PIX-8", 699.00, 799.00, 400.0, 0, 0.187, ProductStatus.OUT_OF_STOCK, True, "phones"),
        ("ThinkPad X1", "TP-X1", 1549.00, None, 1100.0, 15, 1.36, ProductStatus.ACTIVE, True, "laptops"),
        ("Running Shoes", "RS-001", 129.99, 159.99, 45.0, 200, 0.35, ProductStatus.ACTIVE, True, "mens"),
        ("Summer Dress", "SD-201", 79.99, None, 25.0, 80, 0.2, ProductStatus.ACTIVE, True, "womens"),
        ("Python Cookbook", "BK-PY1", 49.99, 59.99, 15.0, 500, 0.8, ProductStatus.ACTIVE, False, "books"),
        ("Clean Code", "BK-CC1", 39.99, None, 12.0, 300, 0.65, ProductStatus.ACTIVE, False, "books"),
        ("Garden Tools Set", "HG-GT1", 89.99, 119.99, 35.0, 40, 3.5, ProductStatus.DRAFT, True, "home-garden"),
        ("Smart Watch", "SW-001", 299.99, None, 180.0, 0, 0.05, ProductStatus.ARCHIVED, True, "electronics"),
        ("Desk Lamp", "DL-001", 45.99, 55.00, 15.0, 150, 1.2, ProductStatus.ACTIVE, True, "home-garden"),
    ]
    products = []
    for name, sku, price, compare, cost, stock, weight, status, taxable, cat_slug in product_data:
        p = Product(
            name=name,
            sku=sku,
            description=f"High-quality {name.lower()}. Perfect for everyday use.",
            price=price,
            compare_at_price=compare,
            cost=cost,
            stock_quantity=stock,
            weight_kg=weight,
            status=status,
            is_taxable=taxable,
            metadata_=(
                {"brand": name.split()[0], "warranty_months": 12, "tags": ["popular"]}
                if random.random() > 0.5
                else None
            ),
            category_id=cat_map[cat_slug].id,
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 180)),
        )
        products.append(p)
        session.add(p)
    session.flush()
    return products


# ── Orders & Items ───────────────────────────────────────────────────────


def _seed_orders(
    session,
    users: list[User],
    products: list[Product],
    tags: list[Tag],
) -> None:
    statuses = list(OrderStatus)
    for i in range(20):
        order_user = random.choice(users)
        order_status = random.choice(statuses)
        is_paid = order_status in (
            OrderStatus.CONFIRMED,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
        )
        order = Order(
            order_number=f"ORD-{2024_0001 + i:08d}",
            status=order_status,
            is_paid=is_paid,
            notes=f"Order notes for #{i + 1}" if i % 3 == 0 else None,
            shipping_address=(
                {
                    "street": f"{100 + i} Main St",
                    "city": random.choice(["New York", "London", "Tokyo", "Berlin"]),
                    "zip": f"{10000 + i * 11}",
                    "country": random.choice(["US", "UK", "JP", "DE"]),
                }
                if is_paid
                else None
            ),
            user_id=order_user.id,
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 90)),
        )
        session.add(order)
        session.flush()

        total = 0.0
        for _ in range(random.randint(1, 4)):
            prod = random.choice(products)
            qty = random.randint(1, 5)
            discount = random.choice([0.0, 5.0, 10.0, 15.0])
            session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=prod.id,
                    quantity=qty,
                    unit_price=float(prod.price),
                    discount_percent=discount,
                )
            )
            total += float(prod.price) * qty * (1 - discount / 100)

        order.total_amount = round(total, 2)
        if random.random() > 0.4:
            order.tags = random.sample(tags, k=random.randint(1, 3))

    session.flush()


# ── Employees (50-field stress test) ─────────────────────────────────────

_FIRST_NAMES = [
    "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace",
    "Hank", "Ivy", "Jack", "Karen", "Leo", "Mona", "Nate", "Olivia",
    "Pete", "Quinn", "Rita", "Sam", "Tina", "Uma", "Vic", "Wendy",
    "Xander", "Yara", "Zach", "Anna", "Ben", "Cora", "Derek",
]
_LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
    "Miller", "Davis", "Rodriguez", "Martinez", "Anderson", "Taylor",
    "Thomas", "Hernandez", "Moore", "Martin", "Jackson", "Thompson",
    "White", "Lopez", "Lee", "Gonzalez", "Harris", "Clark", "Lewis",
]
_JOB_TITLES = [
    "Software Engineer", "Senior Engineer", "Staff Engineer",
    "Engineering Manager", "Product Manager", "Designer",
    "Data Analyst", "DevOps Engineer", "QA Engineer",
    "Marketing Specialist", "Sales Rep", "HR Coordinator",
    "Finance Analyst", "Support Engineer", "Security Engineer",
    "Technical Writer", "Intern", "VP Engineering", "CTO", "Director",
]
_CITIES = [
    ("San Francisco", "CA", "US", "94102"),
    ("New York", "NY", "US", "10001"),
    ("London", None, "UK", "EC1A"),
    ("Berlin", None, "DE", "10115"),
    ("Tokyo", None, "JP", "100-0001"),
    ("Sydney", "NSW", "AU", "2000"),
    ("Toronto", "ON", "CA", "M5V"),
    ("São Paulo", None, "BR", "01310"),
    ("Mumbai", None, "IN", "400001"),
    ("Nairobi", None, "KE", "00100"),
]
_CONTINENTS = [
    Continent.NORTH_AMERICA, Continent.NORTH_AMERICA,
    Continent.EUROPE, Continent.EUROPE, Continent.ASIA,
    Continent.OCEANIA, Continent.NORTH_AMERICA,
    Continent.SOUTH_AMERICA, Continent.ASIA, Continent.AFRICA,
]
_SKILLS = [
    "Python, SQL, Docker", "React, TypeScript, Node.js",
    "Java, Spring, Kubernetes", "Go, gRPC, Terraform",
    "Rust, WebAssembly", "Machine Learning, PyTorch",
    "Data Engineering, Spark", "iOS, Swift, Objective-C",
    "Android, Kotlin", "DevOps, AWS, CI/CD",
]
_CERTS = [
    "AWS Solutions Architect", "PMP", "CKA", "CISSP",
    "Google Cloud Professional", None, None, "Scrum Master",
    "TOGAF", None,
]


def _seed_employees(session) -> None:
    now = datetime.utcnow()
    for i in range(30):
        fn = _FIRST_NAMES[i % len(_FIRST_NAMES)]
        ln = _LAST_NAMES[i % len(_LAST_NAMES)]
        city, state, country, zipcode = _CITIES[i % len(_CITIES)]
        session.add(
            Employee(
                first_name=fn,
                last_name=ln,
                middle_name=random.choice([None, "A.", "M.", "J.", "R."]),
                employee_code=f"EMP-{1000 + i}",
                email=f"{fn.lower()}.{ln.lower()}@example.com",
                personal_email=(
                    f"{fn.lower()}@gmail.com" if random.random() > 0.3 else None
                ),
                phone=(
                    f"+1-555-{random.randint(1000, 9999)}"
                    if random.random() > 0.2
                    else None
                ),
                mobile=f"+1-555-{random.randint(1000, 9999)}",
                department=random.choice(list(Department)),
                role=random.choice(list(UserRole)),
                priority=random.choice(list(Priority)),
                continent=_CONTINENTS[i % len(_CONTINENTS)],
                is_active=random.random() > 0.1,
                is_remote=random.random() > 0.5,
                is_manager=random.random() > 0.75,
                is_contractor=random.random() > 0.85,
                has_parking=random.random() > 0.6,
                has_laptop=random.random() > 0.05,
                email_verified=random.random() > 0.15,
                onboarding_complete=random.random() > 0.2,
                salary=round(random.uniform(50000, 250000), 2),
                bonus=round(random.uniform(0, 30000), 2),
                hourly_rate=(
                    round(random.uniform(25, 150), 2)
                    if random.random() > 0.4
                    else None
                ),
                vacation_days=random.randint(10, 30),
                sick_days_used=random.randint(0, 10),
                overtime_hours=round(random.uniform(0, 40), 1),
                performance_score=(
                    round(random.uniform(1.0, 5.0), 1)
                    if random.random() > 0.2
                    else None
                ),
                years_experience=random.randint(0, 25),
                team_size=random.randint(0, 15),
                office_floor=(
                    random.randint(1, 20) if random.random() > 0.3 else None
                ),
                job_title=random.choice(_JOB_TITLES),
                office_location=(
                    f"Building {random.choice(['A', 'B', 'C', 'D'])}"
                    f"-{random.randint(100, 500)}"
                ),
                city=city,
                state=state,
                country=country,
                zip_code=zipcode,
                address_line1=(
                    f"{random.randint(1, 999)} "
                    f"{random.choice(['Main', 'Oak', 'Elm', 'Pine', 'Maple'])} St"
                ),
                address_line2=(
                    f"Suite {random.randint(1, 50)}"
                    if random.random() > 0.6
                    else None
                ),
                bio=(
                    f"{fn} is a {random.choice(_JOB_TITLES).lower()} "
                    f"with {random.randint(1, 20)} years of experience."
                    if random.random() > 0.3
                    else None
                ),
                notes=random.choice(
                    [None, "Top performer", "Needs mentoring",
                     "On improvement plan", "Promotion candidate"]
                ),
                skills=random.choice(_SKILLS),
                certifications=random.choice(_CERTS),
                linkedin_url=(
                    f"https://linkedin.com/in/{fn.lower()}{ln.lower()}"
                    if random.random() > 0.3
                    else None
                ),
                github_url=(
                    f"https://github.com/{fn.lower()}{ln.lower()}"
                    if random.random() > 0.5
                    else None
                ),
                emergency_contact_name=(
                    f"{random.choice(_FIRST_NAMES)} {random.choice(_LAST_NAMES)}"
                ),
                emergency_contact_phone=f"+1-555-{random.randint(1000, 9999)}",
                date_of_birth=datetime(
                    random.randint(1965, 2000),
                    random.randint(1, 12),
                    random.randint(1, 28),
                ),
                hire_date=now - timedelta(days=random.randint(30, 3000)),
                last_review_date=(
                    now - timedelta(days=random.randint(1, 365))
                    if random.random() > 0.3
                    else None
                ),
                next_review_date=(
                    now + timedelta(days=random.randint(30, 365))
                    if random.random() > 0.3
                    else None
                ),
                termination_date=None,
                metadata_=(
                    {"source": random.choice(
                        ["referral", "linkedin", "career_page", "recruiter"]
                    )}
                    if random.random() > 0.4
                    else None
                ),
            )
        )
    session.flush()
