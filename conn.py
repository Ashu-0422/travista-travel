import os
import pyodbc

# If running in production, set DB_CONNECTION_STRING in your environment.
# Example (Azure SQL / SQL Server):
# "DRIVER={ODBC Driver 17 for SQL Server};SERVER=<host>;DATABASE=<db>;UID=<user>;PWD=<pass>;TrustServerCertificate=yes;"
CONNECTION_STRING = os.environ.get(
    "DB_CONNECTION_STRING",
    (
        r"DRIVER={ODBC Driver 17 for SQL Server};"
        r"SERVER=HelloAshuu\SQLEXPRESS;"
        r"DATABASE=Travista;"
        r"UID=travista_user;"
        r"PWD=Travista@123;"
        r"TrustServerCertificate=yes;"
    ),
)

conn = None
cursor = None

try:
    conn = pyodbc.connect(CONNECTION_STRING)
    cursor = conn.cursor()
    print("Database connected successfully")
except pyodbc.Error as e:
    # Keep app startup alive; DB-dependent operations can handle unavailable DB.
    print(f"Database connection failed: {e}")
