TABLE_METADATA = {
    "orders": {
        "description": "Core order table with 3.4M orders from 200K+ users",
        "columns": {
            "order_id": "Unique order identifier (PRIMARY KEY)",
            "user_id": "Customer identifier",
            "eval_set": "Dataset partition: 'prior', 'train', or 'test'",
            "order_number": "Sequential order count per user (1 = first order)",
            "order_dow": "Day of week the order was placed (0=Saturday through 6=Friday)",
            "order_hour_of_day": "Hour of day order was placed (0-23)",
            "days_since_prior_order": "Days since the user's previous order (NULL for first orders)",
        },
        "notes": "First orders have NULL days_since_prior_order. Use order_number=1 to identify first-time orders.",
    },
    "order_products_prior": {
        "description": "Products in prior/historical orders (~32M rows). JOIN to orders ON order_id.",
        "columns": {
            "order_id": "FK to orders.order_id",
            "product_id": "FK to products.product_id",
            "add_to_cart_order": "Position the product was added to cart (1=first item added)",
            "reordered": "1 if user previously ordered this product, 0 if first time",
        },
        "notes": "This is the main table for purchase history analysis. Very large - always use aggregations, never SELECT *.",
    },
    "order_products_train": {
        "description": "Products in training orders (~1.4M rows). Same schema as order_products_prior.",
        "columns": {
            "order_id": "FK to orders.order_id",
            "product_id": "FK to products.product_id",
            "add_to_cart_order": "Position the product was added to cart",
            "reordered": "1 if reordered, 0 if first time",
        },
        "notes": "For BI queries, combine with order_products_prior using UNION ALL for full picture, or use prior alone for historical analysis.",
    },
    "products": {
        "description": "Product catalog with ~50K products linked to aisles and departments",
        "columns": {
            "product_id": "Unique product identifier (PRIMARY KEY)",
            "product_name": "Full product name (e.g., 'Organic Whole Milk')",
            "aisle_id": "FK to aisles.aisle_id",
            "department_id": "FK to departments.department_id",
        },
        "notes": "Three-level hierarchy: product -> aisle -> department. JOIN through products to get department/aisle for order items.",
    },
    "aisles": {
        "description": "134 product aisles (subcategories within departments)",
        "columns": {
            "aisle_id": "Unique aisle identifier (PRIMARY KEY)",
            "aisle": "Aisle name (e.g., 'fresh fruits', 'yogurt', 'prepared soups salads')",
        },
        "notes": "Middle level of product hierarchy. JOIN: products.aisle_id = aisles.aisle_id",
    },
    "departments": {
        "description": "21 top-level product departments",
        "columns": {
            "department_id": "Unique department identifier (PRIMARY KEY)",
            "department": "Department name (e.g., 'produce', 'dairy eggs', 'frozen')",
        },
        "notes": "Top level of product hierarchy. JOIN: products.department_id = departments.department_id",
    },
}

RELATIONSHIP_DOC = """
KEY RELATIONSHIPS (Foreign Keys):
- orders.order_id -> order_products_prior.order_id (one-to-many)
- orders.order_id -> order_products_train.order_id (one-to-many)
- order_products_prior.product_id -> products.product_id (many-to-one)
- order_products_train.product_id -> products.product_id (many-to-one)
- products.aisle_id -> aisles.aisle_id (many-to-one)
- products.department_id -> departments.department_id (many-to-one)

COMMON JOIN PATTERNS:
- Product details for orders: order_products_prior JOIN products ON product_id
- Department analysis: order_products_prior JOIN products ON product_id JOIN departments ON department_id
- Aisle analysis: order_products_prior JOIN products ON product_id JOIN aisles ON aisle_id
- Full hierarchy: order_products_prior JOIN products JOIN aisles JOIN departments
- User purchase patterns: orders JOIN order_products_prior ON order_id

IMPORTANT NOTES:
- order_products_prior has ~32M rows: ALWAYS use aggregation (COUNT, AVG, SUM) and LIMIT
- days_since_prior_order is NULL for first orders (order_number=1)
- reordered=1 means the user bought this product in a previous order
- Use order_dow (0-6) for day-of-week analysis, order_hour_of_day (0-23) for hourly patterns
"""


def get_schema_text() -> str:
    """Return full schema as plain text for prompt injection."""
    parts = []
    for table_name, meta in TABLE_METADATA.items():
        cols = ", ".join(meta["columns"].keys())
        parts.append(f"- {table_name}: {cols} | {meta['description']}")
    parts.append("")
    parts.append(RELATIONSHIP_DOC)
    return "\n".join(parts)
