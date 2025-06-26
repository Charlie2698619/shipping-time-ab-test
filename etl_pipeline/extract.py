import pandas as pd
from sqlalchemy import create_engine

# Connection string: update if needed
MYSQL_URI = "mysql+mysqlconnector://devcharlie:devcharlie@localhost:3308/ecommerce_ab_test"
engine = create_engine(MYSQL_URI)

def extract_all_tables():
    tables = [
        "users", "stores", "orders", "order_items",
        "logistics", "user_behaviors", "reviews"
    ]
    data = {}
    for table in tables:
        df = pd.read_sql(f"SELECT * FROM {table}", engine)
        data[table] = df
        print(f"{table}: {len(df)} rows extracted.")
    return data

if __name__ == "__main__":
    data = extract_all_tables()
    
    # Optionally save to CSV for debugging
    for table_name, df in data.items():
        df.to_csv(f"{table_name}.csv", index=False)
        print(f"Saved {table_name} to CSV.")