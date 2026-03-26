"""
Admin view configuration for each model.

Demonstrates:
- FA icon strings (backward compat)
- Lucide icon names (direct)
- Raw SVG icon strings (new)
- Timestamp fields in column_list / column_details_list
- form_excluded_columns for auto-generated timestamp fields
"""

from spa_sqladmin import ModelView

from models import (
    Category,
    Employee,
    Order,
    OrderItem,
    Product,
    Tag,
    User,
)

# ── SVG icon strings for testing raw SVG rendering ──

SVG_CATEGORY = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"'
    ' fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"'
    ' stroke-linejoin="round"><path d="M12 2 2 7l10 5 10-5-10-5Z"/>'
    '<path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/></svg>'
)

SVG_ORDER_ITEM = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"'
    ' fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"'
    ' stroke-linejoin="round"><rect width="20" height="14" x="2" y="5" rx="2"/>'
    '<line x1="2" x2="22" y1="10" y2="10"/></svg>'
)


class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.username,
        User.email,
        User.full_name,
        User.role,
        User.is_active,
        User.is_superuser,
        User.created_at,
        User.updated_at,
    ]
    column_details_list = [
        User.id,
        User.username,
        User.email,
        User.full_name,
        User.role,
        User.is_active,
        User.is_superuser,
        User.bio,
        User.profile_data,
        User.created_at,
        User.updated_at,
        User.orders,
    ]
    column_searchable_list = [User.username, User.email, User.full_name]
    column_sortable_list = [
        User.id, User.username, User.email, User.created_at, User.updated_at,
    ]
    column_labels = {
        User.is_active: "Active",
        User.is_superuser: "Superuser",
        User.full_name: "Full Name",
        User.created_at: "Joined",
        User.updated_at: "Last Updated",
    }
    icon = "fa-solid fa-users"

    name = "User"
    name_plural = "Users"
    page_size = 25


class CategoryAdmin(ModelView, model=Category):
    column_list = [
        Category.id,
        Category.name,
        Category.slug,
        Category.is_featured,
        Category.display_order,
        Category.parent,
    ]
    column_details_list = [
        Category.id,
        Category.name,
        Category.slug,
        Category.description,
        Category.is_featured,
        Category.display_order,
        Category.parent,
        Category.products,
    ]
    column_searchable_list = [Category.name, Category.slug]
    column_sortable_list = [Category.id, Category.name, Category.display_order]
    column_labels = {
        Category.is_featured: "Featured",
        Category.display_order: "Order",
    }
    form_excluded_columns = [Category.products, "children"]
    # Raw SVG icon (Layers icon) to test SVG string rendering
    icon = SVG_CATEGORY
    name = "Category"
    name_plural = "Categories"


class ProductAdmin(ModelView, model=Product):
    column_list = [
        Product.id,
        Product.name,
        Product.sku,
        Product.price,
        Product.stock_quantity,
        Product.status,
        Product.is_taxable,
        Product.category,
        Product.created_at,
    ]
    column_details_list = [
        Product.id,
        Product.name,
        Product.sku,
        Product.description,
        Product.price,
        Product.compare_at_price,
        Product.cost,
        Product.stock_quantity,
        Product.weight_kg,
        Product.status,
        Product.is_taxable,
        Product.metadata_,
        Product.category,
        Product.created_at,
    ]
    column_searchable_list = [Product.name, Product.sku]
    column_sortable_list = [
        Product.id, Product.name, Product.price,
        Product.stock_quantity, Product.created_at,
    ]
    column_labels = {
        Product.is_taxable: "Taxable",
        Product.stock_quantity: "In Stock",
        Product.metadata_: "Metadata",
        Product.compare_at_price: "Compare Price",
        Product.weight_kg: "Weight (kg)",
    }
    form_excluded_columns = [Product.order_items, Product.created_at]
    # Lucide icon name directly
    icon = "Package"
    name = "Product"
    name_plural = "Products"
    page_size = 25


class OrderAdmin(ModelView, model=Order):
    column_list = [
        Order.id,
        Order.order_number,
        Order.status,
        Order.total_amount,
        Order.is_paid,
        Order.user,
        Order.tags,
        Order.created_at,
        Order.updated_at,
    ]
    column_details_list = [
        Order.id,
        Order.order_number,
        Order.status,
        Order.total_amount,
        Order.is_paid,
        Order.notes,
        Order.shipping_address,
        Order.user,
        Order.items,
        Order.tags,
        Order.created_at,
        Order.updated_at,
    ]
    column_searchable_list = [Order.order_number]
    column_sortable_list = [
        Order.id, Order.order_number, Order.total_amount,
        Order.created_at, Order.updated_at,
    ]
    column_labels = {
        Order.is_paid: "Paid",
        Order.total_amount: "Total",
        Order.order_number: "Order #",
        Order.shipping_address: "Shipping Address",
        Order.updated_at: "Last Updated",
    }
    form_excluded_columns = [Order.items, Order.created_at, Order.updated_at]
    icon = "ShoppingCart"
    name = "Order"
    name_plural = "Orders"
    page_size = 25


class OrderItemAdmin(ModelView, model=OrderItem):
    column_list = [
        OrderItem.id,
        OrderItem.order,
        OrderItem.product,
        OrderItem.quantity,
        OrderItem.unit_price,
        OrderItem.discount_percent,
    ]
    column_sortable_list = [
        OrderItem.id, OrderItem.quantity, OrderItem.unit_price,
    ]
    column_labels = {
        OrderItem.unit_price: "Unit Price",
        OrderItem.discount_percent: "Discount %",
    }
    # Raw SVG icon (CreditCard icon) to test SVG string rendering
    icon = SVG_ORDER_ITEM
    name = "Order Item"
    name_plural = "Order Items"


class TagAdmin(ModelView, model=Tag):
    column_list = [Tag.id, Tag.name, Tag.color]
    column_searchable_list = [Tag.name]
    column_sortable_list = [Tag.id, Tag.name]
    icon = "Tag"
    name = "Tag"
    name_plural = "Tags"


class EmployeeAdmin(ModelView, model=Employee):
    column_list = [
        Employee.id,
        Employee.employee_code,
        Employee.first_name,
        Employee.last_name,
        Employee.email,
        Employee.department,
        Employee.role,
        Employee.priority,
        Employee.is_active,
        Employee.is_remote,
        Employee.is_manager,
        Employee.salary,
        Employee.job_title,
        Employee.city,
        Employee.country,
        Employee.continent,
        Employee.hire_date,
        Employee.performance_score,
        Employee.years_experience,
        Employee.team_size,
        Employee.vacation_days,
        Employee.is_contractor,
        Employee.has_laptop,
        Employee.email_verified,
        Employee.onboarding_complete,
        Employee.hourly_rate,
        Employee.bonus,
        Employee.overtime_hours,
        Employee.office_floor,
        Employee.office_location,
        Employee.state,
        Employee.zip_code,
        Employee.skills,
        Employee.certifications,
        Employee.phone,
        Employee.mobile,
        Employee.linkedin_url,
        Employee.github_url,
        Employee.created_at,
        Employee.updated_at,
    ]
    column_searchable_list = [
        Employee.first_name,
        Employee.last_name,
        Employee.email,
        Employee.employee_code,
        Employee.job_title,
    ]
    column_sortable_list = [
        Employee.id,
        Employee.first_name,
        Employee.last_name,
        Employee.salary,
        Employee.hire_date,
        Employee.performance_score,
        Employee.years_experience,
        Employee.created_at,
    ]
    column_labels = {
        Employee.employee_code: "Emp Code",
        Employee.is_active: "Active",
        Employee.is_remote: "Remote",
        Employee.is_manager: "Manager",
        Employee.is_contractor: "Contractor",
        Employee.has_parking: "Parking",
        Employee.has_laptop: "Laptop",
        Employee.email_verified: "Email OK",
        Employee.onboarding_complete: "Onboarded",
        Employee.performance_score: "Perf Score",
        Employee.years_experience: "Experience (yrs)",
        Employee.overtime_hours: "OT Hours",
        Employee.office_floor: "Floor",
        Employee.emergency_contact_name: "Emergency Contact",
        Employee.emergency_contact_phone: "Emergency Phone",
        Employee.metadata_: "Extra Data",
        Employee.created_at: "Created",
        Employee.updated_at: "Updated",
    }
    form_excluded_columns = [
        Employee.created_at,
        Employee.updated_at,
    ]
    icon = "Users"
    name = "Employee"
    name_plural = "Employees"
    page_size = 25
