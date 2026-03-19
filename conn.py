import sqlite3
from pathlib import Path

# SQLite is easy to deploy and works on any host.
# The database file is stored next to this module as "site.db".
# Create/connect to SQLite database
DB_PATH = Path(__file__).resolve().parent / "site.db"

conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
conn.row_factory = sqlite3.Row

# Create cursor
cursor = conn.cursor()

print(f"SQLite database connected: {DB_PATH}")

# Ensure core user tables exist.
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS register (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        email TEXT UNIQUE,
        phone TEXT,
        role TEXT,
        state TEXT,
        city TEXT,
        pincode TEXT,
        address TEXT,
        username TEXT UNIQUE,
        password TEXT
    )
    """
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS login (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """
)

conn.commit()

# Ensure other tables exist in the same database file.
# These are used throughout the app for trips, bookings, chat, and feedback.
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS Operator (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        tel TEXT,
        email TEXT,
        tripname TEXT,
        price REAL,
        sourcee TEXT,
        destination TEXT,
        sourcedate TEXT,
        destinationdate TEXT,
        maximumpeople INTEGER,
        pick_time TEXT,
        pickup_location TEXT,
        journey_start TEXT,
        travel_mode TEXT,
        travel_details TEXT,
        destination_overview TEXT,
        hotel_details TEXT,
        places_visit TEXT,
        amenities TEXT,
        cover_image TEXT,
        hotel_image TEXT,
        place_image TEXT
    )
    """
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS OperatorGallery (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operator_id INTEGER NOT NULL,
        image_type TEXT NOT NULL,
        image_name TEXT NOT NULL
    )
    """
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS OperatorDay (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operator_id INTEGER NOT NULL,
        day_no INTEGER NOT NULL,
        day_date TEXT,
        place TEXT,
        time TEXT,
        tplan TEXT,
        image_name TEXT
    )
    """
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS OperatorDayGallery (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operator_id INTEGER NOT NULL,
        day_no INTEGER NOT NULL,
        image_name TEXT
    )
    """
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS TripBooking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        trip_id INTEGER NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        travelers INTEGER NOT NULL,
        payment_mode TEXT NOT NULL,
        special_notes TEXT,
        booking_ref TEXT NOT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS TripChat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        trip_id INTEGER NOT NULL,
        sender_role TEXT NOT NULL,
        message_text TEXT NOT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS TripFeedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        trip_id INTEGER NOT NULL,
        feedback_text TEXT NOT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """
)

conn.commit()