import random
from faker import Faker
from datetime import datetime, timedelta
from db_connection import get_connection

fake = Faker()
random.seed(42)

BEHAVIOR_TYPES = [
    "view_product", "add_to_cart", "wishlist",
    "remove_from_cart", "search"
]

REFERRAL_SOURCES = ["email", "ad", "social", "affiliate", "direct"]

CATEGORIES = [
    "electronics", "fashion", "home", "toys", "books", "sports", "beauty"
]

# Define a reasonable minimum event date (e.g., start of simulation)
MIN_EVENT_DATE = datetime(2023, 1, 1)

def fetch_orders_with_user():
    """Fetch orders with user info and product category."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.order_id, o.user_id, o.product_category, o.order_date
        FROM orders o
    """)
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return orders

def fetch_all_users():
    """Fetch all user IDs."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return users

def generate_behaviors_for_orders(order_data):
    """Generate user behaviors for users who placed orders."""
    behaviors = []

    for order_id, user_id, order_category, order_date in order_data:
        # Vary number of behaviors per order: weighted towards moderate activity
        num_behaviors = random.choices(
            population=range(1, 11),
            weights=[0.05, 0.10, 0.15, 0.20, 0.15, 0.10, 0.10, 0.08, 0.05, 0.02],
            k=1
        )[0]

        for _ in range(num_behaviors):
            # 85% chance behavior category matches order category, else random category
            if random.random() < 0.85:
                behavior_category = order_category
            else:
                behavior_category = random.choice(CATEGORIES)

            referral_source = random.choice(REFERRAL_SOURCES)
            max_days_before = (order_date - MIN_EVENT_DATE).days
            days_before = random.randint(0, max_days_before if max_days_before > 0 else 0)
            event_time = order_date - timedelta(
                days=days_before,
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            # Safety check to ensure event_time not before MIN_EVENT_DATE
            if event_time < MIN_EVENT_DATE:
                event_time = MIN_EVENT_DATE

            behavior_type = random.choice(BEHAVIOR_TYPES)

            behaviors.append((
                user_id,
                behavior_type,
                behavior_category,
                referral_source,
                event_time
            ))

    return behaviors

def generate_behaviors_for_non_order_users(all_users, users_with_orders):
    """Generate user behaviors for users without orders."""
    behaviors = []
    non_order_users = set(all_users) - set(users_with_orders)

    now = datetime.now()

    for user_id in non_order_users:
        # Generate 0 to 5 behaviors, weighted towards fewer interactions
        num_behaviors = random.choices(
            population=range(0, 6),
            weights=[0.4, 0.3, 0.15, 0.10, 0.04, 0.01],
            k=1
        )[0]

        for _ in range(num_behaviors):
            behavior_category = random.choice(CATEGORIES)
            referral_source = random.choice(REFERRAL_SOURCES)
            # Event time between MIN_EVENT_DATE and now
            total_days = (now - MIN_EVENT_DATE).days
            days_before = random.randint(0, total_days if total_days > 0 else 0)
            event_time = now - timedelta(
                days=days_before,
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            if event_time < MIN_EVENT_DATE:
                event_time = MIN_EVENT_DATE

            behavior_type = random.choice(BEHAVIOR_TYPES)

            behaviors.append((
                user_id,
                behavior_type,
                behavior_category,
                referral_source,
                event_time
            ))

    return behaviors

def insert_behaviors_to_db(behaviors):
    conn = get_connection()
    cursor = conn.cursor()

    insert_query = """
    INSERT INTO user_behaviors (
        user_id, behavior_type, product_category, referral_source, event_time
    ) VALUES (%s, %s, %s, %s, %s)
    """
    cursor.executemany(insert_query, behaviors)
    conn.commit()
    print(f"{cursor.rowcount} user behaviors inserted successfully.")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    # Fetch data
    order_data = fetch_orders_with_user()
    all_users = fetch_all_users()
    users_with_orders = {row[1] for row in order_data}

    # Generate behaviors for users with orders
    behaviors_order_users = generate_behaviors_for_orders(order_data)

    # Generate behaviors for users without orders
    behaviors_non_order_users = generate_behaviors_for_non_order_users(all_users, users_with_orders)

    # Combine all behaviors
    all_behaviors = behaviors_order_users + behaviors_non_order_users

    # Insert into DB
    insert_behaviors_to_db(all_behaviors)

    print("User behavior data generated and inserted successfully.")
