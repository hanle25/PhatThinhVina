import os, pyodbc
from dotenv import load_dotenv

load_dotenv()

conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={os.getenv('DB_SERVER')},{os.getenv('DB_PORT', '1433')};"
    f"DATABASE={os.getenv('DB_NAME')};"
    f"UID={os.getenv('DB_USERNAME')};"
    f"PWD={os.getenv('DB_PASSWORD')};"
    "Encrypt=yes;TrustServerCertificate=yes;"
)

try:
    conn = pyodbc.connect(conn_str, timeout=5)
    print("✅ Connected!")
    conn.close()
except Exception as e:
    print("❌ Connection failed:", e)
