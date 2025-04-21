import sqlite3
from datetime import datetime

conn = sqlite3.connect('intern_logs.db')
c = conn.cursor()

def init_db():
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            username TEXT,
            type TEXT,
            date TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()

def log_message(user_id, username, log_type):
    now = datetime.now()
    c.execute('''
        INSERT INTO logs (user_id, username, type, date, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, log_type, now.date().isoformat(), now.isoformat()))
    conn.commit()

def get_logs_by_date(date):
    c.execute('SELECT user_id, type FROM logs WHERE date = ?', (date,))
    return c.fetchall()

def get_user_logs(user_id):
    c.execute('SELECT * FROM logs WHERE user_id = ?', (user_id,))
    return c.fetchall()
