from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from regi import register_user, login_user, get_user_profile
from operator_service import (
    operator as create_operator_trip,
    get_operator_trips,
    get_operator_trip_detail,
    get_operator_day_details,
    get_operator_trips_by_email,
    update_operator_itinerary,
    delete_operator_trip,
)
from booking_service import (
    create_booking,
    get_traveller_trip_stats,
    get_traveller_bookings,
    get_traveller_dashboard_metrics,
    get_city_region,
    get_home_trip_recommendations,
)
from booking_service import (
    get_operator_dashboard_metrics,
    build_operator_dashboard_view_model,
    get_trip_booking_summary_map,
    has_user_booked_trip,
    get_user_trip_booking,
    add_chat_message,
    get_trip_chat_messages,
    get_user_trip_feedback,
    save_trip_feedback,
)
from werkzeug.utils import secure_filename
import os
import re
import uuid
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "travista-dev-secret-key")

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

CITY_PINCODE_PREFIXES = {
    "Visakhapatnam": ("530",),
    "Vijayawada": ("520",),
    "Guntur": ("522",),
    "Tirupati": ("517",),
    "Itanagar": ("791",),
    "Naharlagun": ("791",),
    "Guwahati": ("781",),
    "Dibrugarh": ("786",),
    "Silchar": ("788",),
    "Patna": ("800", "801"),
    "Gaya": ("823",),
    "Bhagalpur": ("812", "813"),
    "Raipur": ("492",),
    "Bilaspur": ("495",),
    "Bhilai": ("490",),
    "Panaji": ("403",),
    "Margao": ("403",),
    "Vasco da Gama": ("403",),
    "Ahmedabad": ("380",),
    "Surat": ("395",),
    "Vadodara": ("390",),
    "Rajkot": ("360",),
    "Gurugram": ("122",),
    "Faridabad": ("121",),
    "Panipat": ("132",),
    "Shimla": ("171",),
    "Manali": ("175",),
    "Dharamshala": ("176",),
    "Ranchi": ("834",),
    "Jamshedpur": ("831",),
    "Dhanbad": ("826",),
    "Bengaluru": ("560",),
    "Mysuru": ("570",),
    "Mangaluru": ("575",),
    "Hubballi": ("580",),
    "Kochi": ("682",),
    "Thiruvananthapuram": ("695",),
    "Kozhikode": ("673",),
    "Bhopal": ("462",),
    "Indore": ("452",),
    "Gwalior": ("474",),
    "Mumbai": ("400", "401"),
    "Pune": ("411", "412"),
    "Nagpur": ("440",),
    "Nashik": ("422",),
    "Thane": ("400", "401"),
    "Bhubaneswar": ("751",),
    "Cuttack": ("753",),
    "Rourkela": ("769",),
    "Puri": ("752",),
    "Ludhiana": ("141",),
    "Amritsar": ("143",),
    "Jalandhar": ("144",),
    "Jaipur": ("302",),
    "Jodhpur": ("342",),
    "Udaipur": ("313",),
    "Kota": ("324",),
    "Chennai": ("600",),
    "Coimbatore": ("641",),
    "Madurai": ("625",),
    "Salem": ("636",),
    "Hyderabad": ("500",),
    "Warangal": ("506",),
    "Nizamabad": ("503",),
    "Lucknow": ("226",),
    "Noida": ("201",),
    "Kanpur": ("208",),
    "Agra": ("282",),
    "Varanasi": ("221",),
    "Kolkata": ("700",),
    "Howrah": ("711",),
    "Durgapur": ("713",),
}


def normalize_role(role):
    role_text = (role or "").strip().lower()
    if role_text in {"operator", "tour operator"}:
        return "tour operator"
    return "traveller"


def as_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def is_valid_city_pincode(city, pincode):
    clean_pin = "".join(ch for ch in str(pincode or "") if ch.isdigit())
    if len(clean_pin) != 6:
        return False

    prefixes = CITY_PINCODE_PREFIXES.get((city or "").strip())
    if not prefixes:
        return True

    return any(clean_pin.startswith(prefix) for prefix in prefixes)


def get_city_options():
    return sorted(CITY_PINCODE_PREFIXES.keys())


def filter_trips_by_preference(trips, preference):
    if not preference:
        return trips

    def normalize_city(value):
        return " ".join(str(value or "").strip().lower().split())

    source = normalize_city(preference.get("source"))
    destination = normalize_city(preference.get("destination"))
    pref_date = preference.get("traveldate")

    filtered = []
    for trip in trips:
        trip_source = normalize_city(trip.get("sourcee"))
        trip_destination = normalize_city(trip.get("destination"))
        trip_source_date = as_date(trip.get("sourcedate"))
        pref_date_value = as_date(pref_date) if pref_date else None

        if source and source != trip_source:
            continue
        if destination and destination != trip_destination:
            continue
        if pref_date_value and trip_source_date and trip_source_date < pref_date_value:
            continue
        filtered.append(trip)
    return filtered


def is_tomorrow_or_later(value):
    date_value = as_date(value)
    if not date_value:
        return False
    return date_value > date.today()


def split_ampm_time(value):
    if isinstance(value, datetime):
        value = value.time()
    if hasattr(value, "strftime") and not isinstance(value, str):
        raw = value.strftime("%I:%M %p")
    else:
        raw = value or ""
    raw = str(raw).strip()
    if not raw:
        return "", "AM"
    parts = raw.split()
    if len(parts) == 2 and parts[1].upper() in {"AM", "PM"}:
        return parts[0], parts[1].upper()
    return raw, "AM"


def normalize_digits(value):
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def validate_booking_payment(form):
    payment_mode = (form.get("payment_mode") or "").strip()
    payment_summary = payment_mode
    payment_details = {
        "payment_mode": payment_mode,
        "upi_app": (form.get("upi_app") or "").strip(),
        "upi_id": (form.get("upi_id") or "").strip(),
        "card_holder": (form.get("card_holder") or "").strip(),
        "card_number": (form.get("card_number") or "").strip(),
        "card_expiry": (form.get("card_expiry") or "").strip(),
        "card_cvv": (form.get("card_cvv") or "").strip(),
        "bank_name": (form.get("bank_name") or "").strip(),
        "account_number": (form.get("account_number") or "").strip(),
        "ifsc_code": (form.get("ifsc_code") or "").strip().upper(),
    }

    if payment_mode == "UPI":
        if payment_details["upi_app"] not in {"GPay", "PhonePe", "Paytm"}:
            return None, payment_details, "Select a valid UPI app."
        if not re.fullmatch(r"[A-Za-z0-9.\-_]{2,}@[A-Za-z]{2,}", payment_details["upi_id"]):
            return None, payment_details, "Enter a valid UPI ID."
        payment_summary = f"UPI - {payment_details['upi_app']}"

    elif payment_mode == "Card":
        card_number = normalize_digits(payment_details["card_number"])
        if len(payment_details["card_holder"]) < 3:
            return None, payment_details, "Enter the card holder name."
        if len(card_number) != 16:
            return None, payment_details, "Enter a valid 16-digit card number."
        if not re.fullmatch(r"(0[1-9]|1[0-2])/\d{2}", payment_details["card_expiry"]):
            return None, payment_details, "Enter card expiry in MM/YY format."
        expiry_month, expiry_year = payment_details["card_expiry"].split("/")
        expiry_year_full = 2000 + int(expiry_year)
        current_month_start = date.today().replace(day=1)
        expiry_start = date(expiry_year_full, int(expiry_month), 1)
        if expiry_start < current_month_start:
            return None, payment_details, "Card expiry must be current or future."
        if len(normalize_digits(payment_details["card_cvv"])) != 3:
            return None, payment_details, "Enter a valid 3-digit CVV."
        payment_summary = f"Card ending {card_number[-4:]}"

    elif payment_mode == "Net Banking":
        account_number = normalize_digits(payment_details["account_number"])
        if payment_details["bank_name"] not in {"SBI", "HDFC", "ICICI", "Axis Bank"}:
            return None, payment_details, "Select a valid bank for net banking."
        if len(account_number) < 9 or len(account_number) > 18:
            return None, payment_details, "Enter a valid account number."
        if not re.fullmatch(r"[A-Z]{4}0[A-Z0-9]{6}", payment_details["ifsc_code"]):
            return None, payment_details, "Enter a valid IFSC code."
        payment_summary = f"Net Banking - {payment_details['bank_name']}"

    elif payment_mode == "Cash":
        payment_summary = "Cash"
    else:
        return None, payment_details, "Select a valid payment method."

    return payment_summary, payment_details, None


@app.route("/")
def root():
    return redirect(url_for("index"))


@app.route("/index")
def index():
    return render_template("index.html")


@app.route("/home")
def home():
    trips = get_operator_trips()
    current_username = session.get("username", "")
    current_role = session.get("role", "")
    preference = session.get("preference") if current_role == "traveller" else None
    today = date.today()

    if current_role == "traveller":
        trips = [
            trip
            for trip in trips
            if as_date(trip.get("destinationdate")) and as_date(trip.get("destinationdate")) >= today
        ]

    trips = filter_trips_by_preference(trips, preference)
    trip_ids = [trip["id"] for trip in trips if trip.get("id") is not None]
    booking_summary = get_trip_booking_summary_map(trip_ids)

    for trip in trips:
        summary = booking_summary.get(int(trip["id"]), {})
        trip["booking_count"] = summary.get("booking_count", 0)
        trip["traveler_count"] = summary.get("traveler_count", 0)
        trip["trip_region"] = get_city_region(trip.get("destination")) or get_city_region(trip.get("sourcee")) or ""

    recommendation_sets = get_home_trip_recommendations(current_username, current_role, trips)

    avatar_letter = current_username[:1].upper() if current_username else "G"
    return render_template(
        "home.html",
        trips=recommendation_sets["all_trips"],
        recommended_trips=recommendation_sets["recommended_trips"],
        is_new_traveller=recommendation_sets.get("is_new_traveller", False),
        current_username=current_username,
        avatar_letter=avatar_letter,
        current_role=current_role,
        has_preference=bool(preference),
    )


@app.route("/dashboard")
def user_dashboard():
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))

    if session.get("role") == "tour operator":
        return redirect(url_for("operator_dashboard"))
    return redirect(url_for("traveller_dashboard"))


@app.route("/traveller/dashboard")
def traveller_dashboard():
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))
    if session.get("role") == "tour operator":
        return redirect(url_for("operator_dashboard"))

    user = get_user_profile(username)
    if not user:
        return redirect(url_for("login"))

    traveller_stats = get_traveller_trip_stats(username)
    traveller_bookings = get_traveller_bookings(username)
    traveller_dashboard_metrics = get_traveller_dashboard_metrics(username)
    profile_stats = {
        "total": traveller_stats["total_trips"],
        "completed": traveller_stats["completed_trips"],
        "upcoming": traveller_stats["upcoming_trips"],
    }

    return render_template(
        "traveller_dashboard.html",
        user=user,
        role="traveller",
        profile_stats=profile_stats,
        traveller_bookings=traveller_bookings,
        traveller_dashboard=traveller_dashboard_metrics,
    )


@app.route("/package/<int:trip_id>")
def package_detail(trip_id):
    trip = get_operator_trip_detail(trip_id)
    if not trip:
        return "Trip not found", 404
    if session.get("role") == "traveller":
        trip_end_date = as_date(trip.get("destinationdate"))
        if trip_end_date and trip_end_date < date.today():
            return "Completed trip itinerary is no longer available for travellers.", 403
    days = get_operator_day_details(trip_id)
    username = session.get("username")
    can_check_booking = session.get("role") == "traveller" and username
    has_booked = has_user_booked_trip(username, trip_id) if can_check_booking else False
    return render_template("package_detail.html", trip=trip, days=days, has_booked=has_booked)


@app.route("/book/<int:trip_id>", methods=["GET", "POST"])
def book_trip(trip_id):
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))
    if session.get("role") == "tour operator":
        return "Only travellers can book trips.", 403

    trip = get_operator_trip_detail(trip_id)
    if not trip:
        return "Trip not found", 404
    trip_end_date = as_date(trip.get("destinationdate"))
    if trip_end_date and trip_end_date < date.today():
        return "Completed trip itinerary is no longer available for travellers.", 403

    days = get_operator_day_details(trip_id)
    current_user = get_user_profile(username) or {}
    per_person_price = float(trip.get("price") or 0)
    existing_booking = get_user_trip_booking(username, trip_id)

    if existing_booking:
        existing_travelers = int(existing_booking.get("travelers") or 0)
        existing_booking["travelers"] = existing_travelers
        existing_booking["total_price"] = per_person_price * existing_travelers
        return render_template(
            "book_trip.html",
            trip=trip,
            days=days,
            booked=True,
            booking=existing_booking,
            current_user=current_user,
            can_chat=True,
            booking_message="You already booked this trip. Duplicate booking is not allowed.",
        )

    if request.method == "POST":
        travelers_value = request.form.get("travelers", "").strip()
        travelers_count = int(travelers_value) if travelers_value.isdigit() and int(travelers_value) > 0 else 1
        payment_summary, payment_details, payment_error = validate_booking_payment(request.form)
        booking = {
            "full_name": request.form.get("full_name", "").strip(),
            "email": request.form.get("email", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "travelers": str(travelers_count),
            "payment_mode": request.form.get("payment_mode", "").strip(),
            "payment_summary": payment_summary or request.form.get("payment_mode", "").strip(),
            "special_notes": request.form.get("special_notes", "").strip(),
            "booking_ref": f"BK{uuid.uuid4().hex[:8].upper()}",
            "total_price": per_person_price * travelers_count,
        }
        booking.update(payment_details)

        if travelers_count > 12:
            return render_template(
                "book_trip.html",
                trip=trip,
                days=days,
                booked=False,
                booking=booking,
                booking_error="One account can book a maximum of 12 travellers only.",
                current_user=current_user,
                can_chat=False,
                per_person_price=per_person_price,
            )

        if payment_error:
            return render_template(
                "book_trip.html",
                trip=trip,
                days=days,
                booked=False,
                booking=booking,
                booking_error=payment_error,
                current_user=current_user,
                can_chat=False,
                per_person_price=per_person_price,
            )

        save_status = create_booking(
            username=username,
            trip_id=trip_id,
            full_name=booking["full_name"],
            email=booking["email"],
            phone=booking["phone"],
            travelers=booking["travelers"],
            payment_mode=booking["payment_summary"],
            special_notes=booking["special_notes"],
            booking_ref=booking["booking_ref"],
        )
        if save_status == "already_booked":
            current_booking = get_user_trip_booking(username, trip_id) or {}
            current_booking["travelers"] = int(current_booking.get("travelers") or 0)
            current_booking["total_price"] = per_person_price * current_booking["travelers"]
            return render_template(
                "book_trip.html",
                trip=trip,
                days=days,
                booked=True,
                booking=current_booking,
                current_user=current_user,
                can_chat=True,
                booking_message="You already booked this trip. Duplicate booking is not allowed.",
            )
        if save_status != "success":
            return "Unable to save booking. Please try again."

        add_chat_message(username, trip_id, "system", "Get ready for the trip.")

        return render_template(
            "book_trip.html",
            trip=trip,
            days=days,
            booked=True,
            booking={**booking, "payment_mode": booking["payment_summary"]},
            current_user=current_user,
            can_chat=True,
            show_booking_popup=True,
        )

    booking_defaults = {
        "full_name": current_user.get("name", ""),
        "email": current_user.get("email", ""),
        "phone": current_user.get("phone", ""),
    }
    return render_template(
        "book_trip.html",
        trip=trip,
        days=days,
        booked=False,
        booking=booking_defaults,
        booking_error="",
        current_user=current_user,
        can_chat=False,
        per_person_price=per_person_price,
    )


@app.route("/chat/<int:trip_id>", methods=["GET"])
def trip_chat(trip_id):
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))
    if session.get("role") != "traveller":
        return "Only travellers can access this chat.", 403
    if not has_user_booked_trip(username, trip_id):
        return "Chat available only after booking this trip.", 403

    trip = get_operator_trip_detail(trip_id)
    if not trip:
        return "Trip not found", 404

    trip_end_date = as_date(trip.get("destinationdate"))
    chat_closed = bool(trip_end_date and trip_end_date < date.today())
    feedback = get_user_trip_feedback(username, trip_id)

    return render_template(
        "chat.html",
        trip=trip,
        current_username=username,
        chat_closed=chat_closed,
        feedback=feedback,
    )


@app.route("/chat/<int:trip_id>/feedback", methods=["POST"])
def trip_feedback(trip_id):
    username = session.get("username")
    if not username:
        return jsonify({"error": "login_required"}), 401
    if session.get("role") != "traveller":
        return jsonify({"error": "traveller_only"}), 403
    if not has_user_booked_trip(username, trip_id):
        return jsonify({"error": "booking_required"}), 403

    trip = get_operator_trip_detail(trip_id)
    if not trip:
        return jsonify({"error": "trip_not_found"}), 404

    trip_end_date = as_date(trip.get("destinationdate"))
    if not trip_end_date or trip_end_date >= date.today():
        return jsonify({"error": "feedback_not_open"}), 400

    payload = request.get_json(silent=True) or {}
    feedback_text = (payload.get("feedback") or "").strip()
    status = save_trip_feedback(username, trip_id, feedback_text)
    if status == "already_saved":
        return jsonify({"error": "already_saved"}), 409
    if status != "success":
        return jsonify({"error": "save_failed"}), 500

    feedback = get_user_trip_feedback(username, trip_id)
    return jsonify(
        {
            "status": "success",
            "feedback": {
                "feedback_text": feedback.get("feedback_text", "") if feedback else feedback_text,
            },
        }
    )


@app.route("/chat/<int:trip_id>/messages", methods=["GET", "POST"])
def trip_chat_messages(trip_id):
    username = session.get("username")
    if not username:
        return jsonify({"error": "login_required"}), 401
    if session.get("role") != "traveller":
        return jsonify({"error": "traveller_only"}), 403
    if not has_user_booked_trip(username, trip_id):
        return jsonify({"error": "booking_required"}), 403


    trip = get_operator_trip_detail(trip_id)
    if not trip:
        return jsonify({"error": "trip_not_found"}), 404

    trip_end_date = as_date(trip.get("destinationdate"))
    chat_closed = bool(trip_end_date and trip_end_date < date.today())
    feedback = get_user_trip_feedback(username, trip_id)

    if request.method == "POST":
        if chat_closed:
            return jsonify({"error": "chat_closed"}), 403
        payload = request.get_json(silent=True) or {}
        message = (payload.get("message") or "").strip()
        if not message:
            return jsonify({"error": "message_required"}), 400

        save_status = add_chat_message(username, trip_id, "traveller", message)
        if save_status != "success":
            return jsonify({"error": "save_failed"}), 500

    messages = get_trip_chat_messages(trip_id)
    serialized_messages = []
    for msg in messages:
        created_at_value = msg.get("created_at")
        if isinstance(created_at_value, datetime):
            created_at_text = created_at_value.strftime("%d %b %Y, %I:%M %p")
        else:
            created_at_text = str(created_at_value or "")

        serialized_messages.append(
            {
                "id": int(msg.get("id") or 0),
                "username": msg.get("username", ""),
                "sender_name": msg.get("sender_name", msg.get("username", "")),
                "sender_role": msg.get("sender_role", ""),
                "message_text": msg.get("message_text", ""),
                "created_at": created_at_text,
                "is_mine": msg.get("username", "") == username,
            }
        )

    response = {
        "messages": serialized_messages,
        "operator": {
            "name": trip.get("name", ""),
            "email": trip.get("email", ""),
            "phone": str(trip.get("tel", "") or "").strip(),
        },
        "chat_closed": chat_closed,
        "feedback": feedback,
    }
    return jsonify(response)


@app.route("/regi", methods=["GET", "POST"])
def regi():
    form_data = {}
    if request.method == "POST":
        data = request.form
        form_data = data.to_dict()

        if data["password"] != request.form["confirm_password"]:
            return render_template("regi.html", error="Passwords do not match.", form_data=form_data)
        if not is_valid_city_pincode(data.get("city"), data.get("pincode")):
            return render_template(
                "regi.html",
                error="Invalid pincode. City and pincode should match.",
                form_data=form_data,
            )

        success = register_user(
            data["name"],
            data["age"],
            data["email"],
            data["phone"],
            data["role"],
            data["state"],
            data["city"],
            data["pincode"],
            data["address"],
            data["username"],
            data["password"],
        )

        if success == "duplicate":
            return render_template("regi.html", error="Email or Username already exists.", form_data=form_data)

        if success == "db_unavailable":
            return render_template(
                "regi.html",
                error="Database not connected. Please check SQL Server and try again.",
                form_data=form_data,
            )

        if success == "success":
            return redirect(url_for("login"))

        return render_template("regi.html", error="Registration failed.", form_data=form_data)

    return render_template("regi.html", form_data=form_data)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = login_user(username, password)
        print("Login result:", user)

        if user == "db_unavailable":
            return render_template(
                "login.html",
                error="Database not connected. Please check SQL Server and try again.",
            )

        if user:
            role = normalize_role(user[0])
            print("role from DB:", role)
            session.clear()
            session["username"] = username
            session["role"] = role

            if role == "tour operator":
                return redirect(url_for("operator_dashboard"))
            return redirect(url_for("home"))

        return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")


@app.route("/preference", methods=["GET", "POST"])
def preference():
    if session.get("role") != "traveller":
        return redirect(url_for("home"))

    if request.method == "POST":
        source = (request.form.get("source") or "").strip()
        destination = (request.form.get("destination") or "").strip()
        days_value = (request.form.get("days") or "").strip()
        budget_value = (request.form.get("budget") or "").strip()
        people_value = (request.form.get("people") or "").strip()
        date_value = (request.form.get("traveldate") or "").strip()
        rating_value = (request.form.get("rating") or "").strip()
        if source and destination and source.lower() == destination.lower():
            return "Source and destination cannot be the same."
        if date_value and not is_tomorrow_or_later(date_value):
            return "Preference date must be from tomorrow onwards."

        preference_data = {
            "source": source,
            "destination": destination,
            "days": int(days_value) if days_value.isdigit() else None,
            "budget": float(budget_value) if budget_value.isdigit() else None,
            "people": int(people_value) if people_value.isdigit() else None,
            "traveldate": date_value or None,
            "rating": int(rating_value) if rating_value.isdigit() else None,
        }
        session["preference"] = preference_data
        return redirect(url_for("home"))

    return render_template(
        "preference.html",
        preference=session.get("preference", {}),
        cities=get_city_options(),
    )


@app.route("/profile")
def profile():
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))

    user = get_user_profile(username)
    if not user:
        return redirect(url_for("login"))

    role = normalize_role(user.get("role"))
    profile_stats = {"total": 0, "completed": 0, "upcoming": 0}
    operator_trips = []
    traveller_bookings = []
    traveller_dashboard = None

    if role == "tour operator":
        operator_trips = get_operator_trips_by_email(user.get("email", ""))
        profile_stats["total"] = len(operator_trips)
        today = date.today()
        profile_stats["completed"] = sum(
            1
            for trip in operator_trips
            if as_date(trip.get("destinationdate")) and as_date(trip.get("destinationdate")) < today
        )
        profile_stats["upcoming"] = max(profile_stats["total"] - profile_stats["completed"], 0)
    else:
        traveller_stats = get_traveller_trip_stats(username)
        traveller_bookings = get_traveller_bookings(username)
        for booking in traveller_bookings:
            booking["is_completed"] = bool(
                as_date(booking.get("destinationdate")) and as_date(booking.get("destinationdate")) < date.today()
            )
        traveller_dashboard = get_traveller_dashboard_metrics(username)
        profile_stats["total"] = traveller_stats["total_trips"]
        profile_stats["completed"] = traveller_stats["completed_trips"]
        profile_stats["upcoming"] = traveller_stats["upcoming_trips"]

    return render_template(
        "profile.html",
        user=user,
        role=role,
        profile_stats=profile_stats,
        operator_trips=operator_trips,
        traveller_bookings=traveller_bookings,
        traveller_dashboard=traveller_dashboard,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/operator", methods=["GET", "POST"])
def operator():
    if session.get("role") != "tour operator":
        return redirect(url_for("login"))

    username = session.get("username")
    operator_user = get_user_profile(username) if username else None
    if not operator_user:
        return redirect(url_for("login"))

    if request.method == "POST":
        form = request.form
        source_city = (form.get("sourcee") or "").strip()
        destination_city = (form.get("destination") or "").strip()
        source_date = (form.get("sourcedate") or "").strip()
        destination_date = (form.get("destinationdate") or "").strip()
        journey_start = (form.get("journey_start") or "").strip()
        if source_city and destination_city and source_city.lower() == destination_city.lower():
            return "Source and destination cannot be the same."
        if not is_tomorrow_or_later(source_date):
            return "Source date must be from tomorrow onwards."
        if not is_tomorrow_or_later(destination_date):
            return "Destination date must be from tomorrow onwards."
        if not is_tomorrow_or_later(journey_start):
            return "Journey start date must be from tomorrow onwards."
        source_date_obj = as_date(source_date)
        destination_date_obj = as_date(destination_date)
        if source_date_obj and destination_date_obj and destination_date_obj < source_date_obj:
            return "Destination date must be on or after source date."

        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

        def save_upload(file_obj):
            if not file_obj or not file_obj.filename:
                return ""
            safe_name = secure_filename(file_obj.filename)
            base, ext = os.path.splitext(safe_name)
            unique_name = f"{base}_{uuid.uuid4().hex}{ext}"
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
            file_obj.save(file_path)
            return unique_name

        def save_uploads(file_list):
            saved = []
            for file_obj in file_list or []:
                file_name = save_upload(file_obj)
                if file_name:
                    saved.append(file_name)
            return saved

        cover_images = save_uploads(request.files.getlist("cover_image"))
        hotel_images = save_uploads(request.files.getlist("hotel_image"))
        place_images = save_uploads(request.files.getlist("place_image"))

        cover_image_name = cover_images[0] if cover_images else ""
        hotel_image_name = hotel_images[0] if hotel_images else ""
        place_image_name = place_images[0] if place_images else ""

        days_count = int(form.get("days") or 0)
        day_details = []
        for i in range(1, days_count + 1):
            day_date = form.get(f"day_{i}_date")
            day_place = form.get(f"day_{i}_place")
            day_time = form.get(f"day_{i}_time")
            day_plan = form.get(f"day_{i}_plan")
            day_image_files = [f for f in request.files.getlist(f"day_{i}_image") if f and f.filename]
            day_image_names = [save_upload(day_img) for day_img in day_image_files]
            day_image_names = [img for img in day_image_names if img]
            day_image_name = day_image_names[0] if day_image_names else ""

            if not (day_date and day_place and day_time and day_plan):
                continue

            day_details.append(
                {
                    "day_no": i,
                    "day_date": day_date,
                    "place": day_place,
                    "time": day_time,
                    "tplan": day_plan,
                    "image_name": day_image_name,
                    "image_names": day_image_names,
                }
            )

        result = create_operator_trip(
            operator_user["name"],
            operator_user["age"],
            operator_user["phone"],
            operator_user["email"],
            form["tripname"],
            form["price"],
            source_city,
            destination_city,
            source_date,
            destination_date,
            form["maximumpeople"],
            form["pickup_time"],
            form["pickuploc"],
            journey_start,
            form["travel_mode"],
            form["travel_d"],
            form["destination_overview"],
            form["hotel_details"],
            form["places_visit"],
            form["amenities"],
            cover_image_name,
            hotel_image_name,
            place_image_name,
            cover_images,
            hotel_images,
            place_images,
            day_details,
        )

        if result == "success":
            return redirect(url_for("operator_dashboard"))

        if result == "db_unavailable":
            return "Database not connected. Please check SQL Server and try again."

        return "Failed to save operator trip details"

    return render_template("operator.html", operator_user=operator_user, cities=get_city_options())


@app.route("/api/operator/trips", methods=["POST"])
def operator_api_create_trip():
    username = session.get("username")
    if not username:
        return jsonify({"error": "login_required"}), 401
    if session.get("role") != "tour operator":
        return jsonify({"error": "operator_only"}), 403

    operator_user = get_user_profile(username) if username else None
    if not operator_user:
        return jsonify({"error": "operator_profile_not_found"}), 404

    payload = request.get_json(silent=True) or {}

    tripname = (payload.get("tripname") or "").strip()
    source_city = (payload.get("sourcee") or "").strip()
    destination_city = (payload.get("destination") or "").strip()
    source_date = (payload.get("sourcedate") or "").strip()
    destination_date = (payload.get("destinationdate") or "").strip()
    journey_start = (payload.get("journey_start") or "").strip()

    missing_fields = []
    required_map = {
        "tripname": tripname,
        "price": payload.get("price"),
        "sourcee": source_city,
        "destination": destination_city,
        "sourcedate": source_date,
        "destinationdate": destination_date,
        "maximumpeople": payload.get("maximumpeople"),
        "pickup_time": payload.get("pickup_time"),
        "pickuploc": pickuploc,
        "journey_start": journey_start,
        "travel_mode": payload.get("travel_mode"),
        "travel_d": travel_d,
    }
    for field_name, field_value in required_map.items():
        if field_value is None or str(field_value).strip() == "":
            missing_fields.append(field_name)
    if missing_fields:
        return jsonify({"error": "missing_fields", "fields": missing_fields}), 400

    if source_city and destination_city and source_city.lower() == destination_city.lower():
        return jsonify({"error": "invalid_route", "message": "Source and destination cannot be the same."}), 400
    if not is_tomorrow_or_later(source_date):
        return jsonify({"error": "invalid_sourcedate", "message": "Source date must be from tomorrow onwards."}), 400
    if not is_tomorrow_or_later(destination_date):
        return jsonify({"error": "invalid_destinationdate", "message": "Destination date must be from tomorrow onwards."}), 400
    if not is_tomorrow_or_later(journey_start):
        return jsonify({"error": "invalid_journey_start", "message": "Journey start date must be from tomorrow onwards."}), 400

    source_date_obj = as_date(source_date)
    destination_date_obj = as_date(destination_date)
    if source_date_obj and destination_date_obj and destination_date_obj < source_date_obj:
        return jsonify({"error": "invalid_date_range", "message": "Destination date must be on or after source date."}), 400

    raw_day_details = payload.get("day_details")
    normalized_day_details = []
    if isinstance(raw_day_details, list):
        for idx, day in enumerate(raw_day_details, start=1):
            if not isinstance(day, dict):
                continue

            day_no_raw = day.get("day_no", idx)
            day_date = (day.get("day_date") or "").strip()
            day_place = (day.get("place") or "").strip()
            day_time = (day.get("time") or "").strip()
            day_plan = (day.get("tplan") or "").strip()

            if not (day_date and day_place and day_time and day_plan):
                continue

            try:
                day_no = int(day_no_raw)
            except (TypeError, ValueError):
                day_no = idx
            if day_no <= 0:
                day_no = idx

            image_name = (day.get("image_name") or "").strip()
            raw_images = day.get("image_names")
            image_names = []
            if isinstance(raw_images, list):
                image_names = [str(img).strip() for img in raw_images if str(img).strip()]
            if image_name and image_name not in image_names:
                image_names = [image_name] + image_names

            normalized_day_details.append(
                {
                    "day_no": day_no,
                    "day_date": day_date,
                    "place": day_place,
                    "time": day_time,
                    "tplan": day_plan,
                    "image_name": image_name,
                    "image_names": image_names,
                }
            )

    cover_images = payload.get("cover_images") or []
    hotel_images = payload.get("hotel_images") or []
    place_images = payload.get("place_images") or []

    pickuploc = (payload.get("pickuploc") or "").strip()
    travel_d = (payload.get("travel_d") or "").strip()

    result = create_operator_trip(
        operator_user.get("name", ""),
        operator_user.get("age", ""),
        operator_user.get("phone", ""),
        operator_user.get("email", ""),
        tripname,
        payload.get("price"),
        source_city,
        destination_city,
        source_date,
        destination_date,
        payload.get("maximumpeople"),
        payload.get("pickup_time"),
        pickuploc,
        journey_start,
        payload.get("travel_mode"),
        travel_d,
        (payload.get("destination_overview") or "").strip(),
        (payload.get("hotel_details") or "").strip(),
        (payload.get("places_visit") or "").strip(),
        (payload.get("amenities") or "").strip(),
        (payload.get("cover_image") or "").strip(),
        (payload.get("hotel_image") or "").strip(),
        (payload.get("place_image") or "").strip(),
        cover_images,
        hotel_images,
        place_images,
        normalized_day_details,
    )

    if result == "success":
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Trip and itinerary saved successfully.",
                    "tripname": tripname,
                    "itinerary_days_saved": len(normalized_day_details),
                }
            ),
            201,
        )

    if result == "db_unavailable":
        return jsonify({"error": "db_unavailable"}), 503

    return jsonify({"error": "save_failed"}), 500


@app.route("/operator/dashboard")
def operator_dashboard():
    if session.get("role") != "tour operator":
        return redirect(url_for("login"))

    username = session.get("username")
    user = get_user_profile(username) if username else None
    if not user:
        return redirect(url_for("login"))

    trips = get_operator_trips_by_email(user.get("email", ""))
    today = date.today()
    completed = sum(
        1 for trip in trips if as_date(trip.get("destinationdate")) and as_date(trip.get("destinationdate")) < today
    )
    upcoming = max(len(trips) - completed, 0)

    stats = {
        "total": len(trips),
        "completed": completed,
        "upcoming": upcoming,
    }
    dashboard_model = build_operator_dashboard_view_model(get_operator_dashboard_metrics(user.get("email", "")))
    return render_template(
        "operator_dashboard.html",
        user=user,
        trips=trips,
        stats=stats,
        dashboard_operator=user.get("username", ""),
        dashboard_model=dashboard_model,
    )


@app.route("/dashboard/<operator>")
def dashboard_api(operator):
    if session.get("role") != "tour operator":
        return jsonify({"error": "operator_only"}), 403

    username = session.get("username")
    if not username:
        return jsonify({"error": "login_required"}), 401
    if username != operator:
        return jsonify({"error": "forbidden"}), 403

    user = get_user_profile(username)
    if not user:
        return jsonify({"error": "operator_not_found"}), 404

    metrics = get_operator_dashboard_metrics(user.get("email", ""))
    return jsonify(metrics)


@app.route("/operator/trip/<int:trip_id>/cancel", methods=["POST"])
def operator_cancel_trip(trip_id):
    if session.get("role") != "tour operator":
        return redirect(url_for("login"))

    username = session.get("username")
    user = get_user_profile(username) if username else None
    if not user:
        return redirect(url_for("login"))

    trip = get_operator_trip_detail(trip_id)
    if not trip or (user.get("email") and trip.get("email") != user.get("email")):
        return "Trip not found", 404

    result = delete_operator_trip(trip_id)
    if result == "success":
        return redirect(url_for("operator_dashboard"))
    if result == "db_unavailable":
        return "Database not connected. Please check SQL Server and try again."
    return "Failed to cancel trip."


@app.route("/operator/trip/<int:trip_id>/edit", methods=["GET", "POST"])
def operator_edit_trip(trip_id):
    if session.get("role") != "tour operator":
        return redirect(url_for("login"))

    username = session.get("username")
    user = get_user_profile(username) if username else None
    if not user:
        return redirect(url_for("login"))

    trip = get_operator_trip_detail(trip_id)
    if not trip or (user.get("email") and trip.get("email") != user.get("email")):
        return "Trip not found", 404

    days = get_operator_day_details(trip_id)
    existing_day_map = {int(day.get("day_no") or 0): day for day in days}

    if request.method == "POST":
        form = request.form
        source_city = (form.get("sourcee") or "").strip()
        destination_city = (form.get("destination") or "").strip()
        source_date = (form.get("sourcedate") or "").strip()
        destination_date = (form.get("destinationdate") or "").strip()
        pick_time = (form.get("pickup_time") or "").strip()
        pickuploc = (form.get("pickuploc") or "").strip()
        journey_start = (form.get("journey_start") or "").strip() or str(trip.get("journey_start") or "")
        travel_mode = (form.get("travel_mode") or "").strip()
        travel_d = (form.get("travel_d") or "").strip()
        price_value = (form.get("price") or "").strip()
        destination_overview = (form.get("destination_overview") or "").strip()
        hotel_details = (form.get("hotel_details") or "").strip()
        places_visit = (form.get("places_visit") or "").strip()
        amenities = (form.get("amenities") or "").strip()

        if source_city and destination_city and source_city.lower() == destination_city.lower():
            return "Source and destination cannot be the same."

        current_source_date = as_date(trip.get("sourcedate"))
        current_destination_date = as_date(trip.get("destinationdate"))
        current_source_text = current_source_date.isoformat() if current_source_date else ""
        current_destination_text = current_destination_date.isoformat() if current_destination_date else ""

        if source_date and source_date != current_source_text and not is_tomorrow_or_later(source_date):
            return "Source date must be from tomorrow onwards."
        if destination_date and destination_date != current_destination_text and not is_tomorrow_or_later(destination_date):
            return "Destination date must be from tomorrow onwards."

        source_date_obj = as_date(source_date) if source_date else current_source_date
        destination_date_obj = as_date(destination_date) if destination_date else current_destination_date
        if source_date_obj and destination_date_obj and destination_date_obj < source_date_obj:
            return "Destination date must be on or after source date."

        if not journey_start:
            journey_start = str(source_date_obj) if source_date_obj else ""

        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

        def save_upload(file_obj):
            if not file_obj or not file_obj.filename:
                return ""
            safe_name = secure_filename(file_obj.filename)
            base, ext = os.path.splitext(safe_name)
            unique_name = f"{base}_{uuid.uuid4().hex}{ext}"
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
            file_obj.save(file_path)
            return unique_name

        if source_date_obj and destination_date_obj:
            days_count = (destination_date_obj - source_date_obj).days + 1
        else:
            days_count = int(trip.get("trip_days") or 0)
        day_details = []
        for i in range(1, days_count + 1):
            day_date = form.get(f"day_{i}_date")
            day_place = form.get(f"day_{i}_place")
            day_time = form.get(f"day_{i}_time")
            day_plan = form.get(f"day_{i}_plan")

            day_image_files = [f for f in request.files.getlist(f"day_{i}_image") if f and f.filename]
            day_image_names = [save_upload(day_img) for day_img in day_image_files]
            day_image_names = [img for img in day_image_names if img]

            if not day_image_names:
                existing_images = existing_day_map.get(i, {}).get("image_names") or []
                day_image_names = [img for img in existing_images if img]

            day_image_name = day_image_names[0] if day_image_names else ""

            if not (day_date and day_place and day_time and day_plan):
                continue

            day_details.append(
                {
                    "day_no": i,
                    "day_date": day_date,
                    "place": day_place,
                    "time": day_time,
                    "tplan": day_plan,
                    "image_name": day_image_name,
                    "image_names": day_image_names,
                }
            )

        result = update_operator_itinerary(
            trip_id,
            price_value,
            source_city or trip.get("sourcee"),
            destination_city or trip.get("destination"),
            source_date or str(trip.get("sourcedate") or ""),
            destination_date or str(trip.get("destinationdate") or ""),
            pick_time,
            pickuploc,
            journey_start,
            travel_mode,
            travel_d,
            destination_overview,
            hotel_details,
            places_visit,
            amenities,
            day_details,
        )

        if result == "success":
            return redirect(url_for("operator_edit_trip", trip_id=trip_id))
        if result == "db_unavailable":
            return "Database not connected. Please check SQL Server and try again."
        return "Failed to update itinerary"

    pickup_time_text, pickup_meridiem = split_ampm_time(trip.get("pick_time"))
    day_view = []
    start_date = as_date(trip.get("sourcedate")) or as_date(trip.get("journey_start"))
    for i in range(1, int(trip.get("trip_days") or 0) + 1):
        day_item = existing_day_map.get(i, {})
        default_date = None
        if start_date:
            default_date = start_date.toordinal() + (i - 1)
            default_date = date.fromordinal(default_date)
        day_date = day_item.get("day_date") or (default_date.isoformat() if default_date else "")
        time_text, time_meridiem = split_ampm_time(day_item.get("time"))
        images = day_item.get("image_names") or []
        day_view.append(
            {
                "day_no": i,
                "day_date": day_date,
                "place": day_item.get("place", ""),
                "time_text": time_text,
                "time_meridiem": time_meridiem,
                "tplan": day_item.get("tplan", ""),
                "images": images,
            }
        )

    return render_template(
        "operator_edit_itinerary.html",
        user=user,
        trip=trip,
        pickup_time_text=pickup_time_text,
        pickup_meridiem=pickup_meridiem,
        day_view=day_view,
        cities=get_city_options(),
    )


if __name__ == "__main__":
    app.run(debug=True)
