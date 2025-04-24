import os
import urllib.parse
from dotenv import load_dotenv
load_dotenv()

class Config:
    # Build a proper ODBC connection string that forces TLS and (for now) trusts
    # the Azure cert so the driver won’t abort on an unrecognized CA.
    odbc_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={os.getenv('DB_SERVER')},1433;"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={os.getenv('DB_USERNAME')};"
        f"PWD={os.getenv('DB_PASSWORD')};"
        "Encrypt=yes;"                  # turn on TLS
        "TrustServerCertificate=yes;"   # skip CA validation (dev only)
        "Connection Timeout=30;"
    )

    # URL-encode it so SQLAlchemy can consume it
    params = urllib.parse.quote_plus(odbc_str)
    SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={params}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
