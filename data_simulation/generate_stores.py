import random 
from faker import Faker
from db_connection import get_connection

fake = Faker()
random.seed(42)

def generate_stores():
    store_locations = [ 
    ("Berlin", "urban"),
    ("Paris", "urban"),
    ("London", "urban"),
    ("Madrid", "urban"),
    ("Rome", "urban"),
    ("Lille", "rural"),
    ("Bordeaux", "rural")
    ]
    
    store_types = ["flagship", "standard", "popup"]
    stores = []
    
    for i in range(7):
        name = f"{fake.company()} Store"
        location, _ = store_locations[i]
        store_type = random.choice(store_types)
        stores.append((name, location, store_type))
    return stores

def insert_stores_to_db(stores):
    conn = get_connection()
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO stores (store_name, location, store_type)
    VALUES (%s, %s, %s) 
    """
    
    cursor.executemany(insert_query, stores)
    conn.commit()
    print(f"{cursor.rowcount} stores inserted successfully.")
    cursor.close()
    conn.close()
    
if __name__ == "__main__":
    stores = generate_stores()
    insert_stores_to_db(stores)
    print("Stores generated and inserted into the database successfully.")