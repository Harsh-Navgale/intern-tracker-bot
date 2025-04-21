import psycopg2
from datetime import datetime
import os
import pytz

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
            timestamp TIMESTAMP,
            date TEXT
        )
    ''')
    conn.commit()

def log_message(user_id, username, log_type, message_text, timestamp):
    if timestamp is None:
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        timestamp = now.isoformat()
        date = now.date().isoformat()
    else:
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.fromisoformat(timestamp).astimezone(ist)
        date = now.date().isoformat()
        
    cur.execute('''
        INSERT INTO logs (user_id, username, type, message, timestamp, date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (user_id, username, log_type, message_text, timestamp, date))
    conn.commit()

def get_logs_by_date(date):
    cur.execute("SELECT user_id, type FROM logs WHERE DATE(timestamp) = %s", (date,))
    return cur.fetchall()

def get_user_logs(user_id):
    cur.execute("SELECT * FROM logs WHERE user_id = %s ORDER BY timestamp DESC", (user_id,))
    return cur.fetchall()

def get_all_logs():
    cur.execute('SELECT user_id, username, type, message, timestamp, date FROM logs')
    return cur.fetchall()

