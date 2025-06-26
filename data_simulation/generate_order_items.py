import random
from faker import Faker
from db_connection import get_connection

fake = Faker()
random.seed(42)

CATEGORIES = [
    ("electronics", (150, 800)),
    ("fashion", (30, 200)),
    ("home", (40, 500)),
    ("toys", (10, 150)),
    ("books", (10, 60)),
    ("sports", (15, 300)),
    ("beauty", (15, 150)),
]

CATEGORY_LIST = [c[0] for c in CATEGORIES]
PRICE_MAP = {cat: price_range for cat, price_range in CATEGORIES}

def fetch_order_data():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT order_id, product_category, total_value FROM orders")
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return orders

def generate_order_items(order_data):
    order_items = []

    for order_id, main_category, total_value in order_data:
        # Determine number of items (1-3)
        num_items = random.choices([1, 2, 3], weights=[0.7, 0.2, 0.1])[0]
        items = []
        remaining_total = total_value
        
        for item_num in range(num_items):
            # Last item needs special handling
            is_last = (item_num == num_items - 1)
            
            # 85% chance to match order category, 15% random
            category = main_category if random.random() < 0.85 else random.choice(CATEGORY_LIST)
            min_price, max_price = PRICE_MAP[category]
            
            # Generate quantity (1-3 except last item)
            if is_last:
                quantity = 1  
            else:
                quantity = random.randint(1, 3)
                # Ensure remaining total can support subsequent items
                max_possible_price = min(max_price, (remaining_total / quantity) - 0.01)
                if max_possible_price < min_price:
                    quantity = max(1, int(remaining_total / max_price))
                    max_possible_price = min(max_price, remaining_total / quantity)
                
                price = round(random.uniform(min_price, max_possible_price), 2)
                item_total = price * quantity
                remaining_total -= item_total
            
            # Handle last item
            if is_last:
                price = round(remaining_total / quantity, 2)
                # Ensure price stays within category bounds
                if price < min_price:
                    # Adjust quantity to meet minimum price
                    quantity = max(1, int(remaining_total / min_price))
                    price = round(remaining_total / quantity, 2)
                if price > max_price:
                    price = max_price
                    quantity = max(1, int(remaining_total / price))
                
                # Final adjustment for floating point precision
                item_total = round(price * quantity, 2)
                remaining_total = total_value - sum(it[3]*it[4] for it in items)
                price = round((remaining_total) / quantity, 2)
            
            product_name = f"{fake.company()} {fake.word().capitalize()}"
            
            items.append((
                order_id,
                product_name,
                category,
                quantity,
                round(price, 2)
            ))

        

        order_items.extend(items)

    return order_items

def insert_order_items_to_db(order_items):
    conn = get_connection()
    cursor = conn.cursor()

    insert_query = """
    INSERT INTO order_items (
        order_id, product_name, category, quantity, price
    ) VALUES (%s, %s, %s, %s, %s)
    """
    cursor.executemany(insert_query, order_items)
    conn.commit()
    print(f"{cursor.rowcount} order items inserted successfully.")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    order_data = fetch_order_data()
    order_items = generate_order_items(order_data)
    insert_order_items_to_db(order_items)
    print("Order items generated and inserted successfully.")
