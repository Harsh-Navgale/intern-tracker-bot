import psycopg2
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()

def init_db():
    cur.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id SERIAL PRIMARY KEY,
            user_id TEXT,
            username TEXT,
            type TEXT,
            message TEXT,
            timestamp TIMESTAMP
        )
    ''')
    conn.commit()

def log_message(user_id, username, log_type, message_text):
    now = datetime.now()
    cur.execute('''
        INSERT INTO logs (user_id, username, type, message, timestamp)
        VALUES (%s, %s, %s, %s, %s)
    ''', (user_id, username, log_type, message_text, now))
    conn.commit()

def get_logs_by_date(date):
    cur.execute("SELECT user_id, type FROM logs WHERE DATE(timestamp) = %s", (date,))
    return cur.fetchall()

def get_user_logs(user_id):
    cur.execute("SELECT * FROM logs WHERE user_id = %s ORDER BY timestamp DESC", (user_id,))
    return cur.fetchall()
