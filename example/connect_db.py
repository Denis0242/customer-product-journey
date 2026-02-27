import os
import psycopg2
from urllib.parse import urlparse

# Replit automatically sets DATABASE_URL in your environment
database_url = os.getenv('DATABASE_URL')

# Parse the connection string
parsed_url = urlparse(database_url)

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname=parsed_url.path[1:],  # Remove leading '/'
    user=parsed_url.username,
    password=parsed_url.password,
    host=parsed_url.hostname,
    port=parsed_url.port
)

cursor = conn.cursor()

# Test connection
cursor.execute("SELECT version();")
version = cursor.fetchone()
print("✅ Connected to PostgreSQL!")
print(f"Version: {version[0]}")

cursor.close()
conn.close()