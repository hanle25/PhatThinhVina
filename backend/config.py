import os
import urllib.parse
from dotenv import load_dotenv
load_dotenv()

class Config:
    # Build a proper ODBC connection string that forces TLS and (for now) trusts
    # the Azure cert so the driver won’t abort on an unrecognized CA.
    # odbc_str = (
    #     "DRIVER={ODBC Driver 17 for SQL Server};"
    #     f"SERVER={os.getenv('DB_SERVER')},1433;"
    #     f"DATABASE={os.getenv('DB_NAME')};"
    #     f"UID={os.getenv('DB_USERNAME')};"
    #     f"PWD={os.getenv('DB_PASSWORD')};"
    #     "Encrypt=yes;"                  # turn on TLS
    #     "TrustServerCertificate=yes;"   # skip CA validation (dev only)
    #     "Connection Timeout=30;"
    # )

    # params = urllib.parse.quote_plus(odbc_str)
    # SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={params}"

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 300,
        "connect_args": {
            "sslmode": "require",
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        },
    }
    
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
