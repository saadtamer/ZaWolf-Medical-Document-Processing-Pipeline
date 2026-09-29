from src.database.database import Database


db = Database()

database_name = db.test_connection()

print(f"Connected successfully to: {database_name}")