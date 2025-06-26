# data_simulation/07_generate_reviews.py

import random
from faker import Faker
from datetime import timedelta
from db_connection import get_connection

fake = Faker()
random.seed(42)

def fetch_delivered_orders():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.order_id, o.user_id, o.received_time, l.delay_hours
        FROM orders o
        JOIN logistics l ON o.order_id = l.order_id
        WHERE o.order_status = 'delivered'
    """)
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return orders

def generate_reviews(order_rows):
    reviews = []

    for order_id, user_id, received_time, delay_hours in order_rows:
        # 30% of delivered orders get a review
        if random.random() > 0.3:
            continue

        review_time = received_time + timedelta(days=random.randint(1, 5))
        delivery_rating = max(1, 5 - (delay_hours // 24))  # Delay in days
        satisfaction = delivery_rating if random.random() < 0.8 else random.randint(1, 5)
        review_text = fake.sentence(nb_words=random.randint(5, 15))

        reviews.append((
            user_id,
            order_id,
            satisfaction,
            delivery_rating,
            review_text,
            review_time
        ))

    return reviews

def insert_reviews_to_db(reviews):
    conn = get_connection()
    cursor = conn.cursor()

    insert_query = """
    INSERT INTO reviews (
        user_id, order_id, satisfaction, delivery_rating, review_text, review_time
    ) VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(insert_query, reviews)
    conn.commit()
    print(f"{cursor.rowcount} reviews inserted successfully.")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    delivered_orders = fetch_delivered_orders()
    reviews = generate_reviews(delivered_orders)
    insert_reviews_to_db(reviews)
    print("Review data generated and inserted.")
