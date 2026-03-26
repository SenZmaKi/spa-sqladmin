"""
SQLAlchemy models demonstrating various field types.

- User: booleans, enums, datetimes, JSON, relationships
- Category: self-referential FK, tree structure
- Product: decimals, floats, JSON metadata, enum status
- Tag: simple model, many-to-many via association table
- Order: computed totals, status enum, shipping JSON, timestamps
- OrderItem: numeric fields, foreign keys
- Employee: 50+ field stress-test (booleans, enums, numerics, text, dates, JSON)
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship

from db import Base


# ──────────────────────────── Enums ─────────────────────────────────────


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class ProductStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    OUT_OF_STOCK = "out_of_stock"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Priority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Continent(str, enum.Enum):
    AFRICA = "africa"
    ASIA = "asia"
    EUROPE = "europe"
    NORTH_AMERICA = "north_america"
    SOUTH_AMERICA = "south_america"
    OCEANIA = "oceania"
    ANTARCTICA = "antarctica"


class Department(str, enum.Enum):
    ENGINEERING = "engineering"
    MARKETING = "marketing"
    SALES = "sales"
    HR = "hr"
    FINANCE = "finance"
    OPERATIONS = "operations"
    LEGAL = "legal"
    SUPPORT = "support"


# ──────────────────────────── Models ────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    bio = Column(Text, nullable=True)
    profile_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    orders = relationship("Order", back_populates="user")

    def __str__(self) -> str:
        return self.username


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_featured = Column(Boolean, default=False, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    parent = relationship("Category", remote_side="Category.id", backref="children")
    products = relationship("Product", back_populates="category")

    def __str__(self) -> str:
        return self.name


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    sku = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    compare_at_price = Column(Numeric(10, 2), nullable=True)
    cost = Column(Float, nullable=True)
    stock_quantity = Column(Integer, default=0, nullable=False)
    weight_kg = Column(Float, nullable=True)
    status = Column(
        Enum(ProductStatus), default=ProductStatus.DRAFT, nullable=False
    )
    is_taxable = Column(Boolean, default=True, nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")

    def __str__(self) -> str:
        return f"{self.name} ({self.sku})"


order_tags = Table(
    "order_tags",
    Base.metadata,
    Column("order_id", Integer, ForeignKey("orders.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    color = Column(String(7), default="#6366f1", nullable=False)

    def __str__(self) -> str:
        return self.name


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_number = Column(String(20), unique=True, nullable=False)
    status = Column(
        Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False
    )
    notes = Column(Text, nullable=True)
    total_amount = Column(Numeric(12, 2), default=0, nullable=False)
    is_paid = Column(Boolean, default=False, nullable=False)
    shipping_address = Column(JSON, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="orders")
    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    tags = relationship("Tag", secondary=order_tags, backref="orders")

    def __str__(self) -> str:
        return self.order_number


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_percent = Column(Float, default=0.0, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    def __str__(self) -> str:
        return f"{self.product} x{self.quantity}"


class Employee(Base):
    """Stress-test model with ~50 fields of various data types."""

    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # ── Identity ──
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    employee_code = Column(String(20), unique=True, nullable=False)
    email = Column(String(255), nullable=False)
    personal_email = Column(String(255), nullable=True)
    phone = Column(String(30), nullable=True)
    mobile = Column(String(30), nullable=True)
    # ── Enums ──
    department = Column(
        Enum(Department), default=Department.ENGINEERING, nullable=False
    )
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    priority = Column(Enum(Priority), default=Priority.MEDIUM, nullable=False)
    continent = Column(Enum(Continent), nullable=True)
    # ── Booleans ──
    is_active = Column(Boolean, default=True, nullable=False)
    is_remote = Column(Boolean, default=False, nullable=False)
    is_manager = Column(Boolean, default=False, nullable=False)
    is_contractor = Column(Boolean, default=False, nullable=False)
    has_parking = Column(Boolean, default=False, nullable=False)
    has_laptop = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    onboarding_complete = Column(Boolean, default=False, nullable=False)
    # ── Numeric ──
    salary = Column(Numeric(12, 2), nullable=True)
    bonus = Column(Numeric(10, 2), default=0)
    hourly_rate = Column(Float, nullable=True)
    vacation_days = Column(Integer, default=20)
    sick_days_used = Column(Integer, default=0)
    overtime_hours = Column(Float, default=0.0)
    performance_score = Column(Float, nullable=True)
    years_experience = Column(Integer, default=0)
    team_size = Column(Integer, default=0)
    office_floor = Column(Integer, nullable=True)
    # ── Text / String ──
    job_title = Column(String(200), nullable=True)
    office_location = Column(String(200), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)
    address_line1 = Column(String(300), nullable=True)
    address_line2 = Column(String(300), nullable=True)
    bio = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    skills = Column(String(500), nullable=True)
    certifications = Column(String(500), nullable=True)
    linkedin_url = Column(String(300), nullable=True)
    github_url = Column(String(300), nullable=True)
    emergency_contact_name = Column(String(200), nullable=True)
    emergency_contact_phone = Column(String(30), nullable=True)
    # ── Dates ──
    date_of_birth = Column(DateTime, nullable=True)
    hire_date = Column(DateTime, default=datetime.utcnow)
    last_review_date = Column(DateTime, nullable=True)
    next_review_date = Column(DateTime, nullable=True)
    termination_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    # ── JSON ──
    metadata_ = Column("metadata", JSON, nullable=True)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.employee_code})"
