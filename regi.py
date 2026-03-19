from conn import conn, cursor


def register_user(name, age, email, phone, role, state, city, pincode, address, username, password):
    if cursor is None or conn is None:
        return "db_unavailable"

    try:
        cursor.execute(
            "SELECT 1 FROM register WHERE email=? OR username=?",
            (email, username),
        )
        existing = cursor.fetchone()

        print("Duplicate result:", existing)

        if existing is not None:
            return "duplicate"

        cursor.execute(
            """
            INSERT INTO [register]
            (name, age, email, phone, role, state, city, pincode, address, username, password)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, int(age), email, phone, role, state, city, int(pincode), address, username, password),
        )

        cursor.execute(
            """
            INSERT INTO login (username, password)
            VALUES (?, ?)
            """,
            (username, password),
        )

        conn.commit()
        return "success"

    except Exception as e:
        conn.rollback()
        print("DB ERROR:", e)
        return False


def login_user(username, password):
    if cursor is None:
        return "db_unavailable"

    cursor.execute(
        "SELECT role FROM register WHERE username=? AND password=?",
        (username, password),
    )
    return cursor.fetchone()


def get_user_profile(username):
    if cursor is None:
        return None

    cursor.execute(
        """
        SELECT
            name,
            age,
            email,
            phone,
            role,
            state,
            city,
            pincode,
            address,
            username
        FROM register
        WHERE username=?
        """,
        (username,),
    )
    row = cursor.fetchone()
    if not row:
        return None

    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))
