import psycopg2
from config import DATABASE_URL
from datetime import datetime, timedelta
import time
import logging

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

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
                    master VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("Database initialized successfully")
            return
        except psycopg2.OperationalError as e:
            logger.error(f"Database connection attempt {attempt + 1} failed: {e}")
            if attempt < attempts - 1:
                time.sleep(5)
            else:
                raise Exception("Failed to connect to database after multiple attempts")

def add_appointment(name, phone, appointment_time, master):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO appointments (client_name, client_phone, appointment_time, master) VALUES (%s, %s, %s, %s)",
            (name, phone, appointment_time, master)
        )
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Appointment added for {name}, master: {master}")
    except Exception as e:
        logger.error(f"Error adding appointment: {e}")
        raise

def is_slot_taken(appointment_time, master):
    try:
        if not appointment_time or not master:
            logger.error(f"Invalid parameters: appointment_time={appointment_time}, master={master}")
            return False
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM appointments WHERE appointment_time = %s AND master = %s",
            (appointment_time, master)
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        logger.info(f"Checked slot for {appointment_time}, master: {master}, taken: {result is not None}")
        return result is not None
    except psycopg2.OperationalError as e:
        logger.error(f"Database connection error in is_slot_taken: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in is_slot_taken: {e}")
        raise

def cancel_appointment(phone):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM appointments WHERE client_phone = %s RETURNING client_name, master",
            (phone,)
        )
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Cancelled appointment for phone {phone}: {result}")
        return result
    except Exception as e:
        logger.error(f"Error cancelling appointment: {e}")
        raise

def get_all_appointments():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT client_name, client_phone, appointment_time, master FROM appointments ORDER BY appointment_time")
        appointments = cursor.fetchall()
        cursor.close()
        conn.close()
        logger.info(f"Retrieved {len(appointments)} appointments")
        return appointments
    except Exception as e:
        logger.error(f"Error retrieving appointments: {e}")
        raise