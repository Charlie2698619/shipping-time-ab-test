import random
from faker import Faker
from datetime import timedelta
from db_connection import get_connection

fake = Faker()
random.seed(42)

NUM_ORDERS = 2000
CATEGORIES = [
    ("electronics", (150, 800)),
    ("fashion", (30, 200)),
    ("home", (40, 500)),
    ("toys", (10, 150)),
    ("books", (10, 60)),
    ("sports", (15, 300)),
    ("beauty", (15, 150)),
]

DELIVERY_VARIANTS = [1, 2, 3]  # days

# Probabilities for each delivery time: (delivered, cancelled, returned)
STATUS_PROBS_BY_DELIVERY = {
    1: [0.90, 0.06, 0.04],
    2: [0.85, 0.10, 0.05],
    3: [0.80, 0.14, 0.06],
}

def fetch_user_ids():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    user_ids = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return user_ids

def fetch_store_ids():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT store_id FROM stores")
    store_ids = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return store_ids

def generate_orders(user_ids, store_ids):
    orders = []

    # Assign delivery variants randomly to avoid sequence bias
    delivery_variants = random.choices(DELIVERY_VARIANTS, k=NUM_ORDERS)

    for i in range(NUM_ORDERS):
        user_id = random.choice(user_ids)
        store_id = random.choice(store_ids)
        order_date = fake.date_time_between(start_date="-1y", end_date="-30d")

        delivery_days = delivery_variants[i]

        shipped_time = order_date + timedelta(hours=random.randint(2, 6))

        # Choose status probabilities based on delivery time
        status_probs = STATUS_PROBS_BY_DELIVERY[delivery_days]
        order_status = random.choices(
            ["delivered", "cancelled", "returned"], weights=status_probs, k=1
        )[0]

        # Category and value: pick category and use its value range
        category, value_range = random.choice(CATEGORIES)
        total_value = round(random.uniform(*value_range), 2)

        # Handle received_time logic
        if order_status == "cancelled":
            received_time = None
        else:
            received_time = shipped_time + timedelta(days=delivery_days, hours=random.randint(0, 6))

        orders.append((
            user_id,
            store_id,
            None,  # logistics_id to be updated later
            order_date,
            shipped_time,
            received_time,
            order_status,
            category,
            total_value
        ))

    return orders

def insert_orders_to_db(orders):
    conn = get_connection()
    cursor = conn.cursor()

    insert_query = """
    INSERT INTO orders (
        user_id, store_id, logistics_id,
        order_date, shipped_time, received_time,
        order_status, product_category, total_value
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    cursor.executemany(insert_query, orders)
    conn.commit()
    print(f"{cursor.rowcount} orders inserted successfully.")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    user_ids = fetch_user_ids()
    store_ids = fetch_store_ids()
    orders = generate_orders(user_ids, store_ids)
    insert_orders_to_db(orders)
    print("Orders generated and inserted into the database successfully.")
