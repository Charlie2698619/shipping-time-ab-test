# data_simulation/00_reset_database.py

from db_connection import get_connection

DROP_QUERIES = [
    "SET FOREIGN_KEY_CHECKS = 0;",
    "DROP TABLE IF EXISTS reviews;",
    "DROP TABLE IF EXISTS user_behaviors;",
    "DROP TABLE IF EXISTS order_items;",
    "DROP TABLE IF EXISTS logistics;",
    "DROP TABLE IF EXISTS orders;",
    "DROP TABLE IF EXISTS users;",
    "DROP TABLE IF EXISTS stores;",
    "SET FOREIGN_KEY_CHECKS = 1;"
]

def reset_database():
    conn = get_connection()
    cursor = conn.cursor()
    for query in DROP_QUERIES:
        cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Database reset successfully.")

if __name__ == "__main__":
    reset_database()