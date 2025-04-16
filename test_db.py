from dotenv import load_dotenv
import os
import pyodbc
import time

load_dotenv()

def test_connection():
    connection_string = os.getenv('AZURE_SQL_CONNECTIONSTRING')
    if not connection_string:
        print("Error: AZURE_SQL_CONNECTIONSTRING not found in .env file")
        return

    print("Attempting to connect to database...")
    try:
        # Convert SQLAlchemy connection string to pyodbc format
        conn_parts = connection_string.replace('mssql+pyodbc://', '').split('?', 1)
        auth_parts = conn_parts[0].split('@')
        creds = auth_parts[0].split(':')
        server_db = auth_parts[1].split('/')
        
        pyodbc_conn_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server_db[0]};"
            f"DATABASE={server_db[1]};"
            f"UID={creds[0]};"
            f"PWD={creds[1]};"
            "TrustServerCertificate=yes;"
        )
        
        conn = pyodbc.connect(pyodbc_conn_string, timeout=30)
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        row = cursor.fetchone()
        print("Successfully connected to database!")
        print(f"SQL Server version: {row[0]}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")

if __name__ == "__main__":
    test_connection() 