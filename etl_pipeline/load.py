import mysql.connector
import pandas as pd
import os
import numpy as np
from dotenv import load_dotenv


load_dotenv()

db_config = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}


def load_results(csv_path='multivariate_ab_test_results.csv'):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"File not found: {csv_path}")

    df = pd.read_csv(csv_path, keep_default_na=False, na_values=['', 'nan, NaN', 'NAN'])
    

    # Flatten the posthoc dictionary to string
    df['Posthoc_Comparison'] = df['Posthoc Results'].apply(lambda d: str(d) if pd.notnull(d) else None)

    df = df[[
        'Metric', 'Test Used', 'Statistic', 'p-value',
        'Significant', 'Effect Size (η²)', 'Assumptions Met', 'Posthoc_Comparison'
    ]]
    
    df = df.replace({np.nan: None, 'nan': None, 'NAN': None})

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ab_test_results (
        id INT AUTO_INCREMENT PRIMARY KEY,
        metric VARCHAR(50),
        test_used VARCHAR(50),
        statistic FLOAT,
        p_value FLOAT,
        significant BOOLEAN,
        effect_size FLOAT,
        assumptions_met BOOLEAN,
        posthoc_comparison TEXT
    )
    """)
    


    insert_query = """
    INSERT INTO ab_test_results (
        metric, test_used, statistic, p_value,
        significant, effect_size, assumptions_met, posthoc_comparison
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    data_tuples = [tuple(x) for x in df.to_numpy()]
    cursor.executemany(insert_query, data_tuples)
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ A/B test results loaded into database.")

if __name__ == "__main__":
    load_results()
