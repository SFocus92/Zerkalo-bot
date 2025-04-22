import psycopg2
from config import DATABASE_URL
from datetime import datetime, timedelta
import time

def init_db():
    attempts = 5
    for attempt in range(attempts):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id SERIAL PRIMARY KEY,
                    client_name VARCHAR(100),
                    client_phone VARCHAR(20),
                    appointment_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            cursor.close()
            conn.close()
            print("Database initialized successfully")
            return
        except psycopg2.OperationalError as e:
            print(f"Database connection attempt {attempt + 1} failed: {e}")
            if attempt < attempts - 1:
                time.sleep(5)
            else:
                raise Exception("Failed to connect to database after multiple attempts")

def add_appointment(name, phone, appointment_time):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO appointments (client_name, client_phone, appointment_time) VALUES (%s, %s, %s)",
        (name, phone, appointment_time)
    )
    conn.commit()
    cursor.close()
    conn.close()

def is_slot_taken(appointment_time):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM appointments WHERE appointment_time = %s",
        (appointment_time,)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result is not None

def cancel_appointment(phone):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM appointments WHERE client_phone = %s RETURNING client_name",
        (phone,)
    )
    result = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    return result

def get_all_appointments():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT client_name, client_phone, appointment_time FROM appointments ORDER BY appointment_time")
    appointments = cursor.fetchall()
    cursor.close()
    conn.close()
    return appointments