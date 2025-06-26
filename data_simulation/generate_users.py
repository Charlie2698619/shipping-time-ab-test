# data_simulation/02_generate_users.py

import random
from faker import Faker
from datetime import datetime, timedelta
from db_connection import get_connection

fake = Faker()
random.seed(42)

NUM_USERS = 5000
NUM_PREMIUM = 1000
REGIONS_URBAN = ["Berlin", "Paris", "London", "Madrid", "Rome"]
REGIONS_RURAL = ["Lille", "Bordeaux"]
DEVICE_TYPES = ["mobile", "desktop", "tablet"]
CHANNELS = ["email", "social", "ads", "organic"]

def generate_users():
    users = []
    region_pool = REGIONS_URBAN + REGIONS_RURAL

    for i in range(NUM_USERS):
        is_premium = i < NUM_PREMIUM
        
        if is_premium:
            # 90% urban, 10% rural for premium
            weights = [0.18]*len(REGIONS_URBAN) + [0.05]*len(REGIONS_RURAL)
        else:
            # 70% urban, 30% rural for regular
            weights = [0.14]*len(REGIONS_URBAN) + [0.15]*len(REGIONS_RURAL)

        region = random.choices(population=region_pool, weights=weights, k=1)[0]
        sign_up_date = fake.date_time_between(start_date="-2y", end_date="-1y")
        device_type = random.choice(DEVICE_TYPES)
        channel = random.choice(CHANNELS)
        tenure_days = random.randint(30, 730)
        users.append((sign_up_date, region, device_type, channel, tenure_days, is_premium))

    return users

def insert_users_to_db(users):
    conn = get_connection()
    cursor = conn.cursor()

    insert_query = """
    INSERT INTO users (sign_up_date, region, device_type, channel, tenure_days, is_premium)
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    cursor.executemany(insert_query, users)
    conn.commit()
    print(f"{cursor.rowcount} users inserted successfully.")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    users = generate_users()
    insert_users_to_db(users)
    print("Users generated and inserted into the database successfully.")
