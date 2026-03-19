import re
from pathlib import Path

path = Path(__file__).resolve().parent / "booking_service.py"
text = path.read_text(encoding="utf-8")

# Remove SQL Server schema prefixes
text = re.sub(r"\bdbo\.\b", "", text)

# Unwrap SQL bracketed table names for our sqlite schema
text = re.sub(r"\[(Operator|TripBooking|OperatorDay|OperatorGallery|OperatorDayGallery|register|login|TripChat|TripFeedback)\]", r"\1", text)

# Replace SQL Server TOP 1 syntax with sqlite LIMIT 1
text = re.sub(r"SELECT\s+TOP\s+1", "SELECT", text, flags=re.IGNORECASE)
text = re.sub(r"ORDER BY id DESC\s*\n\s*\"\"\"", "ORDER BY id DESC\n        LIMIT 1\n        \"\"\"", text)

# Replace GETDATE cast with sqlite date('now')
text = re.sub(r"CAST\(GETDATE\(\) AS DATE\)", "date('now')", text, flags=re.IGNORECASE)

# Replace ISNULL with IFNULL
text = re.sub(r"\bISNULL\b", "IFNULL", text, flags=re.IGNORECASE)

# Replace TRY_CAST(... AS DECIMAL(...)) with CAST(... AS REAL)
text = re.sub(r"TRY_CAST\(([^)]+) AS DECIMAL\([^)]+\)\)", r"CAST(\1 AS REAL)", text, flags=re.IGNORECASE)

# Ensure DATEDIFF is replaced with sqlite julianday difference if any remain
text = re.sub(r"DATEDIFF\(day, ([^,]+), ([^)]+)\) \+ 1", r"CAST(julianday(\2) - julianday(\1) + 1 AS INTEGER)", text, flags=re.IGNORECASE)

path.write_text(text, encoding="utf-8")
print(f"Updated {path}")
