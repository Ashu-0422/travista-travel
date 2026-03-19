from collections import Counter
from datetime import date, datetime, timedelta
import math

from conn import conn, cursor

INDIA_REGION_ORDER = ["North", "West", "East", "South"]

CITY_REGION_MAP = {
    "agra": "North",
    "ahmedabad": "West",
    "amritsar": "North",
    "bhagalpur": "East",
    "bhilai": "East",
    "bhopal": "North",
    "bhubaneswar": "East",
    "bilaspur": "East",
    "bengaluru": "South",
    "chennai": "South",
    "coimbatore": "South",
    "cuttack": "East",
    "dhanbad": "East",
    "dharamshala": "North",
    "dibrugarh": "East",
    "durgapur": "East",
    "faridabad": "North",
    "gaya": "East",
    "goa": "West",
    "guntur": "South",
    "gurugram": "North",
    "guwahati": "East",
    "gwalior": "North",
    "howrah": "East",
    "hubballi": "South",
    "hyderabad": "South",
    "itanagar": "East",
    "jaipur": "West",
    "jalandhar": "North",
    "jamshedpur": "East",
    "jodhpur": "West",
    "kanpur": "North",
    "kochi": "South",
    "kolkata": "East",
    "kota": "West",
    "kozhikode": "South",
    "lucknow": "North",
    "ludhiana": "North",
    "madurai": "South",
    "manali": "North",
    "mangaluru": "South",
    "margao": "West",
    "mumbai": "West",
    "mysuru": "South",
    "nagpur": "West",
    "naharlagun": "East",
    "nashik": "West",
    "nizamabad": "South",
    "noida": "North",
    "panaji": "West",
    "panipat": "North",
    "patna": "East",
    "pune": "West",
    "puri": "East",
    "raipur": "East",
    "rajkot": "West",
    "ranchi": "East",
    "rourkela": "East",
    "salem": "South",
    "shimla": "North",
    "silchar": "East",
    "surat": "West",
    "thane": "West",
    "thiruvananthapuram": "South",
    "tirupati": "South",
    "udaipur": "West",
    "vadodara": "West",
    "varanasi": "North",
    "vasco da gama": "West",
    "vijayawada": "South",
    "visakhapatnam": "South",
    "warangal": "South",
}


def _normalize_city_name(value):
    return " ".join(str(value or "").strip().lower().split())


def _parse_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _get_region_for_city(city_name):
    return CITY_REGION_MAP.get(_normalize_city_name(city_name))


def get_city_region(city_name):
    return _get_region_for_city(city_name)


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _normalize_price(price_value):
    price = max(_safe_float(price_value, 0.0), 0.0)
    return min(price / 100000.0, 1.0)


def _normalize_trip_days(days_value):
    days = max(_safe_float(days_value, 0.0), 0.0)
    return min(days / 30.0, 1.0)


def _normalize_recency(start_date):
    trip_start = _parse_date(start_date)
    if not trip_start:
        return 0.0
    days_until_trip = max((trip_start - date.today()).days, 0)
    return max(0.0, 1.0 - min(days_until_trip / 90.0, 1.0))


def _normalize_popularity(traveler_count, booking_count):
    travelers = max(_safe_float(traveler_count, 0.0), 0.0)
    bookings = max(_safe_float(booking_count, 0.0), 0.0)
    popularity_signal = travelers + (bookings * 0.7)
    return min(popularity_signal / 100.0, 1.0)


def _add_weighted_feature(feature_map, key, value):
    if not key or not value:
        return
    feature_map[key] = feature_map.get(key, 0.0) + float(value)


def _trip_to_feature_vector(trip):
    feature_vector = {
        "bias": 1.0,
        "price_norm": _normalize_price(trip.get("price")),
        "days_norm": _normalize_trip_days(trip.get("trip_days")),
        "freshness_norm": _normalize_recency(trip.get("sourcedate")),
        "popularity_norm": _normalize_popularity(trip.get("traveler_count"), trip.get("booking_count")),
    }

    source_city = _normalize_city_name(trip.get("sourcee"))
    destination_city = _normalize_city_name(trip.get("destination"))
    trip_region = trip.get("trip_region") or get_city_region(trip.get("destination")) or get_city_region(trip.get("sourcee")) or ""

    _add_weighted_feature(feature_vector, f"source:{source_city}", 1.0)
    _add_weighted_feature(feature_vector, f"destination:{destination_city}", 1.35)
    _add_weighted_feature(feature_vector, f"region:{trip_region}", 1.15)

    return feature_vector


def _merge_feature_vectors(vectors):
    merged = {}
    if not vectors:
        return merged
    for vector, weight in vectors:
        for key, value in vector.items():
            merged[key] = merged.get(key, 0.0) + (value * weight)
    total_weight = sum(weight for _, weight in vectors) or 1.0
    for key in list(merged.keys()):
        merged[key] = merged[key] / total_weight
    return merged


def _cosine_similarity(vector_a, vector_b):
    if not vector_a or not vector_b:
        return 0.0

    dot = 0.0
    for key, value in vector_a.items():
        dot += value * vector_b.get(key, 0.0)

    norm_a = math.sqrt(sum(value * value for value in vector_a.values()))
    norm_b = math.sqrt(sum(value * value for value in vector_b.values()))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def _trip_start_date(trip):
    return _parse_date(trip.get("sourcedate")) or date.max


def _unique_trips(items):
    seen_ids = set()
    unique_items = []
    for item in items:
        trip_id = item.get("id")
        if trip_id in seen_ids:
            continue
        seen_ids.add(trip_id)
        unique_items.append(item)
    return unique_items


def get_recommendation_training_rows():
    if cursor is None:
        return []
    if not ensure_booking_table():
        return []

    cursor.execute(
        """
        SELECT
            b.username,
            b.trip_id,
            b.travelers,
            b.created_at,
            o.tripname,
            o.price,
            o.sourcee,
            o.destination,
            o.sourcedate,
            o.destinationdate,
            DATEDIFF(day, o.sourcedate, o.destinationdate) + 1 AS trip_days
        FROM dbo.TripBooking b
        INNER JOIN dbo.[Operator] o ON o.id = b.trip_id
        ORDER BY b.id DESC
        """
    )
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def get_traveller_dashboard_metrics(username):
    empty_response = {
        "weekly_trip_count": 0,
        "monthly_trip_count": 0,
        "weekly_series": [],
        "monthly_series": [],
        "region_breakdown": [{"label": region, "value": 0} for region in INDIA_REGION_ORDER],
        "top_region": "Not enough trip data yet",
        "top_region_count": 0,
        "unexplored_regions": INDIA_REGION_ORDER[:],
        "longest_trip": None,
        "suggested_regions": INDIA_REGION_ORDER[:2],
    }

    bookings = get_traveller_bookings(username)
    if not bookings:
        return empty_response

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    weekly_series = []
    for offset in range(3, -1, -1):
        current_start = week_start - timedelta(days=offset * 7)
        current_end = current_start + timedelta(days=6)
        weekly_series.append(
            {
                "label": f"{current_start.strftime('%d %b')}",
                "value": 0,
                "start": current_start,
                "end": current_end,
            }
        )

    monthly_series = []
    for offset in range(5, -1, -1):
        month_index = month_start.month - offset
        year_value = month_start.year
        while month_index <= 0:
            month_index += 12
            year_value -= 1
        month_date = date(year_value, month_index, 1)
        monthly_series.append(
            {
                "label": month_date.strftime("%b"),
                "year": year_value,
                "month": month_index,
                "value": 0,
            }
        )

    region_counter = Counter()
    longest_trip = None

    for booking in bookings:
        source_date = _parse_date(booking.get("sourcedate"))
        destination_date = _parse_date(booking.get("destinationdate"))

        if source_date and week_start <= source_date <= week_start + timedelta(days=6):
            empty_response["weekly_trip_count"] += 1
        if source_date and source_date.year == today.year and source_date.month == today.month:
            empty_response["monthly_trip_count"] += 1

        for item in weekly_series:
            if source_date and item["start"] <= source_date <= item["end"]:
                item["value"] += 1
                break

        for item in monthly_series:
            if source_date and source_date.year == item["year"] and source_date.month == item["month"]:
                item["value"] += 1
                break

        trip_regions = {
            _get_region_for_city(booking.get("sourcee")),
            _get_region_for_city(booking.get("destination")),
        }
        trip_regions.discard(None)
        for region in trip_regions:
            region_counter[region] += 1

        trip_days = 0
        if source_date and destination_date and destination_date >= source_date:
            trip_days = (destination_date - source_date).days + 1
        if trip_days and (not longest_trip or trip_days > longest_trip["days"]):
            longest_trip = {
                "name": booking.get("tripname") or "Trip",
                "days": trip_days,
                "route": f"{booking.get('sourcee') or '-'} -> {booking.get('destination') or '-'}",
                "dates": f"{source_date.strftime('%d %b %Y')} to {destination_date.strftime('%d %b %Y')}",
            }

    explored_regions = [region for region in INDIA_REGION_ORDER if region_counter.get(region, 0) > 0]
    unexplored_regions = [region for region in INDIA_REGION_ORDER if region_counter.get(region, 0) == 0]

    top_region = "Not enough trip data yet"
    top_region_count = 0
    if explored_regions:
        top_region = max(
            explored_regions,
            key=lambda region: (region_counter[region], -INDIA_REGION_ORDER.index(region)),
        )
        top_region_count = region_counter[top_region]

    suggested_regions = unexplored_regions[:] if unexplored_regions else [
        region for region, _ in sorted(region_counter.items(), key=lambda item: (item[1], INDIA_REGION_ORDER.index(item[0])))
    ][:2]

    return {
        "weekly_trip_count": empty_response["weekly_trip_count"],
        "monthly_trip_count": empty_response["monthly_trip_count"],
        "weekly_series": [{"label": item["label"], "value": item["value"]} for item in weekly_series],
        "monthly_series": [{"label": item["label"], "value": item["value"]} for item in monthly_series],
        "region_breakdown": [{"label": region, "value": region_counter.get(region, 0)} for region in INDIA_REGION_ORDER],
        "top_region": top_region,
        "top_region_count": top_region_count,
        "unexplored_regions": unexplored_regions,
        "longest_trip": longest_trip,
        "suggested_regions": suggested_regions or INDIA_REGION_ORDER[:2],
    }


def get_home_trip_recommendations(username, role, trips):
    prepared_trips = [dict(trip) for trip in trips]
    for trip in prepared_trips:
        trip["trip_region"] = get_city_region(trip.get("destination")) or get_city_region(trip.get("sourcee")) or ""

    empty_response = {
        "all_trips": prepared_trips,
        "recommended_trips": [],
        "is_new_traveller": False,
    }

    if role != "traveller":
        return empty_response

    traveller_stats = get_traveller_trip_stats(username) if username else {"total_trips": 0}
    if int(traveller_stats.get("total_trips") or 0) == 0:
        return {
            "all_trips": prepared_trips,
            "recommended_trips": [],
            "is_new_traveller": True,
        }

    training_rows = get_recommendation_training_rows()
    user_training_rows = [row for row in training_rows if row.get("username") == username]
    booked_trip_ids = {
        int(row.get("trip_id"))
        for row in user_training_rows
        if row.get("trip_id") is not None
    }

    user_profile_vector = {}
    if user_training_rows:
        weighted_user_vectors = []
        for row in user_training_rows:
            row["trip_region"] = get_city_region(row.get("destination")) or get_city_region(row.get("sourcee")) or ""
            interaction_weight = 1.0 + min(max(_safe_float(row.get("travelers"), 1.0), 1.0), 8.0) * 0.18
            weighted_user_vectors.append((_trip_to_feature_vector(row), interaction_weight))
        user_profile_vector = _merge_feature_vectors(weighted_user_vectors)

    region_profiles = {}
    for row in training_rows:
        row["trip_region"] = get_city_region(row.get("destination")) or get_city_region(row.get("sourcee")) or ""
        region = row.get("trip_region")
        if not region:
            continue
        region_profiles.setdefault(region, []).append((_trip_to_feature_vector(row), 1.0))

    traveller_dashboard = get_traveller_dashboard_metrics(username) if username else {}
    top_region = traveller_dashboard.get("top_region")
    fallback_region_profile = {}
    if top_region in region_profiles:
        fallback_region_profile = _merge_feature_vectors(region_profiles[top_region])

    def ml_recommendation_score(trip):
        trip_vector = _trip_to_feature_vector(trip)
        profile_vector = user_profile_vector or fallback_region_profile
        similarity_score = _cosine_similarity(profile_vector, trip_vector) if profile_vector else 0.0
        score = similarity_score
        if trip.get("id") in booked_trip_ids:
            score -= 0.25
        return score

    recommendation_candidates = [
        trip for trip in prepared_trips if trip.get("id") not in booked_trip_ids
    ]

    recommended_trips = sorted(
        recommendation_candidates,
        key=lambda trip: (
            -ml_recommendation_score(trip),
            _trip_start_date(trip),
        ),
    )[:6]

    recommended_trips = _unique_trips(recommended_trips)

    return {
        "all_trips": prepared_trips,
        "recommended_trips": recommended_trips,
        "is_new_traveller": False,
    }
def ensure_booking_table():
    if cursor is None:
        return False
    try:
        cursor.execute(
            """
            IF OBJECT_ID('dbo.TripBooking', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.TripBooking (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    username NVARCHAR(80) NOT NULL,
                    trip_id INT NOT NULL,
                    full_name NVARCHAR(120) NOT NULL,
                    email NVARCHAR(160) NOT NULL,
                    phone NVARCHAR(20) NOT NULL,
                    travelers INT NOT NULL,
                    payment_mode NVARCHAR(50) NOT NULL,
                    special_notes NVARCHAR(MAX) NULL,
                    booking_ref NVARCHAR(30) NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT GETDATE()
                )
            END
            """
        )
        conn.commit()
        return True
    except Exception:
        if conn:
            conn.rollback()
        return False


def create_booking(
    username,
    trip_id,
    full_name,
    email,
    phone,
    travelers,
    payment_mode,
    special_notes,
    booking_ref,
):
    if cursor is None or conn is None:
        return "db_unavailable"

    try:
        travelers_count = int(travelers)
    except (TypeError, ValueError):
        return "failed"
    if travelers_count <= 0 or travelers_count > 12:
        return "failed"
    if not str(payment_mode or "").strip():
        return "failed"

    if not ensure_booking_table():
        return "failed"

    if has_user_booked_trip(username, trip_id):
        return "already_booked"

    try:
        cursor.execute(
            """
            INSERT INTO dbo.TripBooking
            (username, trip_id, full_name, email, phone, travelers, payment_mode, special_notes, booking_ref)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                trip_id,
                full_name,
                email,
                phone,
                travelers_count,
                payment_mode,
                special_notes,
                booking_ref,
            ),
        )
        conn.commit()
        return "success"
    except Exception:
        conn.rollback()
        return "failed"


def get_user_trip_booking(username, trip_id):
    if cursor is None:
        return None
    if not ensure_booking_table():
        return None

    cursor.execute(
        """
        SELECT TOP 1
            booking_ref,
            full_name,
            email,
            phone,
            travelers,
            payment_mode,
            special_notes,
            created_at
        FROM dbo.TripBooking
        WHERE username = ? AND trip_id = ?
        ORDER BY id DESC
        """,
        (username, trip_id),
    )
    row = cursor.fetchone()
    if not row:
        return None

    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))


def get_traveller_trip_stats(username):
    if cursor is None:
        return {"total_trips": 0, "completed_trips": 0, "upcoming_trips": 0}

    if not ensure_booking_table():
        return {"total_trips": 0, "completed_trips": 0, "upcoming_trips": 0}
    cursor.execute(
        """
        SELECT
            COUNT(*) AS total_trips,
            SUM(CASE WHEN o.destinationdate < CAST(GETDATE() AS DATE) THEN 1 ELSE 0 END) AS completed_trips,
            SUM(CASE WHEN o.destinationdate >= CAST(GETDATE() AS DATE) THEN 1 ELSE 0 END) AS upcoming_trips
        FROM dbo.TripBooking b
        LEFT JOIN [Operator] o ON o.id = b.trip_id
        WHERE b.username = ?
        """,
        (username,),
    )
    row = cursor.fetchone()
    return {
        "total_trips": int(row[0] or 0),
        "completed_trips": int(row[1] or 0),
        "upcoming_trips": int(row[2] or 0),
    }


def get_traveller_bookings(username):
    if cursor is None:
        return []

    if not ensure_booking_table():
        return []
    cursor.execute(
        """
        SELECT
            b.booking_ref,
            b.created_at,
            b.travelers,
            o.id AS trip_id,
            o.tripname,
            o.sourcee,
            o.destination,
            o.sourcedate,
            o.destinationdate
        FROM dbo.TripBooking b
        LEFT JOIN [Operator] o ON o.id = b.trip_id
        WHERE b.username = ?
        ORDER BY b.id DESC
        """,
        (username,),
    )
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def get_trip_booking_summary_map(trip_ids):
    if cursor is None or not trip_ids:
        return {}
    if not ensure_booking_table():
        return {}

    placeholders = ",".join("?" for _ in trip_ids)
    cursor.execute(
        f"""
        SELECT
            trip_id,
            COUNT(*) AS booking_count,
            SUM(travelers) AS traveler_count
        FROM dbo.TripBooking
        WHERE trip_id IN ({placeholders})
        GROUP BY trip_id
        """,
        tuple(trip_ids),
    )
    rows = cursor.fetchall()
    summary = {}
    for trip_id, booking_count, traveler_count in rows:
        summary[int(trip_id)] = {
            "booking_count": int(booking_count or 0),
            "traveler_count": int(traveler_count or 0),
        }
    return summary


def get_operator_dashboard_metrics(operator_email):
    empty_response = {
        "trips": 0,
        "bookings": 0,
        "revenue": 0.0,
        "monthly_bookings": [],
        "trip_options": [],
        "trip_breakdown": [],
        "revenue_breakdown": {"weekly": [], "monthly": []},
        "customer_behavior": {
            "avg_travelers_per_booking": 0,
            "repeat_customers": 0,
            "single_booking_customers": 0,
            "payment_modes": [],
            "top_customers": [],
        },
    }

    if cursor is None:
        return empty_response

    clean_email = str(operator_email or "").strip()
    if not clean_email:
        return empty_response

    cursor.execute(
        """
        SELECT
            id,
            tripname,
            TRY_CAST(price AS DECIMAL(18, 2)) AS price
        FROM dbo.[Operator]
        WHERE email = ?
        ORDER BY id DESC
        """,
        (clean_email,),
    )
    trip_rows = cursor.fetchall()
    trip_options = []
    trip_prices = {}
    for trip_id, tripname, trip_price in trip_rows:
        trip_id_value = int(trip_id or 0)
        trip_options.append({"id": trip_id_value, "name": tripname or f"Trip {trip_id_value}"})
        trip_prices[trip_id_value] = float(trip_price or 0)

    trips = len(trip_options)
    if not ensure_booking_table():
        empty_response["trips"] = trips
        empty_response["trip_options"] = trip_options
        return empty_response

    cursor.execute(
        """
        SELECT
            COUNT(b.id) AS bookings,
            COALESCE(SUM(TRY_CAST(o.price AS DECIMAL(18, 2)) * ISNULL(b.travelers, 0)), 0) AS revenue
        FROM dbo.[Operator] o
        LEFT JOIN dbo.TripBooking b ON b.trip_id = o.id
        WHERE o.email = ?
        """,
        (clean_email,),
    )
    metrics_row = cursor.fetchone()
    bookings = int(metrics_row[0] or 0) if metrics_row else 0
    revenue = float(metrics_row[1] or 0) if metrics_row else 0.0

    cursor.execute(
        """
        SELECT
            MONTH(b.created_at) AS booking_month,
            COUNT(*) AS booking_count
        FROM dbo.TripBooking b
        INNER JOIN dbo.[Operator] o ON o.id = b.trip_id
        WHERE o.email = ? AND YEAR(b.created_at) = YEAR(GETDATE())
        GROUP BY MONTH(b.created_at)
        ORDER BY booking_month ASC
        """,
        (clean_email,),
    )
    monthly_counts = {int(month): int(count or 0) for month, count in cursor.fetchall()}
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_bookings = [
        {"label": month_labels[index - 1], "value": monthly_counts.get(index, 0)}
        for index in range(1, 13)
    ]

    cursor.execute(
        """
        SELECT
            trip_id,
            COUNT(*) AS booking_count,
            COALESCE(SUM(travelers), 0) AS traveler_count
        FROM dbo.TripBooking
        WHERE trip_id IN (SELECT id FROM dbo.[Operator] WHERE email = ?)
        GROUP BY trip_id
        """,
        (clean_email,),
    )
    trip_booking_map = {}
    for trip_id, booking_count, traveler_count in cursor.fetchall():
        trip_booking_map[int(trip_id or 0)] = {
            "bookings": int(booking_count or 0),
            "travelers": int(traveler_count or 0),
        }

    cursor.execute(
        """
        WITH customer_trip_stats AS (
            SELECT
                b.trip_id,
                b.username,
                MAX(b.full_name) AS full_name,
                MAX(b.email) AS email,
                COUNT(*) AS booking_count,
                SUM(b.travelers) AS traveler_count,
                COALESCE(SUM(TRY_CAST(o.price AS DECIMAL(18, 2)) * ISNULL(b.travelers, 0)), 0) AS revenue
            FROM dbo.TripBooking b
            INNER JOIN dbo.[Operator] o ON o.id = b.trip_id
            WHERE o.email = ?
            GROUP BY b.trip_id, b.username
        ),
        ranked_trip_stats AS (
            SELECT
                trip_id,
                username,
                full_name,
                email,
                booking_count,
                traveler_count,
                revenue,
                ROW_NUMBER() OVER (
                    PARTITION BY trip_id
                    ORDER BY traveler_count DESC, booking_count DESC, username ASC
                ) AS row_no
            FROM customer_trip_stats
        )
        SELECT
            trip_id,
            username,
            full_name,
            email,
            booking_count,
            traveler_count,
            revenue
        FROM ranked_trip_stats
        WHERE row_no = 1
        """,
        (clean_email,),
    )
    trip_top_customer_map = {}
    for trip_id, username, full_name, email, booking_count, traveler_count, customer_revenue in cursor.fetchall():
        trip_top_customer_map[int(trip_id or 0)] = {
            "username": username or "",
            "name": full_name or username or "",
            "email": email or "",
            "bookings": int(booking_count or 0),
            "travelers": int(traveler_count or 0),
            "revenue": float(customer_revenue or 0),
        }

    trip_breakdown = []
    for trip in trip_options:
        trip_id_value = trip["id"]
        booking_info = trip_booking_map.get(trip_id_value, {})
        trip_travelers = int(booking_info.get("travelers", 0))
        trip_revenue = float(trip_prices.get(trip_id_value, 0) * trip_travelers)
        trip_breakdown.append(
            {
                "trip_id": trip_id_value,
                "trip_name": trip["name"],
                "bookings": int(booking_info.get("bookings", 0)),
                "travelers": trip_travelers,
                "revenue": trip_revenue,
                "top_customer": trip_top_customer_map.get(
                    trip_id_value,
                    {
                        "username": "",
                        "name": "No bookings yet",
                        "email": "",
                        "bookings": 0,
                        "travelers": 0,
                        "revenue": 0,
                    },
                ),
            }
        )

    cursor.execute(
        """
        SELECT
            CONCAT('W', RIGHT('0' + CAST(DATEPART(ISO_WEEK, week_start) AS VARCHAR(2)), 2)) AS label,
            COALESCE(SUM(revenue_amount), 0) AS revenue
        FROM (
            SELECT
                DATEADD(day, 1 - DATEPART(weekday, CAST(b.created_at AS DATE)), CAST(b.created_at AS DATE)) AS week_start,
                TRY_CAST(o.price AS DECIMAL(18, 2)) * ISNULL(b.travelers, 0) AS revenue_amount
            FROM dbo.TripBooking b
            INNER JOIN dbo.[Operator] o ON o.id = b.trip_id
            WHERE o.email = ?
              AND b.created_at >= DATEADD(day, -56, CAST(GETDATE() AS DATE))
        ) revenue_rows
        GROUP BY week_start
        ORDER BY MIN(week_start) ASC
        """,
        (clean_email,),
    )
    weekly_revenue = [{"label": label, "value": float(value or 0)} for label, value in cursor.fetchall()]

    cursor.execute(
        """
        SELECT
            CONCAT(LEFT(DATENAME(month, month_start), 3), ' ', YEAR(month_start)) AS label,
            COALESCE(SUM(revenue_amount), 0) AS revenue
        FROM (
            SELECT
                DATEFROMPARTS(YEAR(b.created_at), MONTH(b.created_at), 1) AS month_start,
                TRY_CAST(o.price AS DECIMAL(18, 2)) * ISNULL(b.travelers, 0) AS revenue_amount
            FROM dbo.TripBooking b
            INNER JOIN dbo.[Operator] o ON o.id = b.trip_id
            WHERE o.email = ?
              AND b.created_at >= DATEADD(month, -11, DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1))
        ) revenue_rows
        GROUP BY month_start
        ORDER BY MIN(month_start) ASC
        """,
        (clean_email,),
    )
    monthly_revenue = [{"label": label, "value": float(value or 0)} for label, value in cursor.fetchall()]

    cursor.execute(
        """
        SELECT
            COUNT(*) AS customer_count,
            SUM(CASE WHEN booking_count > 1 THEN 1 ELSE 0 END) AS repeat_customers,
            SUM(CASE WHEN booking_count = 1 THEN 1 ELSE 0 END) AS single_booking_customers,
            AVG(CAST(total_travelers AS FLOAT)) AS avg_travelers
        FROM (
            SELECT
                b.username,
                COUNT(*) AS booking_count,
                SUM(b.travelers) AS total_travelers
            FROM dbo.TripBooking b
            INNER JOIN dbo.[Operator] o ON o.id = b.trip_id
            WHERE o.email = ?
            GROUP BY b.username
        ) customer_stats
        """,
        (clean_email,),
    )
    behavior_row = cursor.fetchone()

    cursor.execute(
        """
        SELECT
            payment_mode,
            COUNT(*) AS booking_count
        FROM dbo.TripBooking b
        INNER JOIN dbo.[Operator] o ON o.id = b.trip_id
        WHERE o.email = ?
        GROUP BY payment_mode
        ORDER BY booking_count DESC, payment_mode ASC
        """,
        (clean_email,),
    )
    payment_modes = [
        {"label": payment_mode or "Unknown", "value": int(booking_count or 0)}
        for payment_mode, booking_count in cursor.fetchall()
    ]

    cursor.execute(
        """
        SELECT TOP 5
            b.username,
            MAX(b.full_name) AS full_name,
            MAX(b.email) AS email,
            COUNT(*) AS booking_count,
            SUM(b.travelers) AS traveler_count,
            COALESCE(SUM(TRY_CAST(o.price AS DECIMAL(18, 2)) * ISNULL(b.travelers, 0)), 0) AS revenue
        FROM dbo.TripBooking b
        INNER JOIN dbo.[Operator] o ON o.id = b.trip_id
        WHERE o.email = ?
        GROUP BY b.username
        ORDER BY traveler_count DESC, booking_count DESC, full_name ASC
        """,
        (clean_email,),
    )
    top_customers = [
        {
            "username": username or "",
            "name": full_name or username or "",
            "email": email or "",
            "bookings": int(booking_count or 0),
            "travelers": int(traveler_count or 0),
            "revenue": float(customer_revenue or 0),
        }
        for username, full_name, email, booking_count, traveler_count, customer_revenue in cursor.fetchall()
    ]

    customer_behavior = {
        "avg_travelers_per_booking": round(float(behavior_row[3] or 0), 1) if behavior_row else 0,
        "repeat_customers": int(behavior_row[1] or 0) if behavior_row else 0,
        "single_booking_customers": int(behavior_row[2] or 0) if behavior_row else 0,
        "payment_modes": payment_modes,
        "top_customers": top_customers,
    }

    return {
        "trips": trips,
        "bookings": bookings,
        "revenue": revenue,
        "monthly_bookings": monthly_bookings,
        "trip_options": trip_options,
        "trip_breakdown": trip_breakdown,
        "revenue_breakdown": {
            "weekly": weekly_revenue,
            "monthly": monthly_revenue,
        },
        "customer_behavior": customer_behavior,
    }


def build_operator_dashboard_view_model(metrics):
    metrics = metrics or {}
    trip_breakdown = metrics.get("trip_breakdown") or []
    trip_options = metrics.get("trip_options") or []
    customer_behavior = metrics.get("customer_behavior") or {}
    revenue_breakdown = metrics.get("revenue_breakdown") or {}
    top_customers = customer_behavior.get("top_customers") or []

    overall_top_customer = top_customers[0] if top_customers else {
        "name": "No bookings yet",
        "bookings": 0,
        "travelers": 0,
        "revenue": 0,
        "email": "",
    }
    total_travelers = sum(int(trip.get("travelers") or 0) for trip in trip_breakdown)

    overview_by_selection = {
        "all": {
            "trips": int(metrics.get("trips") or 0),
            "bookings": int(metrics.get("bookings") or 0),
            "travelers": total_travelers,
            "revenue": float(metrics.get("revenue") or 0),
            "top_customer": overall_top_customer,
        }
    }

    for trip in trip_breakdown:
        trip_id = str(trip.get("trip_id"))
        overview_by_selection[trip_id] = {
            "trips": 1,
            "bookings": int(trip.get("bookings") or 0),
            "travelers": int(trip.get("travelers") or 0),
            "revenue": float(trip.get("revenue") or 0),
            "top_customer": trip.get("top_customer") or overall_top_customer,
        }

    return {
        "trip_options": trip_options,
        "overview_by_selection": overview_by_selection,
        "revenue_breakdown": revenue_breakdown,
        "trip_revenue_chart": {
            "labels": [trip.get("trip_name") or "Trip" for trip in trip_breakdown],
            "values": [float(trip.get("revenue") or 0) for trip in trip_breakdown],
        },
        "payment_mode_chart": {
            "labels": [item.get("label") or "" for item in customer_behavior.get("payment_modes") or []],
            "values": [int(item.get("value") or 0) for item in customer_behavior.get("payment_modes") or []],
        },
        "customer_behavior": {
            "avg_travelers_per_booking": customer_behavior.get("avg_travelers_per_booking", 0),
            "repeat_customers": int(customer_behavior.get("repeat_customers") or 0),
            "single_booking_customers": int(customer_behavior.get("single_booking_customers") or 0),
            "top_customers": top_customers,
        },
    }


def has_user_booked_trip(username, trip_id):
    if cursor is None:
        return False
    if not ensure_booking_table():
        return False

    cursor.execute(
        """
        SELECT TOP 1 1
        FROM dbo.TripBooking
        WHERE username = ? AND trip_id = ?
        ORDER BY id DESC
        """,
        (username, trip_id),
    )
    return cursor.fetchone() is not None


def ensure_chat_table():
    if cursor is None:
        return False
    try:
        cursor.execute(
            """
            IF OBJECT_ID('dbo.TripChat', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.TripChat (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    username NVARCHAR(80) NOT NULL,
                    trip_id INT NOT NULL,
                    sender_role NVARCHAR(30) NOT NULL,
                    message_text NVARCHAR(MAX) NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT GETDATE()
                )
            END
            """
        )
        conn.commit()
        return True
    except Exception:
        if conn:
            conn.rollback()
        return False


def ensure_feedback_table():
    if cursor is None:
        return False
    try:
        cursor.execute(
            """
            IF OBJECT_ID('dbo.TripFeedback', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.TripFeedback (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    username NVARCHAR(80) NOT NULL,
                    trip_id INT NOT NULL,
                    feedback_text NVARCHAR(MAX) NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT GETDATE()
                )
            END
            """
        )
        conn.commit()
        return True
    except Exception:
        if conn:
            conn.rollback()
        return False


def add_chat_message(username, trip_id, sender_role, message_text):
    if cursor is None or conn is None:
        return "db_unavailable"
    if not ensure_chat_table():
        return "failed"

    clean_message = (message_text or "").strip()
    if not clean_message:
        return "failed"

    try:
        cursor.execute(
            """
            INSERT INTO dbo.TripChat (username, trip_id, sender_role, message_text)
            VALUES (?, ?, ?, ?)
            """,
            (username, trip_id, sender_role, clean_message),
        )
        conn.commit()
        return "success"
    except Exception:
        conn.rollback()
        return "failed"


def get_user_trip_feedback(username, trip_id):
    if cursor is None:
        return None
    if not ensure_feedback_table():
        return None

    cursor.execute(
        """
        SELECT TOP 1 feedback_text, created_at
        FROM dbo.TripFeedback
        WHERE username = ? AND trip_id = ?
        ORDER BY id DESC
        """,
        (username, trip_id),
    )
    row = cursor.fetchone()
    if not row:
        return None

    return {
        "feedback_text": row[0] or "",
        "created_at": row[1],
    }


def save_trip_feedback(username, trip_id, feedback_text):
    if cursor is None or conn is None:
        return "db_unavailable"
    if not ensure_feedback_table():
        return "failed"

    clean_feedback = (feedback_text or "").strip()
    if not clean_feedback:
        return "failed"
    if get_user_trip_feedback(username, trip_id):
        return "already_saved"

    try:
        cursor.execute(
            """
            INSERT INTO dbo.TripFeedback (username, trip_id, feedback_text)
            VALUES (?, ?, ?)
            """,
            (username, trip_id, clean_feedback),
        )
        conn.commit()
        return "success"
    except Exception:
        conn.rollback()
        return "failed"


def get_trip_chat_messages(trip_id):
    if cursor is None:
        return []
    if not ensure_chat_table():
        return []

    cursor.execute(
        """
        SELECT
            c.id,
            c.username,
            c.trip_id,
            c.sender_role,
            c.message_text,
            c.created_at,
            COALESCE(r.name, c.username) AS sender_name
        FROM dbo.TripChat c
        LEFT JOIN dbo.[register] r ON r.username = c.username
        WHERE c.trip_id = ?
        ORDER BY id ASC
        """,
        (trip_id,),
    )
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in rows]
