import os
from dotenv import load_dotenv

# Load environment variables from the .env file in the same folder
load_dotenv()

class Config:
    # Construct the Azure SQL Database connection string using values from .env
    SQLALCHEMY_DATABASE_URI = (
        f"mssql+pyodbc://{os.environ.get('DB_USERNAME')}:"
        f"{os.environ.get('DB_PASSWORD')}@"
        f"{os.environ.get('DB_SERVER')}:{os.environ.get('DB_PORT', '1433')}/"
        f"{os.environ.get('DB_NAME')}?driver=ODBC+Driver+17+for+SQL+Server"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
