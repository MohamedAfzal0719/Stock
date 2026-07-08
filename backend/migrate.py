import sys
import re

with open('api/main.py', 'r') as f:
    code = f.read()

# 1. Imports
code = code.replace('import sqlite3', 'import psycopg2\nfrom psycopg2.extras import RealDictCursor\nimport os\nimport urllib.parse')

# 2. Connection string
code = code.replace(
    'DB_PATH = os.path.join(os.path.dirname(__file__), "portfolio.db")',
    'DATABASE_URL = os.environ.get("DATABASE_URL")'
)
code = code.replace('conn = sqlite3.connect(DB_PATH)', 'conn = psycopg2.connect(DATABASE_URL)')

# 3. Exceptions
code = code.replace('sqlite3.IntegrityError', 'psycopg2.IntegrityError')

# 4. Schema definitions
code = code.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')

# 5. Placeholders ? to %s
# Only replace '?' in SQL statements (heuristic but safe for this file)
code = code.replace('WHERE username=?', 'WHERE username=%s')
code = code.replace('VALUES (?, ?)', 'VALUES (%s, %s)')
code = code.replace('WHERE user_id=?', 'WHERE user_id=%s')

# 6. Upsert Portfolio
port_upsert_old = """INSERT OR REPLACE INTO portfolios (user_id, total_invested, units, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)"""
port_upsert_new = """INSERT INTO portfolios (user_id, total_invested, units, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE SET total_invested = EXCLUDED.total_invested, units = EXCLUDED.units, updated_at = CURRENT_TIMESTAMP"""
code = code.replace(port_upsert_old, port_upsert_new)

# 7. Upsert Push Subscriptions
push_upsert_old = """INSERT OR REPLACE INTO push_subscriptions (user_id, endpoint, p256dh, auth)
            VALUES (?, ?, ?, ?)"""
push_upsert_new = """INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (endpoint) DO UPDATE SET user_id = EXCLUDED.user_id, p256dh = EXCLUDED.p256dh, auth = EXCLUDED.auth"""
code = code.replace(push_upsert_old, push_upsert_new)

with open('api/main.py', 'w') as f:
    f.write(code)

print("Migration script completed!")
