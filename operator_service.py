from conn import conn, cursor
def operator(
    name,
    age,
    tel,
    email,
    tripname,
    price,
    sourcee,
    destination,
    sourcedate,
    destinationdate,
    maximumpeople,
    pick_time,
    pickuploc,
    journey_start,
    travel_mode,
    travel_d,
    destination_overview,
    hotel_details,
    places_visit,
    amenities,
    cover_image,
    hotel_image,
    place_image,
    cover_images=None,
    hotel_images=None,
    place_images=None,
    day_details=None,
):
    if cursor is None or conn is None:
        return "db_unavailable"
    cursor.execute(
        """
        INSERT INTO [Operator]
        (name, age, tel, email, tripname, price, sourcee, destination, sourcedate, destinationdate, maximumpeople, pick_time, pickup_location, journey_start,
         travel_mode, travel_details, destination_overview, hotel_details, places_visit, amenities, cover_image, hotel_image, place_image)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            age,
            tel,
            email,
            tripname,
            price,
            sourcee,
            destination,
            sourcedate,
            destinationdate,
            maximumpeople,
            pick_time,
            pickuploc,
            journey_start,
            travel_mode,
            travel_d,
            destination_overview,
            hotel_details,
            places_visit,
            amenities,
            cover_image,
            hotel_image,
            place_image,
        ),
    )
    operator_id_row = cursor.fetchone()
    operator_id = operator_id_row[0] if operator_id_row else None

    if operator_id and ensure_operator_gallery_table():
        gallery_rows = []
        for image_name in cover_images or []:
            if image_name:
                gallery_rows.append((operator_id, "cover", image_name))
        for image_name in hotel_images or []:
            if image_name:
                gallery_rows.append((operator_id, "hotel", image_name))
        for image_name in place_images or []:
            if image_name:
                gallery_rows.append((operator_id, "place", image_name))
        if gallery_rows:
            cursor.executemany(
                """
                INSERT INTO [OperatorGallery] (operator_id, image_type, image_name)
                VALUES (?, ?, ?)
                """,
                gallery_rows,
            )
    if operator_id and day_details:
        cursor.executemany(
            """
            INSERT INTO [OperatorDay]
            (operator_id, day_no, day_date, place, time, tplan, image_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    operator_id,
                    day["day_no"],
                    day["day_date"],
                    day["place"],
                    day["time"],
                    day["tplan"],
                    day["image_name"],
                )
                for day in day_details
            ],
        )
        if ensure_operator_day_gallery_table():
            day_gallery_rows = []
            for day in day_details:
                images = day.get("image_names") or []
                for image_name in images:
                    if image_name:
                        day_gallery_rows.append((operator_id, day["day_no"], image_name))
            if day_gallery_rows:
                cursor.executemany(
                    """
                    INSERT INTO [OperatorDayGallery] (operator_id, day_no, image_name)
                    VALUES (?, ?, ?)
                    """,
                    day_gallery_rows,
                )
    conn.commit()
    return "success"
def ensure_operator_gallery_table():
    if cursor is None or conn is None:
        return False
    try:
        cursor.execute(
            """
            IF OBJECT_ID('dbo.OperatorGallery', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.OperatorGallery (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    operator_id INT NOT NULL,
                    image_type NVARCHAR(20) NOT NULL,
                    image_name NVARCHAR(255) NOT NULL
                )
            END
            """
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    
def ensure_operator_day_gallery_table():
    if cursor is None or conn is None:
        return False
    try:
        cursor.execute(
            """
            IF OBJECT_ID('dbo.OperatorDayGallery', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.OperatorDayGallery (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    operator_id INT NOT NULL,
                    day_no INT NOT NULL,
                    image_name NVARCHAR(255) NOT NULL
                )
            END
            """
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
def get_operator_trips():
    if cursor is None:
        return []

    cursor.execute(
        """
        SELECT
            id,
            name,
            age,
            tel,
            email,
            tripname,
            price,
            sourcee,
            destination,
            sourcedate,
            destinationdate,
            maximumpeople,
            pick_time,
            journey_start,
            travel_mode,
            destination_overview,
            hotel_details,
            amenities,
            places_visit,
            cover_image,
            DATEDIFF(day, sourcedate, destinationdate) + 1 AS trip_days
        FROM [Operator]
        ORDER BY id DESC
        """
    )
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def get_operator_trip_detail(trip_id):
    if cursor is None:
        return None

    cursor.execute(
        """
        SELECT
            id,
            name,
            tel,
            email,
            tripname,
            price,
            sourcee,
            destination,
            sourcedate,
            destinationdate,
            maximumpeople,
            pick_time,
            pickup_location,
            journey_start,
            travel_mode,
            travel_details,
            destination_overview,
            hotel_details,
            places_visit,
            amenities,
            cover_image,
            hotel_image,
            place_image,
            DATEDIFF(day, sourcedate, destinationdate) + 1 AS trip_days
        FROM [Operator]
        WHERE id = ?
        """,
        (trip_id,),
    )
    row = cursor.fetchone()
    if not row:
        return None
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))


def get_operator_day_details(trip_id):
    if cursor is None:
        return []

    cursor.execute(
        """
        SELECT day_no, day_date, place, time, tplan, image_name
        FROM [OperatorDay]
        WHERE operator_id = ?
        ORDER BY day_no ASC
        """,
        (trip_id,),
    )
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    day_items = [dict(zip(columns, row)) for row in rows]

    day_gallery = {}
    if ensure_operator_day_gallery_table():
        cursor.execute(
            """
            SELECT day_no, image_name
            FROM [OperatorDayGallery]
            WHERE operator_id = ?
            ORDER BY id ASC
            """,
            (trip_id,),
        )
        gallery_rows = cursor.fetchall()
        for day_no, image_name in gallery_rows:
            day_gallery.setdefault(int(day_no), []).append(image_name)

    for day in day_items:
        day_no = int(day.get("day_no") or 0)
        images = day_gallery.get(day_no, [])
        if day.get("image_name") and day["image_name"] not in images:
            images = [day["image_name"]] + images
        day["image_names"] = images

    return day_items


def get_operator_trips_by_email(email):
    if cursor is None:
        return []

    cursor.execute(
        """
        SELECT
            id,
            tripname,
            sourcee,
            destination,
            sourcedate,
            destinationdate,
            price,
            maximumpeople,
            DATEDIFF(day, sourcedate, destinationdate) + 1 AS trip_days
        FROM [Operator]
        WHERE email = ?
        ORDER BY id DESC
        """,
        (email,),
    )
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def delete_operator_trip(trip_id):
    if cursor is None or conn is None:
        return "db_unavailable"

    try:
        cursor.execute("DELETE FROM dbo.TripChat WHERE trip_id = ?", (trip_id,))
    except Exception:
        conn.rollback()
        return "failed"

    try:
        cursor.execute("DELETE FROM dbo.TripBooking WHERE trip_id = ?", (trip_id,))
    except Exception:
        conn.rollback()
        return "failed"

    try:
        cursor.execute("DELETE FROM dbo.OperatorDayGallery WHERE operator_id = ?", (trip_id,))
    except Exception:
        pass

    try:
        cursor.execute("DELETE FROM dbo.OperatorDay WHERE operator_id = ?", (trip_id,))
    except Exception:
        conn.rollback()
        return "failed"

    try:
        cursor.execute("DELETE FROM dbo.OperatorGallery WHERE operator_id = ?", (trip_id,))
    except Exception:
        pass

    try:
        cursor.execute("DELETE FROM dbo.[Operator] WHERE id = ?", (trip_id,))
        conn.commit()
        return "success"
    except Exception:
        conn.rollback()
        return "failed"


def update_operator_itinerary(
    trip_id,
    price,
    sourcee,
    destination,
    sourcedate,
    destinationdate,
    pick_time,
    pickuploc,
    journey_start,
    travel_mode,
    travel_d,
    destination_overview,
    hotel_details,
    places_visit,
    amenities,
    day_details=None,
):
    if cursor is None or conn is None:
        return "db_unavailable"

    cursor.execute(
        """
        UPDATE [Operator]
        SET
            price = ?,
            sourcee = ?,
            destination = ?,
            sourcedate = ?,
            destinationdate = ?,
            pick_time = ?,
            pickup_location = ?,
            journey_start = ?,
            travel_mode = ?,
            travel_details = ?,
            destination_overview = ?,
            hotel_details = ?,
            places_visit = ?,
            amenities = ?
        WHERE id = ?
        """,
        (
            price,
            sourcee,
            destination,
            sourcedate,
            destinationdate,
            pick_time,
            pickuploc,
            journey_start,
            travel_mode,
            travel_d,
            destination_overview,
            hotel_details,
            places_visit,
            amenities,
            trip_id,
        ),
    )

    cursor.execute("DELETE FROM [OperatorDay] WHERE operator_id = ?", (trip_id,))
    if ensure_operator_day_gallery_table():
        cursor.execute("DELETE FROM [OperatorDayGallery] WHERE operator_id = ?", (trip_id,))

    if day_details:
        cursor.executemany(
            """
            INSERT INTO [OperatorDay]
            (operator_id, day_no, day_date, place, time, tplan, image_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    trip_id,
                    day["day_no"],
                    day["day_date"],
                    day["place"],
                    day["time"],
                    day["tplan"],
                    day["image_name"],
                )
                for day in day_details
            ],
        )

        if ensure_operator_day_gallery_table():
            day_gallery_rows = []
            for day in day_details:
                images = day.get("image_names") or []
                for image_name in images:
                    if image_name:
                        day_gallery_rows.append((trip_id, day["day_no"], image_name))
            if day_gallery_rows:
                cursor.executemany(
                    """
                    INSERT INTO [OperatorDayGallery] (operator_id, day_no, image_name)
                    VALUES (?, ?, ?)
                    """,
                    day_gallery_rows,
                )

    conn.commit()
    return "success"
