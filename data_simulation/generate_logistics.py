import random
from datetime import datetime
from db_connection import get_connection

random.seed(42)

LOGISTICS_COMPANIES = ["DHL", "UPS", "FedEx", "DPD", "GLS"]
SHIPPING_METHODS = {0: "express", 1: "standard", 2: "economy"}
SHIPPING_PROMISE_DAYS = {0: 1, 1: 2, 2: 3}

def fetch_orders_needing_logistics():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT order_id, shipped_time, received_time
        FROM orders
        WHERE logistics_id IS NULL 
        AND order_status != 'cancelled' 
    """)
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return orders

def assign_variant(order_id):
    return order_id % 3

def generate_logistics_records(order_rows):
    logistics_records = []

    for order_id, shipped_time, received_time in order_rows:
        variant = assign_variant(order_id)
        logistics_company = random.choice(LOGISTICS_COMPANIES)
        shipping_method = SHIPPING_METHODS[variant]
        expected_days = SHIPPING_PROMISE_DAYS[variant]

        # Calculate actual delivery days (only for non-cancelled orders)
        actual_delivery = (received_time - shipped_time).days
        
        # Calculate delay in hours (zero if early/on-time)
        total_hours = int((received_time - shipped_time).total_seconds() // 3600)
        expected_hours = expected_days * 24
        delay_hours = max(total_hours - expected_hours, 0)

        logistics_records.append((
            order_id,
            logistics_company,
            shipping_method,
            expected_days,
            actual_delivery,
            delay_hours
        ))

    return logistics_records

def insert_logistics_to_db(logistics_records):
    conn = get_connection()
    cursor = conn.cursor()

    insert_query = """
    INSERT INTO logistics (
        order_id, logistics_company, shipping_method,
        expected_delivery, actual_delivery, delay_hours
    ) VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(insert_query, logistics_records)
    conn.commit()

    # Update orders table with logistics IDs using efficient batch update
    cursor.execute("""
        UPDATE orders o
        JOIN logistics l ON o.order_id = l.order_id
        SET o.logistics_id = l.logistics_id
        WHERE o.logistics_id IS NULL
    """)
    conn.commit()

    cursor.close()
    conn.close()
    print(f"{len(logistics_records)} logistics records inserted and orders updated.")

if __name__ == "__main__":
    order_rows = fetch_orders_needing_logistics()
    logistics = generate_logistics_records(order_rows)
    insert_logistics_to_db(logistics)
    print("Logistics records generated and inserted successfully.")
