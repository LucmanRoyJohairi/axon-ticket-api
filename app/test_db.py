from sqlalchemy import create_engine
from app.config import settings

# Replace with your actual info
URL = settings.database_url

try:
    engine = create_engine(URL)
    # This tries to connect and execute a simple query
    with engine.connect() as connection:
        print("✅ Success! You are connected to the database.")
except Exception as e:
    print(f"❌ Connection failed: {e}")
