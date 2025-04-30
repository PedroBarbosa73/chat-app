import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

print("Testing database connection...")
conn_str = os.getenv('AZURE_SQL_CONNECTIONSTRING')
try:
    conn = pyodbc.connect(conn_str)
    print("Connection successful!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {str(e)}") 