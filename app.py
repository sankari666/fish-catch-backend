
import os
import random
import pandas as pd

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

from db import get_cursor, close_db


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)
CORS(app)

# Close database connection automatically after each request
app.teardown_appcontext(close_db)


# ============================================================
# FOLDERS
# ============================================================

UPLOAD_FOLDER = "uploads"
CLEAN_FOLDER = "cleaned"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CLEAN_FOLDER, exist_ok=True)


# ============================================================
# HOME / HEALTH CHECK
# ============================================================

@app.route("/")
def home():
    return jsonify({
        "message": "Fish Catch Repository API is running",
        "status": "success"
    })


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    cursor = get_cursor(dictionary=True)

    # --------------------------------------------------------
    # Total records
    # --------------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*) AS total_records
        FROM fish_data
    """)

    total = cursor.fetchone()

    # --------------------------------------------------------
    # Fish species counts
    # --------------------------------------------------------

    cursor.execute("""
        SELECT fish_name, COUNT(*) AS count
        FROM fish_data
        GROUP BY fish_name
        ORDER BY count DESC
    """)

    species = cursor.fetchall()

    # --------------------------------------------------------
    # Location counts
    # --------------------------------------------------------

    cursor.execute("""
        SELECT location, COUNT(*) AS count
        FROM fish_data
        GROUP BY location
        ORDER BY count DESC
    """)

    locations = cursor.fetchall()

    return jsonify({
        "total_records": total["total_records"],
        "species_data": species,
        "location_data": locations
    })


# ============================================================
# SEARCH FISH DATA
# ============================================================

@app.route("/search")
def search():

    search_term = request.args.get("search", "").strip()

    cursor = get_cursor(dictionary=True)

    if search_term:

        query = """
            SELECT *
            FROM fish_data
            WHERE fish_name LIKE %s
               OR location LIKE %s
        """

        search_value = f"%{search_term}%"

        cursor.execute(
            query,
            (search_value, search_value)
        )

    else:

        cursor.execute("""
            SELECT *
            FROM fish_data
        """)

    rows = cursor.fetchall()

    return jsonify(rows)


# ============================================================
# RECOMMENDATION
# ============================================================

@app.route("/recommend")
def recommend():

    location = request.args.get("location")
    month = request.args.get("month")

    cursor = get_cursor(dictionary=True)

    # --------------------------------------------------------
    # If both filters are provided
    # --------------------------------------------------------

    if location and month:

        query = """
            SELECT fish_name,
                   location,
                   temperature_c,
                   depth_m
            FROM fish_data
            WHERE location = %s
              AND MONTH(date) = %s
        """

        cursor.execute(
            query,
            (location, month)
        )

    # --------------------------------------------------------
    # Only location
    # --------------------------------------------------------

    elif location:

        query = """
            SELECT fish_name,
                   location,
                   temperature_c,
                   depth_m
            FROM fish_data
            WHERE location = %s
        """

        cursor.execute(
            query,
            (location,)
        )

    # --------------------------------------------------------
    # Only month
    # --------------------------------------------------------

    elif month:

        query = """
            SELECT fish_name,
                   location,
                   temperature_c,
                   depth_m
            FROM fish_data
            WHERE MONTH(date) = %s
        """

        cursor.execute(
            query,
            (month,)
        )

    # --------------------------------------------------------
    # No filters
    # --------------------------------------------------------

    else:

        cursor.execute("""
            SELECT fish_name,
                   location,
                   temperature_c,
                   depth_m
            FROM fish_data
        """)

    rows = cursor.fetchall()

    return jsonify(rows)


# ============================================================
# TREND
# ============================================================

@app.route("/trend")
def trend():

    cursor = get_cursor()

    cursor.execute("""
        SELECT YEAR(date) AS year,
               COUNT(*) AS count
        FROM fish_data
        GROUP BY YEAR(date)
        ORDER BY YEAR(date)
    """)

    rows = cursor.fetchall()

    data = []

    for row in rows:

        data.append({
            "year": row[0],
            "count": row[1]
        })

    return jsonify(data)


# ============================================================
# GET ALL FISH DATA
# ============================================================

@app.route("/fish-data")
def fish_data():

    cursor = get_cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM fish_data
        ORDER BY date DESC
    """)

    rows = cursor.fetchall()

    return jsonify(rows)


# ============================================================
# GET UNIQUE LOCATIONS
# ============================================================

@app.route("/locations")
def locations():

    cursor = get_cursor()

    cursor.execute("""
        SELECT DISTINCT location
        FROM fish_data
        WHERE location IS NOT NULL
          AND location != ''
        ORDER BY location
    """)

    rows = cursor.fetchall()

    locations_list = [
        row[0]
        for row in rows
    ]

    return jsonify(locations_list)


# ============================================================
# GET UNIQUE FISH SPECIES
# ============================================================

@app.route("/species")
def species():

    cursor = get_cursor()

    cursor.execute("""
        SELECT DISTINCT fish_name
        FROM fish_data
        WHERE fish_name IS NOT NULL
          AND fish_name != ''
        ORDER BY fish_name
    """)

    rows = cursor.fetchall()

    species_list = [
        row[0]
        for row in rows
    ]

    return jsonify(species_list)


# ============================================================
# DOWNLOAD FISH DATA AS CSV
# ============================================================

@app.route("/download/csv")
def download_csv():

    cursor = get_cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM fish_data
    """)

    rows = cursor.fetchall()

    df = pd.DataFrame(rows)

    file_path = os.path.join(
        CLEAN_FOLDER,
        "fish_data.csv"
    )

    df.to_csv(
        file_path,
        index=False
    )

    return send_file(
        file_path,
        as_attachment=True,
        download_name="fish_data.csv"
    )


# ============================================================
# DOWNLOAD FISH DATA AS EXCEL
# ============================================================

@app.route("/download/excel")
def download_excel():

    cursor = get_cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM fish_data
    """)

    rows = cursor.fetchall()

    df = pd.DataFrame(rows)

    file_path = os.path.join(
        CLEAN_FOLDER,
        "fish_data.xlsx"
    )

    df.to_excel(
        file_path,
        index=False
    )

    return send_file(
        file_path,
        as_attachment=True,
        download_name="fish_data.xlsx"
    )


# ============================================================
# ADMIN LOGIN
# ============================================================

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:

        return jsonify({
            "success": False,
            "message": "Username and password are required"
        }), 400

    cursor = get_cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM users
        WHERE username = %s
          AND password = %s
    """, (username, password))

    user = cursor.fetchone()

    if user:

        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": user
        })

    return jsonify({
        "success": False,
        "message": "Invalid username or password"
    }), 401


# ============================================================
# UPLOAD CSV
# ============================================================

@app.route("/upload", methods=["POST"])
def upload():

    if "file" not in request.files:

        return jsonify({
            "success": False,
            "message": "No file uploaded"
        }), 400

    file = request.files["file"]

    if file.filename == "":

        return jsonify({
            "success": False,
            "message": "No file selected"
        }), 400

    file_path = os.path.join(
        UPLOAD_FOLDER,
        file.filename
    )

    file.save(file_path)

    try:

        df = pd.read_csv(file_path)

        # Replace NaN values with None
        df = df.where(
            pd.notnull(df),
            None
        )

        cursor = get_cursor()

        columns = list(df.columns)

        column_names = ", ".join(
            f"`{column}`"
            for column in columns
        )

        placeholders = ", ".join(
            ["%s"] * len(columns)
        )

        query = f"""
            INSERT INTO fish_data
            ({column_names})
            VALUES ({placeholders})
        """

        for _, row in df.iterrows():

            values = tuple(
                row[column]
                for column in columns
            )

            cursor.execute(
                query,
                values
            )

        get_cursor().connection.commit()

        return jsonify({
            "success": True,
            "message": "File uploaded successfully",
            "records_added": len(df)
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
@app.route("/search/data")
def search_data():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    radius = request.args.get("radius", type=float, default=10)

    if lat is None or lon is None:
        return jsonify({
            "success": False,
            "message": "Latitude and longitude are required"
        }), 400

    cursor = get_cursor(dictionary=True)

    query = """
        SELECT *,
        (
            6371 * ACOS(
                COS(RADIANS(%s))
                * COS(RADIANS(latitude))
                * COS(RADIANS(longitude) - RADIANS(%s))
                + SIN(RADIANS(%s))
                * SIN(RADIANS(latitude))
            )
        ) AS distance_km
        FROM fish_data
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL
        HAVING distance_km <= %s
        ORDER BY distance_km ASC
    """

    cursor.execute(query, (lat, lon, lat, radius))

    rows = cursor.fetchall()

    return jsonify(rows)

# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )


