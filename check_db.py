import sqlite3
import json

# Connect to the database
conn = sqlite3.connect('/app/telegram_marketplace.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in the database:")
for table in tables:
    print(f"- {table['name']}")
    
# Check packages table structure
print("\nPackages table structure:")
cursor.execute("PRAGMA table_info(packages);")
columns = cursor.fetchall()
for col in columns:
    print(f"- {col['name']} ({col['type']})")

# Check packages data
print("\nPackages data:")
cursor.execute("SELECT * FROM packages;")
packages = cursor.fetchall()
for package in packages:
    package_dict = dict(package)
    print(json.dumps(package_dict, indent=2))

# Check user_free_posts table structure
print("\nuser_free_posts table structure:")
cursor.execute("PRAGMA table_info(user_free_posts);")
columns = cursor.fetchall()
for col in columns:
    print(f"- {col['name']} ({col['type']})")

# Check user_packages table structure
print("\nuser_packages table structure:")
cursor.execute("PRAGMA table_info(user_packages);")
columns = cursor.fetchall()
for col in columns:
    print(f"- {col['name']} ({col['type']})")

# Check post_boost_schedule table structure
print("\npost_boost_schedule table structure:")
cursor.execute("PRAGMA table_info(post_boost_schedule);")
columns = cursor.fetchall()
for col in columns:
    print(f"- {col['name']} ({col['type']})")

conn.close()