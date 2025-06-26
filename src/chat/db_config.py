import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

def get_db_connection():
    return mysql.connector.connect(
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        host=os.getenv("MYSQL_HOST"),
        database=os.getenv("MYSQL_DATABASE"),
        connection_timeout=3
    )
