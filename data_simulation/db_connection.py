import os
import mysql.connector  
from dotenv import load_dotenv

def get_connection():
    load_dotenv() 
    db_config = {
        'host': os.getenv('MYSQL_HOST', ''),
        'user': os.getenv('MYSQL_USER', ''),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', ''),
        'port': os.getenv('MYSQL_PORT', '')
    }
    
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    
    